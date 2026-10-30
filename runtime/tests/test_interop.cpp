// RUN-04 — contrato da API do runtime consumida pelo backend CORE-07 (src/codegen.py, src/cpp_template.py).
//
// Usa EXATAMENTE os 13 símbolos que o C++ gerado chama, do mesmo jeito que o gerador os emite:
//   Value, value_cast, to_value, TaskHandle, TaskArgs, Destination (::parse), start, join,
//   join_or_exit, to_string(ErrorCode), register_function, set_build_id, worker_main_if_requested.
// Se alguém mudar a API da qual o backend depende, este teste quebra antes do C++ gerado.
//
// O trecho "copiado do gerador" abaixo reproduz o _FJ_HEADER de src/cpp_template.py e o formato dos
// wrappers/main de CppCodeGenerator._fj_program (CORE-07, PR #18). Não é usado pelo backend: é a
// referência do consumidor dentro do teste do runtime.
//
// Modos (o mesmo binário, como no programa gerado):
//   test_interop [filtro]                         casos de teste; os remotos exigem MINIPAR_INTEROP_PORT
//                                                 (worker com o mesmo build_id) e MINIPAR_INTEROP_PORT_OUTRO
//                                                 (worker com build_id diferente). O run_tests.py sobe os dois.
//   test_interop --minipar-worker <porta> [--bind <ip>] [--build-id-outro]
//   test_interop --sondagem-join-coordenador      join de tarefa que falha fora de tarefa -> exit 1
#include "minipar_rt/minipar_rt.hpp"

#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include "test_util.hpp"

// ---- copiado do gerador (src/cpp_template.py: _CPP_HEADER/_FJ_HEADER) ---------------------------

inline thread_local bool __fj_in_task = false;

struct __fj_scope {
    bool previous;
    explicit __fj_scope(bool active) : previous(__fj_in_task) { __fj_in_task = active; }
    ~__fj_scope() { __fj_in_task = previous; }
};

// No coordenador usa a API contratada; dentro de tarefa, preserva o worker.
inline minipar_rt::Value __fj_join(const minipar_rt::TaskHandle& h, int timeout) {
    if (!__fj_in_task) return minipar_rt::join_or_exit(h, timeout);
    auto r = minipar_rt::join(h, timeout);
    if (!r.ok) throw std::runtime_error(std::string(minipar_rt::to_string(r.error.code)) + ": " + r.error.message);
    return std::move(r.value);
}

// ---- funções "MiniPar" já especializadas, como o backend as emite --------------------------------

static const char* const kBuildId = "run04-interop-contrato-0001";

int soma_quadrados(double n) {  // n vem de parse_ints (vector<double>); acumulador inteiro
    int s = 0;
    for (int i = 0; i < n; i = i + 1) s = s + i * i;
    return s;
}
std::vector<double> escala(std::vector<double> xs, int k) {
    for (std::size_t i = 0; i < xs.size(); ++i) xs[i] = xs[i] * k;
    return xs;
}
std::string eco(std::string t) {
    if (t.size() < 1) throw std::out_of_range("substr indices invalidos");  // como __minipar_substr em tarefa
    return t + "|" + t.substr(0, 1);
}
bool eh_par(std::ptrdiff_t n) { return n % 2 == 0; }
std::vector<bool> inverte(std::vector<bool> bs) {
    for (std::size_t i = 0; i < bs.size(); ++i) bs[i] = !bs[i];
    return bs;
}
int traco(std::vector<std::vector<int>> m) {
    int s = 0;
    for (std::size_t i = 0; i < m.size(); ++i) s = s + m[i][i];
    return s;
}
std::vector<std::vector<int>> marca(std::vector<std::vector<int>> m, int v) {
    m[0][1] = v;
    return m;
}
std::vector<std::vector<std::string>> grade_texto(std::vector<std::vector<std::string>> g) {
    g[0][0] = g[0][0] + "!";
    return g;
}
double media(std::vector<double> xs) {
    double s = 0;
    for (double x : xs) s = s + x;
    return s / static_cast<double>(xs.size());
}
void sem_retorno(int x) { (void)(x + 1); }
int falha(std::string s) {  // como substr(s, 99, 1) dentro de tarefa
    throw std::out_of_range("substr indices invalidos (len=" + std::to_string(s.size()) + ")");
}
int aninhada(std::string s) {  // join dentro de tarefa: a falha da filha vira exceção da mãe
    auto h = ([&]() { auto a0 = minipar_rt::to_value(s); auto d = std::string("local");
                      return minipar_rt::start("falha", {a0}, minipar_rt::Destination::parse(d)); }());
    return ([&]() { auto c = h; auto t = -1; return minipar_rt::value_cast<int>(__fj_join(c, t)); }());
}

// Wrappers no formato de CppCodeGenerator._fj_program: aridade, escopo de tarefa, value_cast, to_value.
minipar_rt::Value __fj_wrap_soma_quadrados(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de soma_quadrados");
    __fj_scope scope(true);
    return minipar_rt::to_value(soma_quadrados(minipar_rt::value_cast<double>(a.at(0))));
}
minipar_rt::Value __fj_wrap_escala(const minipar_rt::TaskArgs& a) {
    if (a.size() != 2) throw std::invalid_argument("aridade de escala");
    __fj_scope scope(true);
    return minipar_rt::to_value(escala(minipar_rt::value_cast<std::vector<double>>(a.at(0)), minipar_rt::value_cast<int>(a.at(1))));
}
minipar_rt::Value __fj_wrap_eco(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de eco");
    __fj_scope scope(true);
    return minipar_rt::to_value(eco(minipar_rt::value_cast<std::string>(a.at(0))));
}
minipar_rt::Value __fj_wrap_eh_par(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de eh_par");
    __fj_scope scope(true);
    return minipar_rt::to_value(eh_par(minipar_rt::value_cast<std::ptrdiff_t>(a.at(0))));
}
minipar_rt::Value __fj_wrap_inverte(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de inverte");
    __fj_scope scope(true);
    return minipar_rt::to_value(inverte(minipar_rt::value_cast<std::vector<bool>>(a.at(0))));
}
minipar_rt::Value __fj_wrap_traco(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de traco");
    __fj_scope scope(true);
    return minipar_rt::to_value(traco(minipar_rt::value_cast<std::vector<std::vector<int>>>(a.at(0))));
}
minipar_rt::Value __fj_wrap_marca(const minipar_rt::TaskArgs& a) {
    if (a.size() != 2) throw std::invalid_argument("aridade de marca");
    __fj_scope scope(true);
    return minipar_rt::to_value(marca(minipar_rt::value_cast<std::vector<std::vector<int>>>(a.at(0)), minipar_rt::value_cast<int>(a.at(1))));
}
minipar_rt::Value __fj_wrap_grade_texto(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de grade_texto");
    __fj_scope scope(true);
    return minipar_rt::to_value(grade_texto(minipar_rt::value_cast<std::vector<std::vector<std::string>>>(a.at(0))));
}
minipar_rt::Value __fj_wrap_media(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de media");
    __fj_scope scope(true);
    return minipar_rt::to_value(media(minipar_rt::value_cast<std::vector<double>>(a.at(0))));
}
minipar_rt::Value __fj_wrap_sem_retorno(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de sem_retorno");
    __fj_scope scope(true);
    sem_retorno(minipar_rt::value_cast<int>(a.at(0))); return minipar_rt::Value();
}
minipar_rt::Value __fj_wrap_falha(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de falha");
    __fj_scope scope(true);
    return minipar_rt::to_value(falha(minipar_rt::value_cast<std::string>(a.at(0))));
}
minipar_rt::Value __fj_wrap_aninhada(const minipar_rt::TaskArgs& a) {
    if (a.size() != 1) throw std::invalid_argument("aridade de aninhada");
    __fj_scope scope(true);
    return minipar_rt::to_value(aninhada(minipar_rt::value_cast<std::string>(a.at(0))));
}

static void registrar_tudo() {
    minipar_rt::register_function("soma_quadrados", __fj_wrap_soma_quadrados);
    minipar_rt::register_function("escala", __fj_wrap_escala);
    minipar_rt::register_function("eco", __fj_wrap_eco);
    minipar_rt::register_function("eh_par", __fj_wrap_eh_par);
    minipar_rt::register_function("inverte", __fj_wrap_inverte);
    minipar_rt::register_function("traco", __fj_wrap_traco);
    minipar_rt::register_function("marca", __fj_wrap_marca);
    minipar_rt::register_function("grade_texto", __fj_wrap_grade_texto);
    minipar_rt::register_function("media", __fj_wrap_media);
    minipar_rt::register_function("sem_retorno", __fj_wrap_sem_retorno);
    minipar_rt::register_function("falha", __fj_wrap_falha);
    minipar_rt::register_function("aninhada", __fj_wrap_aninhada);
}

// fork f(args...) on d -> start("f", {to_value(a)...}, Destination::parse(d)), com snapshots em ordem.
template <typename... A>
static minipar_rt::TaskHandle fork_em(const std::string& fn, const std::string& destino, const A&... args) {
    minipar_rt::TaskArgs a{minipar_rt::to_value(args)...};
    auto d = destino;
    return minipar_rt::start(fn, a, minipar_rt::Destination::parse(d));
}

// join(h) dentro de tarefa (__fj_in_task = true): erro vira exceção com "<CODIGO>: <mensagem>".
template <typename T>
static T join_em_tarefa(const minipar_rt::TaskHandle& h, int timeout = -1) {
    __fj_scope scope(true);
    auto c = h;
    return minipar_rt::value_cast<T>(__fj_join(c, timeout));
}

static std::string erro_de_join(const minipar_rt::TaskHandle& h) {
    try {
        (void)join_em_tarefa<minipar_rt::Value>(h, 20000);
    } catch (const std::runtime_error& ex) {
        return ex.what();
    }
    return "(sem erro)";
}

static std::string destino_remoto(const char* env) {
    const char* p = std::getenv(env);
    if (!p || !*p) throw rt_test::Failure{std::string(env) + " ausente: rode pelo runtime/tests/run_tests.py"};
    return std::string("127.0.0.1:") + p;
}

// ---- conversões (sem tarefa) ------------------------------------------------------------------

TEST_CASE("to_value/value_cast: numeros int, ptrdiff_t e double como o backend emite") {
    using minipar_rt::Value;
    using minipar_rt::to_value;
    using minipar_rt::value_cast;
    Value i = to_value(2000000000);
    CHECK(i.kind() == Value::Kind::Int);
    CHECK(value_cast<int>(i) == 2000000000);
    Value p = to_value(static_cast<std::ptrdiff_t>(-7));  // len(...) no backend
    CHECK(p.is_int() && value_cast<std::ptrdiff_t>(p) == -7);
    Value d = to_value(7.5);
    CHECK(d.kind() == Value::Kind::Float && value_cast<double>(d) == 7.5);
    CHECK(value_cast<double>(i) == 2000000000.0);  // int -> double numérico (C-FJ-v1 §2.4)
    CHECK(value_cast<int>(to_value(-3.9)) == -3);   // double -> int trunca
    CHECK(value_cast<minipar_rt::Value>(d) == d);
}

TEST_CASE("to_value/value_cast: string e bool; forma errada lanca invalid_argument") {
    using minipar_rt::to_value;
    using minipar_rt::value_cast;
    std::string s = "a\xC3\xA7\xC3\xA3o \"x\"\n";  // UTF-8, aspas, quebra
    CHECK(value_cast<std::string>(to_value(s)) == s);
    CHECK(value_cast<std::string>(to_value(std::string())).empty());
    CHECK(value_cast<bool>(to_value(true)) == true);
    CHECK(value_cast<bool>(to_value(false)) == false);
    bool lancou = false;
    try { (void)value_cast<bool>(to_value(1)); } catch (const std::invalid_argument&) { lancou = true; }
    CHECK(lancou);
    lancou = false;
    try { (void)value_cast<int>(to_value(std::string("12"))); } catch (const std::invalid_argument&) { lancou = true; }
    CHECK(lancou);
}

TEST_CASE("to_value/value_cast: listas (double, int, bool) e matrizes (int, string)") {
    using minipar_rt::to_value;
    using minipar_rt::value_cast;
    std::vector<double> xs{1.5, -2.0, 3e10, 0.0};
    CHECK(value_cast<std::vector<double>>(to_value(xs)) == xs);
    std::vector<int> is{1, -2, 3};
    CHECK(value_cast<std::vector<int>>(to_value(is)) == is);
    CHECK(value_cast<std::vector<double>>(to_value(is)) == (std::vector<double>{1.0, -2.0, 3.0}));
    std::vector<bool> bs{true, false, true};
    CHECK(value_cast<std::vector<bool>>(to_value(bs)) == bs);
    std::vector<std::vector<int>> m(3, std::vector<int>(2, 7));
    m[2][1] = -1;
    auto vm = to_value(m);
    CHECK(vm.is_list() && vm.as_list().size() == 3 && vm.as_list()[0].is_list());
    CHECK(value_cast<std::vector<std::vector<int>>>(vm) == m);
    std::vector<std::vector<std::string>> g{{"a", "b"}, {"", "d"}};
    CHECK(value_cast<std::vector<std::vector<std::string>>>(to_value(g)) == g);
    CHECK(value_cast<std::vector<int>>(to_value(std::vector<int>{})).empty());
    bool lancou = false;
    try { (void)value_cast<std::vector<int>>(to_value(5)); } catch (const std::invalid_argument&) { lancou = true; }
    CHECK(lancou);
}

TEST_CASE("to_string(ErrorCode): nomes do contrato usados na mensagem do __fj_join") {
    using minipar_rt::ErrorCode;
    using minipar_rt::to_string;
    CHECK(std::strcmp(to_string(ErrorCode::NONE), "NONE") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::TASK_FAILED), "TASK_FAILED") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::UNKNOWN_FUNCTION), "UNKNOWN_FUNCTION") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::TIMEOUT), "TIMEOUT") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::WORKER_UNAVAILABLE), "WORKER_UNAVAILABLE") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::WORKER_LOST), "WORKER_LOST") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::INVALID_HANDLE), "INVALID_HANDLE") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::PROTOCOL_ERROR), "PROTOCOL_ERROR") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::VERSION_MISMATCH), "VERSION_MISMATCH") == 0);
    CHECK(std::strcmp(to_string(ErrorCode::BAD_DESTINATION), "BAD_DESTINATION") == 0);
}

TEST_CASE("Destination::parse: textos que chegam do input() do programa") {
    using minipar_rt::Destination;
    CHECK(Destination::parse("local").kind == Destination::Kind::Local);
    CHECK(Destination::parse("LOCAL\r\n").kind == Destination::Kind::Local);
    auto r = Destination::parse(" 127.0.0.1:7100 ");
    CHECK(r.kind == Destination::Kind::Remote && r.host == "127.0.0.1" && r.port == 7100);
    CHECK(Destination::parse("").kind == Destination::Kind::Invalid);
    CHECK(Destination::parse("host:abc").kind == Destination::Kind::Invalid);
    CHECK(Destination::parse("host:0").kind == Destination::Kind::Invalid);
    CHECK(Destination::parse("::1:7000").kind == Destination::Kind::Invalid);
}

TEST_CASE("worker_main_if_requested: sem flag devolve -1; porta ruim devolve 2") {
    char prog[] = "programa", flag[] = "--minipar-worker", ruim[] = "abc", filtro[] = "qualquer";
    char* sem_flag[] = {prog, filtro, nullptr};
    CHECK(minipar_rt::worker_main_if_requested(2, sem_flag) == -1);
    char* sem_porta[] = {prog, flag, nullptr};
    CHECK(minipar_rt::worker_main_if_requested(2, sem_porta) == 2);
    char* porta_ruim[] = {prog, flag, ruim, nullptr};
    CHECK(minipar_rt::worker_main_if_requested(3, porta_ruim) == 2);
}

// ---- tarefas locais com os wrappers do gerador -------------------------------------------------

TEST_CASE("local: wrappers registrados devolvem numero, string, bool, lista e matriz") {
    std::vector<double> nums{12, -4, 5.5};
    std::vector<std::vector<int>> m(4, std::vector<int>(4, 2));
    auto h1 = fork_em("soma_quadrados", "local", nums[0]);
    auto h2 = fork_em("escala", "local", nums, 3);
    auto h3 = fork_em("eco", "local", std::string("abcde"));
    auto h4 = fork_em("eh_par", "local", static_cast<std::ptrdiff_t>(5));
    auto h5 = fork_em("traco", "local", m);
    auto h6 = fork_em("marca", "local", m, 7);
    auto h7 = fork_em("inverte", "local", std::vector<bool>{true, false});
    auto h8 = fork_em("grade_texto", "local", std::vector<std::vector<std::string>>{{"x", "y"}});
    nums[0] = 0;  // RT-03: argumentos já copiados no start
    m[0][1] = 99;
    CHECK(join_em_tarefa<int>(h1) == 506);  // 0^2 + ... + 11^2
    CHECK(join_em_tarefa<std::vector<double>>(h2) == (std::vector<double>{36, -12, 16.5}));
    CHECK(join_em_tarefa<std::string>(h3) == "abcde|a");
    CHECK(join_em_tarefa<bool>(h4) == false);
    CHECK(join_em_tarefa<int>(h5) == 8);
    auto marcada = join_em_tarefa<std::vector<std::vector<int>>>(h6);
    CHECK(marcada[0][1] == 7 && marcada[1][1] == 2 && marcada.size() == 4);
    CHECK(join_em_tarefa<std::vector<bool>>(h7) == (std::vector<bool>{false, true}));
    CHECK(join_em_tarefa<std::vector<std::vector<std::string>>>(h8) == (std::vector<std::vector<std::string>>{{"x!", "y"}}));
}

TEST_CASE("local: join devolve TaskResult com ok, task_id e executed_by; void vira none") {
    auto h = fork_em("media", "local", std::vector<double>{1, 2, 4});
    CHECK(h.task_id == "task-" + std::to_string(h.id));
    minipar_rt::TaskResult r = minipar_rt::join(h);
    CHECK(r.ok && r.task_id == h.task_id);
    CHECK(r.executed_by.rfind("local:", 0) == 0);
    CHECK(std::fabs(minipar_rt::value_cast<double>(r.value) - 7.0 / 3.0) < 1e-12);
    auto hv = fork_em("sem_retorno", "local", 1);
    minipar_rt::TaskResult rv = minipar_rt::join(hv);
    CHECK(rv.ok && rv.value.is_none());
}

TEST_CASE("TaskHandle: copia aponta para a mesma tarefa; segundo join -> INVALID_HANDLE") {
    auto h = fork_em("soma_quadrados", "local", 4.0);
    minipar_rt::TaskHandle copia = h;  // `var copy = h` no MiniPar
    std::vector<minipar_rt::TaskHandle> lista{h};  // listas de task -> vector<TaskHandle>
    CHECK(copia.id == h.id && copia.task_id == h.task_id && lista[0].id == h.id);
    CHECK(join_em_tarefa<int>(copia) == 14);
    std::string e = erro_de_join(h);
    CHECK_MSG(e.rfind("INVALID_HANDLE: ", 0) == 0, e);
}

TEST_CASE("TASK_FAILED: excecao na funcao, aridade e value_cast errado; __fj_join lanca CODIGO: msg") {
    auto hf = fork_em("falha", "local", std::string("a"));
    minipar_rt::TaskResult r = minipar_rt::join(hf);
    CHECK(!r.ok && r.error.code == minipar_rt::ErrorCode::TASK_FAILED);
    CHECK_MSG(r.error.message.find("substr indices invalidos") != std::string::npos, r.error.message);
    std::string e = erro_de_join(fork_em("falha", "local", std::string("abc")));
    CHECK_MSG(e.rfind("TASK_FAILED: substr indices invalidos", 0) == 0, e);
    e = erro_de_join(fork_em("escala", "local", std::vector<double>{1}));  // falta um argumento
    CHECK_MSG(e == "TASK_FAILED: aridade de escala", e);
    e = erro_de_join(fork_em("soma_quadrados", "local", std::string("10")));  // tipo errado
    CHECK_MSG(e.rfind("TASK_FAILED: minipar_rt::Value: esperado number", 0) == 0, e);
    e = erro_de_join(fork_em("nao_registrada", "local", 1));
    CHECK_MSG(e.rfind("UNKNOWN_FUNCTION: ", 0) == 0, e);
}

TEST_CASE("join aninhado em tarefa: falha da filha vira TASK_FAILED da mae") {
    std::string e = erro_de_join(fork_em("aninhada", "local", std::string("a")));
    CHECK_MSG(e.rfind("TASK_FAILED: TASK_FAILED: substr indices invalidos", 0) == 0, e);
}

TEST_CASE("destino invalido vindo do input: start nao lanca, join -> BAD_DESTINATION") {
    auto h = fork_em("soma_quadrados", "host:abc", 3.0);
    std::string e = erro_de_join(h);
    CHECK_MSG(e.rfind("BAD_DESTINATION: ", 0) == 0, e);
}

TEST_CASE("join_or_exit: no caminho de sucesso devolve o Value (coordenador)") {
    auto h = fork_em("eco", "local", std::string("zz"));
    CHECK(!__fj_in_task);
    minipar_rt::Value v = __fj_join(h, -1);  // usa join_or_exit
    CHECK(minipar_rt::value_cast<std::string>(v) == "zz|z");
}

TEST_CASE("set_build_id: valor do main e o que o worker confere") {
    CHECK(minipar_rt::build_id() == kBuildId);
}

// ---- remoto: worker = este mesmo binário (run_tests.py sobe os processos) ----------------------

TEST_CASE("remoto: numero, string, bool, lista e matriz cruzam a rede pelos wrappers") {
    std::string d = destino_remoto("MINIPAR_INTEROP_PORT");
    std::vector<double> nums{30, 1.25, -2, 1e6};
    std::vector<std::vector<int>> m(3, std::vector<int>(3, 5));
    auto h1 = fork_em("soma_quadrados", d, nums[0]);
    auto h2 = fork_em("escala", d, nums, -2);
    auto h3 = fork_em("eco", d, std::string("\xC3\xA7\xC3\xA3o"));
    auto h4 = fork_em("eh_par", d, static_cast<std::ptrdiff_t>(10));
    auto h5 = fork_em("traco", d, m);
    auto h6 = fork_em("marca", d, m, -9);
    auto h7 = fork_em("inverte", d, std::vector<bool>{false, false, true});
    auto h8 = fork_em("grade_texto", d, std::vector<std::vector<std::string>>{{"p"}, {"q"}});
    auto h9 = fork_em("media", d, std::vector<double>{2, 2, 2});  // double inteiro: 2.0 no JSON
    auto hv = fork_em("sem_retorno", d, 1);
    minipar_rt::TaskResult r1 = minipar_rt::join(h1, 20000);
    CHECK_MSG(r1.ok, std::string(minipar_rt::to_string(r1.error.code)) + ": " + r1.error.message);
    CHECK(r1.executed_by.rfind("local:", 0) != 0 && !r1.executed_by.empty());
    CHECK(minipar_rt::value_cast<int>(r1.value) == 8555);  // soma de i^2, i < 30
    CHECK(join_em_tarefa<std::vector<double>>(h2, 20000) == (std::vector<double>{-60, -2.5, 4, -2e6}));
    CHECK(join_em_tarefa<std::string>(h3, 20000) == std::string("\xC3\xA7\xC3\xA3o|\xC3"));
    CHECK(join_em_tarefa<bool>(h4, 20000) == true);
    CHECK(join_em_tarefa<int>(h5, 20000) == 15);
    auto marcada = join_em_tarefa<std::vector<std::vector<int>>>(h6, 20000);
    CHECK(marcada[0][1] == -9 && marcada[0][0] == 5 && marcada.size() == 3);
    CHECK(join_em_tarefa<std::vector<bool>>(h7, 20000) == (std::vector<bool>{true, true, false}));
    CHECK(join_em_tarefa<std::vector<std::vector<std::string>>>(h8, 20000) ==
          (std::vector<std::vector<std::string>>{{"p!"}, {"q"}}));
    minipar_rt::TaskResult r9 = minipar_rt::join(h9, 20000);
    CHECK(r9.ok && r9.value.is_float() && minipar_rt::value_cast<double>(r9.value) == 2.0);
    minipar_rt::TaskResult rv = minipar_rt::join(hv, 20000);
    CHECK(rv.ok && rv.value.is_none());
}

TEST_CASE("remoto: TASK_FAILED, aridade e UNKNOWN_FUNCTION voltam do worker") {
    std::string d = destino_remoto("MINIPAR_INTEROP_PORT");
    minipar_rt::TaskResult r = minipar_rt::join(fork_em("falha", d, std::string("a")), 20000);
    CHECK(!r.ok && r.error.code == minipar_rt::ErrorCode::TASK_FAILED);
    CHECK(r.executed_by.rfind("local:", 0) != 0);
    std::string e = erro_de_join(fork_em("aninhada", d, std::string("a")));
    CHECK_MSG(e.rfind("TASK_FAILED: TASK_FAILED: substr indices invalidos", 0) == 0, e);
    e = erro_de_join(fork_em("marca", d, 1));
    CHECK_MSG(e == "TASK_FAILED: aridade de marca", e);
    e = erro_de_join(fork_em("nao_registrada", d, 1));
    CHECK_MSG(e.rfind("UNKNOWN_FUNCTION: ", 0) == 0, e);
    // o worker continua atendendo depois dos erros
    CHECK(join_em_tarefa<int>(fork_em("soma_quadrados", d, 3.0), 20000) == 5);
}

TEST_CASE("remoto: worker com outro build_id -> VERSION_MISMATCH no join") {
    std::string d = destino_remoto("MINIPAR_INTEROP_PORT_OUTRO");
    std::string e = erro_de_join(fork_em("soma_quadrados", d, 3.0));
    CHECK_MSG(e.rfind("VERSION_MISMATCH: ", 0) == 0, e);
}

// ---- main no formato do programa gerado -------------------------------------------------------

int main(int argc, char** argv) {
    bool outro = false;
    for (int i = 1; i < argc; ++i) outro = outro || std::strcmp(argv[i], "--build-id-outro") == 0;
    minipar_rt::set_build_id(outro ? std::string(kBuildId) + "-outro" : std::string(kBuildId));
    registrar_tudo();
    if (int rc = minipar_rt::worker_main_if_requested(argc, argv); rc >= 0) return rc;

    if (argc > 1 && std::strcmp(argv[1], "--sondagem-join-coordenador") == 0) {
        // Igual ao main gerado: join fora de tarefa usa join_or_exit (stderr + exit 1).
        try {
            auto h = fork_em("falha", "local", std::string("a"));
            std::cout << ([&]() { auto c = h; auto t = -1; return minipar_rt::value_cast<int>(__fj_join(c, t)); }()) << std::endl;
            std::cout << "NAO DEVERIA CHEGAR AQUI" << std::endl;
            std::cout.flush(); std::cerr.flush(); std::_Exit(0);
        } catch (const std::exception& e) {
            std::cerr << "[CORE-07] " << e.what() << std::endl; std::cout.flush(); std::_Exit(1);
        }
    }
    int rc = rt_test::run_all(argc, argv);
    std::fflush(stdout);
    std::_Exit(rc);  // como os probes: não espera threads do executor/conexões
}
