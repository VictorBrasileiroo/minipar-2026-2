// Probe do join_or_exit (C-FJ-v1 §2.2.3): o runner espera stdout com o valor da tarefa ok,
// stderr "[minipar_rt] join task-2 falhou: TASK_FAILED: ..." e código de saída 1.
#include <iostream>
#include <stdexcept>

#include "minipar_rt/minipar_rt.hpp"

int main() {
    using namespace minipar_rt;
    register_function("ok", [](const TaskArgs& a) { return Value(a.at(0).as_int() + 1); });
    register_function("falha", [](const TaskArgs&) -> Value { throw std::runtime_error("erro de proposito"); });
    TaskHandle h1 = start("ok", {41});
    TaskHandle h2 = start("falha", {});
    std::cout << "ok=" << join_or_exit(h1).to_display() << std::endl;
    join_or_exit(h2);
    std::cout << "NAO DEVERIA CHEGAR AQUI" << std::endl;
    return 0;
}
