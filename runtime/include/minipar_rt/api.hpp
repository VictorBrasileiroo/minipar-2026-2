// minipar_rt — start/join (C-FJ-v1 §2.3, garantias RT-01..RT-10).
#pragma once

#include <chrono>
#include <cstdio>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <system_error>
#include <thread>
#include <utility>

#include "core.hpp"

namespace minipar_rt {

namespace detail {

// Transporte remoto: implementado no RUN-02. Neste build a tarefa remota termina com erro explícito.
inline void start_remote(const std::shared_ptr<TaskState>& st, const std::string& /*function_id*/,
                         TaskArgs /*args*/, const Destination& where) {
    complete(st, TaskResult::failure(ErrorCode::WORKER_UNAVAILABLE,
                                     "transporte remoto nao disponivel neste build (destino " + where.text + ")",
                                     st->task_id));
}

inline void start_local(const std::shared_ptr<TaskState>& st, const std::string& function_id, TaskArgs args) {
    if (!find_function(function_id)) {
        complete(st, TaskResult::failure(ErrorCode::UNKNOWN_FUNCTION, "funcao nao registrada: " + function_id,
                                         st->task_id, local_executor()));
        return;
    }
    try {
        // args é capturado por valor (movido): a tarefa não vê alterações posteriores do chamador (RT-03).
        Executor::get().submit([st, function_id, args = std::move(args)]() {
            complete(st, execute(function_id, args, local_executor()));
        });
    } catch (const std::system_error& ex) {
        complete(st, TaskResult::failure(ErrorCode::TASK_FAILED, std::string("nao foi possivel criar thread: ") + ex.what(),
                                         st->task_id, local_executor()));
    }
}

}  // namespace detail

// Dispara a tarefa e retorna sem esperar o cálculo (RT-01). Nunca lança por destino ruim (RT-02).
inline TaskHandle start(const std::string& function_id, TaskArgs args,
                        const Destination& where = Destination::local()) {
    TaskHandle h;
    switch (where.kind) {
        case Destination::Kind::Invalid: {
            auto st = detail::new_task(h, false);
            detail::complete(st, TaskResult::failure(ErrorCode::BAD_DESTINATION,
                                                     "destino invalido '" + where.text + "': " + where.problem,
                                                     h.task_id));
            break;
        }
        case Destination::Kind::Remote: {
            auto st = detail::new_task(h, true);
            detail::start_remote(st, function_id, std::move(args), where);
            break;
        }
        case Destination::Kind::Local: {
            auto st = detail::new_task(h, false);
            detail::start_local(st, function_id, std::move(args));
            break;
        }
    }
    return h;
}

// Espera o resultado. timeout_ms < 0: sem limite no local, limite padrão no remoto (RT-06).
// TIMEOUT mantém o handle válido (RT-05); resultado coletado invalida o handle (RT-07).
inline TaskResult join(const TaskHandle& handle, int timeout_ms = -1) {
    auto& reg = detail::Registry::get();
    std::shared_ptr<detail::TaskState> st;
    {
        std::lock_guard<std::mutex> lk(reg.m);
        auto it = reg.tasks.find(handle.id);
        if (it != reg.tasks.end()) st = it->second;
    }
    if (!st) {
        return TaskResult::failure(ErrorCode::INVALID_HANDLE, "handle desconhecido ou ja coletado: " + handle.task_id,
                                   handle.task_id);
    }
    int limit = timeout_ms;
    if (limit < 0 && st->remote) limit = detail::default_remote_timeout_ms();

    TaskResult res;
    {
        std::unique_lock<std::mutex> lk(st->m);
        if (limit < 0) {
            st->cv.wait(lk, [&] { return st->done; });
        } else if (!st->cv.wait_for(lk, std::chrono::milliseconds(limit), [&] { return st->done; })) {
            return TaskResult::failure(ErrorCode::TIMEOUT,
                                       "tarefa nao concluiu em " + std::to_string(limit) + " ms", handle.task_id);
        }
        res = st->result;
    }
    {
        std::lock_guard<std::mutex> lk(reg.m);
        auto it = reg.tasks.find(handle.id);
        if (it == reg.tasks.end() || it->second != st) {
            return TaskResult::failure(ErrorCode::INVALID_HANDLE, "resultado ja coletado por outro join: " + handle.task_id,
                                       handle.task_id);
        }
        reg.tasks.erase(it);
    }
    return res;
}

// Usado pelo código gerado: devolve o valor ou encerra o programa com mensagem e código 1 (C-FJ-v1 §2.2.3).
inline Value join_or_exit(const TaskHandle& handle, int timeout_ms = -1) {
    TaskResult r = join(handle, timeout_ms);
    if (r.ok) return std::move(r.value);
    std::cout.flush();
    std::fprintf(stderr, "[minipar_rt] join %s falhou: %s: %s\n", handle.task_id.c_str(), to_string(r.error.code),
                 r.error.message.c_str());
    std::fflush(stderr);
    std::_Exit(1);  // não roda destrutores estáticos enquanto tarefas destacadas ainda executam
}

}  // namespace minipar_rt
