// RUN-02 — testes ponta a ponta coordenador <-> worker (processos separados no mesmo host).
// O runner inicia dois test_worker e passa as portas por ambiente:
//   MINIPAR_TEST_PORT_A, MINIPAR_TEST_PORT_B (workers vivos), MINIPAR_TEST_PORT_DEAD (sem ninguém escutando).
// Loopback prova o PROTOCOLO, não a execução entre computadores (isso é o RUN-03).
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <thread>
#include <vector>

#include "minipar_rt/minipar_rt.hpp"
#include "test_util.hpp"

using namespace minipar_rt;
using rt_test::now_ms;

namespace {

const char* kBuild = "minipar-rt-test";

std::uint16_t env_port(const char* name) {
    const char* v = std::getenv(name);
    if (!v) throw rt_test::Failure{std::string("variavel ausente: ") + name};
    return static_cast<std::uint16_t>(std::atoi(v));
}
Destination A() { return Destination::remote("127.0.0.1", env_port("MINIPAR_TEST_PORT_A")); }
Destination B() { return Destination::remote("127.0.0.1", env_port("MINIPAR_TEST_PORT_B")); }

long long pid_of(const std::string& executed_by) {
    auto pos = executed_by.rfind(':');
    return pos == std::string::npos ? -1 : std::atoll(executed_by.c_str() + pos + 1);
}

std::string frame_of(const Json& j) {
    std::string p = j.dump();
    std::uint32_t n = static_cast<std::uint32_t>(p.size());
    std::string w = {char((n >> 24) & 0xFF), char((n >> 16) & 0xFF), char((n >> 8) & 0xFF), char(n & 0xFF)};
    return w + p;
}

Json hello() { return detail::make_message("HELLO", {{"build_id", kBuild}, {"request_id", "raw-test"}}); }

net::Socket raw_connect(std::uint16_t port) {
    std::string err;
    net::Socket s = net::connect_tcp("127.0.0.1", port, 2000, err);
    if (!s.valid()) throw rt_test::Failure{"raw connect: " + err};
    net::set_recv_timeout(s.get(), 5000);
    return s;
}

Json read_json(net::Socket& s) {
    std::string f, err;
    if (net::read_frame(s.get(), f, err) != net::FrameStatus::Ok) throw rt_test::Failure{"read_frame: " + err};
    return Json::parse(f);
}

struct Init {
    Init() { set_build_id(kBuild); }
} g_init;

}  // namespace

TEST_CASE("remoto: calculo real executado em outro processo") {
    TaskResult r = join(start("soma_quadrados", {20000}, A()));
    CHECK_MSG(r.ok, r.error.message);
    CHECK(r.value.as_int() == 20000LL * 19999 * 39999 / 6);
    CHECK_MSG(pid_of(r.executed_by) > 0 && pid_of(r.executed_by) != detail::current_pid(),
              "executed_by=" + r.executed_by);
}

TEST_CASE("RT-01 remoto: start nao espera o calculo") {
    long long t0 = now_ms();
    TaskHandle h = start("dormir", {600, "x"}, A());
    long long dt = now_ms() - t0;
    CHECK_MSG(dt < 100, "start levou " + std::to_string(dt) + " ms");
    TaskResult r = join(h);
    CHECK(r.ok && r.value == Value("x"));
    CHECK(now_ms() - t0 >= 550);
}

TEST_CASE("RT-04 remoto: duas tarefas fora de ordem na mesma conexao") {
    long long t0 = now_ms();
    TaskHandle lenta = start("dormir", {800, "lenta"}, A());
    TaskHandle rapida = start("dormir", {0, "rapida"}, A());
    TaskResult rr = join(rapida);
    long long t_rapida = now_ms() - t0;
    TaskResult rl = join(lenta);
    CHECK(rr.ok && rr.value == Value("rapida"));
    CHECK(rl.ok && rl.value == Value("lenta"));
    CHECK_MSG(t_rapida < 500, "a rapida esperou a lenta: " + std::to_string(t_rapida) + " ms");
}

TEST_CASE("dois workers em paralelo (processos distintos)") {
    long long t0 = now_ms();
    std::vector<TaskHandle> hs;
    for (int i = 0; i < 2; ++i) {
        hs.push_back(start("dormir", {500, "a"}, A()));
        hs.push_back(start("dormir", {500, "b"}, B()));
    }
    std::set<std::string> who;
    for (auto& h : hs) {
        TaskResult r = join(h);
        CHECK(r.ok);
        who.insert(r.executed_by);
    }
    long long dt = now_ms() - t0;
    CHECK_MSG(dt < 900, "4 x 500 ms em 2 workers levou " + std::to_string(dt) + " ms");
    CHECK(who.size() == 2);
}

TEST_CASE("160 tarefas em 2 workers sem perda nem duplicacao") {
    std::vector<TaskHandle> hs;
    for (int i = 0; i < 160; ++i) hs.push_back(start("eco", {i}, i % 2 ? B() : A()));
    std::set<long long> seen;
    std::map<std::string, int> per_worker;
    for (int i = 0; i < 160; ++i) {
        TaskResult r = join(hs[static_cast<std::size_t>(i)]);
        CHECK_MSG(r.ok, r.error.message);
        CHECK(r.value.as_list().at(0).as_int() == i);
        seen.insert(i);
        per_worker[r.executed_by]++;
    }
    CHECK(seen.size() == 160);
    CHECK(per_worker.size() == 2);
    for (auto& kv : per_worker) CHECK(kv.second == 80);
}

TEST_CASE("erros remotos: TASK_FAILED e UNKNOWN_FUNCTION") {
    TaskResult f = join(start("falha", {}, A()));
    CHECK(!f.ok && f.error.code == ErrorCode::TASK_FAILED && f.error.message == "falha proposital");
    TaskResult u = join(start("nao_existe", {}, A()));
    CHECK(!u.ok && u.error.code == ErrorCode::UNKNOWN_FUNCTION);
    TaskResult ok = join(start("eco", {1}, A()));  // a conexão continua boa depois de erros de tarefa
    CHECK(ok.ok);
}

TEST_CASE("mensagens maiores que 1 MiB nos dois sentidos") {
    std::vector<long long> big(300000);
    for (std::size_t i = 0; i < big.size(); ++i) big[i] = static_cast<long long>(i);
    TaskResult t = join(start("tamanho", {to_value(big)}, A()));
    CHECK_MSG(t.ok, t.error.message);
    CHECK(t.value.as_int() == 300000);
    TaskResult g = join(start("gera_lista", {300000}, A()));
    CHECK_MSG(g.ok, g.error.message);
    CHECK(g.value.as_list().size() == 300000 && g.value.as_list().back().as_int() == 299999);
}

TEST_CASE("worker indisponivel vira WORKER_UNAVAILABLE sem travar") {
    long long t0 = now_ms();
    TaskResult r = join(start("eco", {1}, Destination::remote("127.0.0.1", env_port("MINIPAR_TEST_PORT_DEAD"))));
    long long dt = now_ms() - t0;
    CHECK(!r.ok && r.error.code == ErrorCode::WORKER_UNAVAILABLE);
    CHECK_MSG(dt < 5000, "levou " + std::to_string(dt) + " ms");
}

TEST_CASE("build_id diferente vira VERSION_MISMATCH") {
    set_build_id("outro-build");
    // "localhost:porta" é outra chave de conexão: força handshake novo com o build_id trocado.
    TaskResult r = join(start("eco", {1}, Destination::remote("localhost", env_port("MINIPAR_TEST_PORT_A"))));
    set_build_id(kBuild);
    CHECK(!r.ok && r.error.code == ErrorCode::VERSION_MISMATCH);
}

TEST_CASE("worker aceita HELLO e TASK fragmentados byte a byte") {
    net::Socket s = raw_connect(env_port("MINIPAR_TEST_PORT_A"));
    std::string w = frame_of(hello());
    for (char c : w) {
        net::send_all(s.get(), &c, 1);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    Json ok = read_json(s);
    CHECK(ok.at("type").str() == "HELLO_OK");
    std::string t = frame_of(detail::make_message("TASK", {{"request_id", "raw-test"}, {"task_id", "raw-1"},
                                                           {"function_id", "soma_quadrados"},
                                                           {"args", Json(Json::Array{Json(100)})}}));
    std::size_t third = t.size() / 3;
    net::send_all(s.get(), t.data(), third);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    net::send_all(s.get(), t.data() + third, third);
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    net::send_all(s.get(), t.data() + 2 * third, t.size() - 2 * third);
    Json res = read_json(s);
    CHECK(res.at("type").str() == "RESULT" && res.at("task_id").str() == "raw-1");
    CHECK(res.at("result").integer() == 328350);
}

TEST_CASE("frame invalido no worker: ERROR e fecha so a conexao") {
    for (int caso = 0; caso < 4; ++caso) {
        net::Socket s = raw_connect(env_port("MINIPAR_TEST_PORT_A"));
        if (caso == 0) {  // tamanho 0
            const char z[4] = {0, 0, 0, 0};
            net::send_all(s.get(), z, 4);
        } else if (caso == 1) {  // tamanho 0x7FFFFFFF
            const unsigned char h[4] = {0x7F, 0xFF, 0xFF, 0xFF};
            net::send_all(s.get(), reinterpret_cast<const char*>(h), 4);
        } else if (caso == 2) {  // JSON quebrado depois de HELLO válido
            std::string w = frame_of(hello());
            net::send_all(s.get(), w.data(), w.size());
            CHECK(read_json(s).at("type").str() == "HELLO_OK");
            std::string bad = "{\"type\":\"TASK\",";
            net::write_frame(s.get(), bad);
        } else {  // TASK antes do HELLO
            net::write_frame(s.get(), detail::make_message("TASK", {{"task_id", "x"}}).dump());
        }
        Json e = read_json(s);
        CHECK_MSG(e.at("type").str() == "ERROR", "caso " + std::to_string(caso));
        CHECK(e.at("error").at("code").str() == "PROTOCOL_ERROR");
        std::string f, err;
        CHECK(net::read_frame(s.get(), f, err) == net::FrameStatus::Closed);
    }
    TaskResult r = join(start("eco", {7}, A()));  // o worker segue atendendo
    CHECK(r.ok && r.value.as_list().at(0).as_int() == 7);
}

TEST_CASE("coordenador: RESULT fragmentado e frame invalido de servidor falso") {
    std::string err;
    net::Socket l = net::listen_tcp("127.0.0.1", 0, err);
    CHECK_MSG(l.valid(), err);
    std::uint16_t port = net::local_port(l.get());
    std::thread fake([&] {
        std::string peer, f, e;
        net::Socket s = net::accept_tcp(l.get(), peer);
        net::read_frame(s.get(), f, e);  // HELLO
        net::write_frame(s.get(), detail::make_message("HELLO_OK", {{"worker_id", "falso:1"}, {"host", "falso"},
                                                                    {"pid", 1}, {"build_id", kBuild}})
                                      .dump());
        net::read_frame(s.get(), f, e);  // TASK 1
        std::string id = Json::parse(f).at("task_id").str();
        std::string w = frame_of(detail::make_message(
            "RESULT", {{"request_id", "r"}, {"task_id", id}, {"status", "ok"}, {"result", 99}, {"worker_id", "falso:1"}}));
        for (char c : w) {
            net::send_all(s.get(), &c, 1);
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        net::read_frame(s.get(), f, e);  // TASK 2
        const char z[4] = {0, 0, 0, 0};
        net::send_all(s.get(), z, 4);  // frame inválido
        std::this_thread::sleep_for(std::chrono::milliseconds(300));
    });
    TaskResult r1 = join(start("qualquer", {}, Destination::remote("127.0.0.1", port)), 5000);
    CHECK_MSG(r1.ok && r1.value == Value(99) && r1.executed_by == "falso:1", to_string(r1.error.code));
    TaskResult r2 = join(start("qualquer", {}, Destination::remote("127.0.0.1", port)), 5000);
    CHECK_MSG(!r2.ok && r2.error.code == ErrorCode::PROTOCOL_ERROR, to_string(r2.error.code));
    fake.join();
}

TEST_CASE("worker que para de ler: start nao trava e as tarefas viram WORKER_LOST") {
    // Servidor falso responde ao HELLO e depois nunca mais lê: o buffer TCP enche com TASKs de ~7 MiB.
    // O runner define MINIPAR_RT_SEND_TIMEOUT_MS=1500 para este binário.
    std::string err;
    net::Socket l = net::listen_tcp("127.0.0.1", 0, err);
    CHECK_MSG(l.valid(), err);
    std::uint16_t port = net::local_port(l.get());
    std::mutex m;
    std::condition_variable cv;
    bool release = false;
    std::thread fake([&] {
        std::string peer, f, e;
        net::Socket s = net::accept_tcp(l.get(), peer);
        net::read_frame(s.get(), f, e);  // HELLO
        net::write_frame(s.get(), detail::make_message("HELLO_OK", {{"worker_id", "mudo:1"}, {"host", "mudo"},
                                                                    {"pid", 1}, {"build_id", kBuild}})
                                      .dump());
        std::unique_lock<std::mutex> lk(m);
        cv.wait_for(lk, std::chrono::seconds(30), [&] { return release; });
    });
    // Libera e junta o servidor falso também quando um CHECK falha (thread joinable no destrutor aborta).
    struct Release {
        std::mutex& m;
        std::condition_variable& cv;
        bool& release;
        std::thread& t;
        ~Release() {
            {
                std::lock_guard<std::mutex> lk(m);
                release = true;
            }
            cv.notify_all();
            if (t.joinable()) t.join();
        }
    } guard{m, cv, release, fake};
    std::string big(7 * 1024 * 1024, 'x');
    Destination d = Destination::remote("127.0.0.1", port);
    std::vector<TaskHandle> hs;
    long long t0 = now_ms();
    for (int i = 0; i < 4; ++i) {
        long long ts = now_ms();
        hs.push_back(start("qualquer", {big}, d));
        long long dt = now_ms() - ts;
        CHECK_MSG(dt < 1000, "start " + std::to_string(i) + " levou " + std::to_string(dt) + " ms");
    }
    for (auto& h : hs) {
        TaskResult r = join(h, 15000);
        CHECK_MSG(!r.ok && r.error.code == ErrorCode::WORKER_LOST, std::string(to_string(r.error.code)) + ": " + r.error.message);
    }
    long long dt = now_ms() - t0;
    CHECK_MSG(dt < 10000, "falha detectada em " + std::to_string(dt) + " ms");
}

TEST_CASE("resultado acima de 8 MiB vira TASK_FAILED, sem esperar o timeout") {
    long long t0 = now_ms();
    TaskResult r = join(start("gera_texto", {9 * 1024 * 1024}, A()), 15000);
    long long dt = now_ms() - t0;
    CHECK_MSG(!r.ok && r.error.code == ErrorCode::TASK_FAILED, std::string(to_string(r.error.code)) + ": " + r.error.message);
    CHECK_MSG(dt < 5000, "levou " + std::to_string(dt) + " ms");
    TaskResult ok = join(start("eco", {2}, A()));  // a conexão continua boa
    CHECK(ok.ok);
}

TEST_CASE("TASK com protocol_version diferente: ERROR VERSION_MISMATCH e fecha a conexao") {
    net::Socket s = raw_connect(env_port("MINIPAR_TEST_PORT_A"));
    std::string w = frame_of(hello());
    net::send_all(s.get(), w.data(), w.size());
    CHECK(read_json(s).at("type").str() == "HELLO_OK");
    Json::Object task{{"protocol_version", 2}, {"type", "TASK"}, {"request_id", "raw-test"}, {"task_id", "raw-v2"},
                      {"function_id", "eco"}, {"args", Json(Json::Array{Json(1)})}};
    net::write_frame(s.get(), Json(std::move(task)).dump());
    Json e = read_json(s);
    CHECK(e.at("type").str() == "ERROR" && e.at("error").at("code").str() == "VERSION_MISMATCH");
    std::string f, err;
    CHECK(net::read_frame(s.get(), f, err) == net::FrameStatus::Closed);
}

TEST_CASE("coordenador: RESULT com protocol_version diferente vira VERSION_MISMATCH") {
    std::string err;
    net::Socket l = net::listen_tcp("127.0.0.1", 0, err);
    CHECK_MSG(l.valid(), err);
    std::uint16_t port = net::local_port(l.get());
    std::thread fake([&] {
        std::string peer, f, e;
        net::Socket s = net::accept_tcp(l.get(), peer);
        net::read_frame(s.get(), f, e);  // HELLO
        net::write_frame(s.get(), detail::make_message("HELLO_OK", {{"worker_id", "falso:2"}, {"host", "falso"},
                                                                    {"pid", 2}, {"build_id", kBuild}})
                                      .dump());
        net::read_frame(s.get(), f, e);  // TASK
        std::string id = Json::parse(f).at("task_id").str();
        Json::Object res{{"protocol_version", 2}, {"type", "RESULT"}, {"request_id", "r"}, {"task_id", id},
                         {"status", "ok"}, {"result", 1}, {"worker_id", "falso:2"}};
        net::write_frame(s.get(), Json(std::move(res)).dump());
        std::this_thread::sleep_for(std::chrono::milliseconds(300));
    });
    TaskResult r = join(start("qualquer", {}, Destination::remote("127.0.0.1", port)), 5000);
    fake.join();
    CHECK_MSG(!r.ok && r.error.code == ErrorCode::VERSION_MISMATCH, to_string(r.error.code));
}

TEST_CASE("RT-05 remoto: TIMEOUT mantem o handle valido") {
    TaskHandle h = start("dormir", {800, "tarde"}, A());
    TaskResult t = join(h, 100);
    CHECK(!t.ok && t.error.code == ErrorCode::TIMEOUT);
    TaskResult r = join(h);
    CHECK(r.ok && r.value == Value("tarde"));
}

// Deve ser o último caso que usa o worker B: ele encerra o processo B.
TEST_CASE("RT-09 worker morre no meio da tarefa: WORKER_LOST sem travar") {
    TaskHandle longa = start("dormir", {10000, "nunca"}, B());
    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    long long t0 = now_ms();
    TaskHandle mata = start("morrer", {}, B());
    TaskResult r1 = join(longa);
    TaskResult r2 = join(mata);
    long long dt = now_ms() - t0;
    CHECK_MSG(!r1.ok && r1.error.code == ErrorCode::WORKER_LOST, to_string(r1.error.code));
    CHECK_MSG(!r2.ok && r2.error.code == ErrorCode::WORKER_LOST, to_string(r2.error.code));
    CHECK_MSG(dt < 3000, "detectou a queda em " + std::to_string(dt) + " ms");
}

TEST_CASE("depois da queda: nova tarefa para o worker morto vira WORKER_UNAVAILABLE") {
    TaskResult r = join(start("eco", {1}, B()));
    CHECK_MSG(!r.ok && r.error.code == ErrorCode::WORKER_UNAVAILABLE, to_string(r.error.code));
}

int main(int argc, char** argv) { return rt_test::run_all(argc, argv); }
