// Worker de teste do RUN-02: binário pré-compilado com as funções que o test_remote usa.
// Uso: test_worker --minipar-worker <porta> [--bind <ip>]
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <thread>

#include "minipar_rt/minipar_rt.hpp"

using namespace minipar_rt;

int main(int argc, char** argv) {
    set_build_id("minipar-rt-test");
    register_function("soma_quadrados", [](const TaskArgs& a) {
        long long n = a.at(0).as_int(), s = 0;
        for (long long i = 0; i < n; ++i) s += i * i;
        return Value(s);
    });
    // dormir(ms, etiqueta) -> etiqueta
    register_function("dormir", [](const TaskArgs& a) {
        std::this_thread::sleep_for(std::chrono::milliseconds(a.at(0).as_int()));
        return a.at(1);
    });
    register_function("eco", [](const TaskArgs& a) { return Value(Value::List(a.begin(), a.end())); });
    register_function("falha", [](const TaskArgs&) -> Value { throw std::runtime_error("falha proposital"); });
    register_function("tamanho", [](const TaskArgs& a) { return Value(static_cast<long long>(a.at(0).as_list().size())); });
    register_function("gera_lista", [](const TaskArgs& a) {
        Value::List l;
        for (long long i = 0; i < a.at(0).as_int(); ++i) l.push_back(Value(i));
        return Value(std::move(l));
    });
    // gera_texto(n) -> string com n bytes (resultado maior que o frame máximo quando n > 8 MiB)
    register_function("gera_texto", [](const TaskArgs& a) {
        return Value(std::string(static_cast<std::size_t>(a.at(0).as_int()), 'y'));
    });
    // morrer(): encerra o processo do worker no meio da tarefa (simula queda da máquina/processo).
    register_function("morrer", [](const TaskArgs&) -> Value {
        std::fprintf(stderr, "[test_worker] morrer() chamado: encerrando com codigo 3\n");
        std::fflush(stderr);
        std::_Exit(3);
    });

    int rc = worker_main_if_requested(argc, argv);
    if (rc >= 0) return rc;
    std::fprintf(stderr, "uso: %s --minipar-worker <porta> [--bind <ip>]\n", argv[0]);
    return 2;
}
