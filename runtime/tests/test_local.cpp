// RUN-01 — testes C++ isolados do runtime local (start/join, registry, isolamento, erros).
// Critério de aceite: `start` retorna sem aguardar a tarefa; `join` aguarda e coleta resultado/erro.
#include <algorithm>
#include <atomic>
#include <mutex>
#include <set>
#include <stdexcept>
#include <thread>
#include <vector>

#include "minipar_rt/minipar_rt.hpp"
#include "test_util.hpp"

using namespace minipar_rt;
using rt_test::now_ms;

namespace {

std::atomic<int> g_running{0};
std::atomic<int> g_max_running{0};
std::mutex g_order_m;
std::vector<std::string> g_finish_order;

void sleep_ms(long long ms) { std::this_thread::sleep_for(std::chrono::milliseconds(ms)); }

// Soma real de i*i para i em [0, n): não é valor pronto, é cálculo.
long long soma_quadrados(long long n) {
    long long s = 0;
    for (long long i = 0; i < n; ++i) s += i * i;
    return s;
}

void register_test_functions() {
    // dobra(x, atraso_ms): espera e devolve 2x
    register_function("dobra", [](const TaskArgs& a) {
        sleep_ms(a.at(1).as_int());
        return Value(a.at(0).as_int() * 2);
    });
    register_function("soma_quadrados", [](const TaskArgs& a) { return Value(soma_quadrados(a.at(0).as_int())); });
    // marca(nome, atraso_ms): registra a ordem de término e devolve o nome
    register_function("marca", [](const TaskArgs& a) {
        sleep_ms(a.at(1).as_int());
        std::lock_guard<std::mutex> lk(g_order_m);
        g_finish_order.push_back(a.at(0).as_string());
        return a.at(0);
    });
    // ocupado(atraso_ms): mede quantas tarefas estão rodando ao mesmo tempo
    register_function("ocupado", [](const TaskArgs& a) {
        int now = ++g_running;
        int prev = g_max_running.load();
        while (now > prev && !g_max_running.compare_exchange_weak(prev, now)) {}
        sleep_ms(a.at(0).as_int());
        --g_running;
        return Value(true);
    });
    // soma_lista(lista, atraso_ms): soma depois de esperar (para testar isolamento)
    register_function("soma_lista", [](const TaskArgs& a) {
        sleep_ms(a.at(1).as_int());
        double s = 0;
        for (const auto& v : a.at(0).as_list()) s += v.as_number();
        return Value(s);
    });
    register_function("falha", [](const TaskArgs&) -> Value { throw std::runtime_error("divisao por zero"); });
    register_function("eco", [](const TaskArgs& a) { return Value(Value::List(a.begin(), a.end())); });
}

struct Init {
    Init() { register_test_functions(); }
} g_init;

}  // namespace

TEST_CASE("RT-01 start nao espera a tarefa terminar") {
    long long t0 = now_ms();
    TaskHandle h = start("dobra", {21, 600});
    long long dt_start = now_ms() - t0;
    CHECK_MSG(dt_start < 100, "start levou " + std::to_string(dt_start) + " ms");
    TaskResult r = join(h);
    long long dt_join = now_ms() - t0;
    CHECK(r.ok);
    CHECK(r.value == Value(42));
    CHECK_MSG(dt_join >= 550, "join retornou cedo demais: " + std::to_string(dt_join) + " ms");
}

TEST_CASE("RT-01 join devolve calculo real") {
    TaskHandle h1 = start("soma_quadrados", {1000});
    TaskHandle h2 = start("soma_quadrados", {12345});
    TaskResult r2 = join(h2);
    TaskResult r1 = join(h1);
    CHECK(r1.ok && r2.ok);
    // fórmula fechada: n(n-1)(2n-1)/6
    CHECK(r1.value.as_int() == 1000LL * 999 * 1999 / 6);
    CHECK(r2.value.as_int() == 12345LL * 12344 * 24689 / 6);
    CHECK(r1.task_id == h1.task_id && r2.task_id == h2.task_id);
    CHECK(r1.executed_by == "local:" + std::to_string(detail::current_pid()));
}

TEST_CASE("RT-04 tarefas terminam fora de ordem sem trocar resultados") {
    {
        std::lock_guard<std::mutex> lk(g_order_m);
        g_finish_order.clear();
    }
    TaskHandle lenta = start("marca", {"lenta", 500});
    TaskHandle rapida = start("marca", {"rapida", 0});
    TaskResult rl = join(lenta);
    TaskResult rr = join(rapida);
    CHECK(rl.ok && rr.ok);
    CHECK(rl.value == Value("lenta"));
    CHECK(rr.value == Value("rapida"));
    std::lock_guard<std::mutex> lk(g_order_m);
    CHECK_MSG(g_finish_order.size() == 2 && g_finish_order[0] == "rapida",
              "a rapida deveria terminar antes da lenta");
}

TEST_CASE("execucao concorrente real (16 tarefas de 200 ms)") {
    g_max_running = 0;
    long long t0 = now_ms();
    std::vector<TaskHandle> hs;
    for (int i = 0; i < 16; ++i) hs.push_back(start("ocupado", {200}));
    for (auto& h : hs) CHECK(join(h).ok);
    long long dt = now_ms() - t0;
    CHECK_MSG(g_max_running.load() > 1, "nenhuma sobreposicao observada");
    CHECK_MSG(dt < 16 * 200, "16 x 200 ms levou " + std::to_string(dt) + " ms: execucao serial");
}

TEST_CASE("160 tarefas sem perda nem duplicacao") {
    std::vector<TaskHandle> hs;
    for (int i = 0; i < 160; ++i) hs.push_back(start("eco", {i}));
    std::set<long long> seen;
    std::set<std::string> ids;
    for (int i = 0; i < 160; ++i) {
        TaskResult r = join(hs[static_cast<std::size_t>(i)]);
        CHECK(r.ok);
        CHECK(r.value.as_list().at(0).as_int() == i);
        seen.insert(r.value.as_list().at(0).as_int());
        ids.insert(r.task_id);
    }
    CHECK(seen.size() == 160);
    CHECK(ids.size() == 160);
}

TEST_CASE("RT-03 argumentos copiados: alterar o original depois do start nao afeta a tarefa") {
    std::vector<double> notas = {7.5, 8.0, 9.5};
    TaskHandle h = start("soma_lista", {to_value(notas), 300});
    notas[0] = 1000.0;  // a tarefa ainda está dormindo
    notas.push_back(5000.0);
    TaskResult r = join(h);
    CHECK(r.ok);
    CHECK(r.value.as_number() == 25.0);
}

TEST_CASE("RT-08 excecao na tarefa vira TASK_FAILED sem derrubar o processo") {
    TaskResult r = join(start("falha", {}));
    CHECK(!r.ok);
    CHECK(r.error.code == ErrorCode::TASK_FAILED);
    CHECK(r.error.message == "divisao por zero");
}

TEST_CASE("funcao nao registrada vira UNKNOWN_FUNCTION") {
    TaskResult r = join(start("nao_existe", {1}));
    CHECK(!r.ok);
    CHECK(r.error.code == ErrorCode::UNKNOWN_FUNCTION);
}

TEST_CASE("RT-05 TIMEOUT mantem o handle valido") {
    TaskHandle h = start("dobra", {5, 400});
    TaskResult t = join(h, 50);
    CHECK(!t.ok);
    CHECK(t.error.code == ErrorCode::TIMEOUT);
    TaskResult r = join(h);
    CHECK(r.ok);
    CHECK(r.value == Value(10));
}

TEST_CASE("RT-07 segundo join e handle desconhecido viram INVALID_HANDLE") {
    TaskHandle h = start("dobra", {1, 0});
    CHECK(join(h).ok);
    TaskResult again = join(h);
    CHECK(again.error.code == ErrorCode::INVALID_HANDLE);
    TaskHandle fake{999999, "task-999999"};
    CHECK(join(fake).error.code == ErrorCode::INVALID_HANDLE);
}

TEST_CASE("RT-07 dois joins concorrentes: exatamente um coleta") {
    TaskHandle h = start("dobra", {3, 200});
    TaskResult a, b;
    std::thread t1([&] { a = join(h); });
    std::thread t2([&] { b = join(h); });
    t1.join();
    t2.join();
    CHECK((a.ok ? 1 : 0) + (b.ok ? 1 : 0) == 1);
    const TaskResult& lost = a.ok ? b : a;
    CHECK(lost.error.code == ErrorCode::INVALID_HANDLE);
}

TEST_CASE("RT-02 destino invalido vira BAD_DESTINATION no join") {
    for (const char* txt : {"", "host", ":80", "host:", "host:abc", "host:0", "host:70000", "a:b:c"}) {
        Destination d = Destination::parse(txt);
        CHECK_MSG(d.kind == Destination::Kind::Invalid, std::string("aceitou '") + txt + "'");
        TaskResult r = join(start("dobra", {1, 0}, d));
        CHECK(r.error.code == ErrorCode::BAD_DESTINATION);
    }
    CHECK(Destination::parse(" LOCAL ").kind == Destination::Kind::Local);
    Destination ok = Destination::parse("192.168.0.12:7000");
    CHECK(ok.kind == Destination::Kind::Remote && ok.host == "192.168.0.12" && ok.port == 7000);
}

TEST_CASE("RT-10 start/join de varias threads ao mesmo tempo") {
    std::atomic<int> errors{0};
    std::vector<std::thread> ts;
    for (int t = 0; t < 8; ++t) {
        ts.emplace_back([t, &errors] {
            for (int i = 0; i < 50; ++i) {
                int x = t * 1000 + i;
                TaskResult r = join(start("dobra", {x, 0}));
                if (!r.ok || r.value.as_int() != 2 * x) ++errors;
            }
        });
    }
    for (auto& th : ts) th.join();
    CHECK(errors.load() == 0);
}

// Regressão: com std::thread::detach no winpthreads algumas tarefas nunca rodavam e o join travava.
TEST_CASE("estresse: 2000 tarefas curtas todas executam (join com limite)") {
    std::vector<TaskHandle> hs;
    for (int i = 0; i < 2000; ++i) hs.push_back(start("dobra", {i, 0}));
    for (int i = 0; i < 2000; ++i) {
        TaskResult r = join(hs[static_cast<std::size_t>(i)], 10000);
        CHECK_MSG(r.ok, hs[static_cast<std::size_t>(i)].task_id + ": " + to_string(r.error.code));
        CHECK(r.value.as_int() == 2 * i);
    }
}

TEST_CASE("Value: conversoes to_value/value_cast") {
    Value l = to_value(std::vector<int>{1, 2, 3});
    CHECK(l.is_list() && l.as_list().size() == 3);
    CHECK(value_cast<std::vector<long>>(l) == (std::vector<long>{1, 2, 3}));
    CHECK(value_cast<std::vector<double>>(l)[2] == 3.0);
    CHECK(Value(2).is_int() && Value(2.0).is_float());
    CHECK(!(Value(2) == Value(2.0)));  // int e float são formas distintas
    CHECK(value_cast<std::string>(Value("abc")) == "abc");
    CHECK(to_value(std::vector<std::string>{"a", "b"}).to_display() == "[a, b]");
    bool threw = false;
    try {
        (void)value_cast<std::string>(Value(3));
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    CHECK(threw);
}

int main(int argc, char** argv) { return rt_test::run_all(argc, argv); }
