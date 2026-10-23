// minipar_rt — tipos públicos, registro de funções e estado das tarefas (C-FJ-v1 §2.3, §2.5).
#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdlib>
#include <deque>
#include <exception>
#include <functional>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <system_error>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#ifdef _WIN32
#include <process.h>
#else
#include <unistd.h>
#endif

#include "value.hpp"

namespace minipar_rt {

using TaskFn = std::function<Value(const TaskArgs&)>;

enum class ErrorCode {
    NONE,
    TASK_FAILED,
    UNKNOWN_FUNCTION,
    TIMEOUT,
    WORKER_UNAVAILABLE,
    WORKER_LOST,
    INVALID_HANDLE,
    PROTOCOL_ERROR,
    VERSION_MISMATCH,
    BAD_DESTINATION,
};

inline const char* to_string(ErrorCode c) {
    switch (c) {
        case ErrorCode::NONE: return "NONE";
        case ErrorCode::TASK_FAILED: return "TASK_FAILED";
        case ErrorCode::UNKNOWN_FUNCTION: return "UNKNOWN_FUNCTION";
        case ErrorCode::TIMEOUT: return "TIMEOUT";
        case ErrorCode::WORKER_UNAVAILABLE: return "WORKER_UNAVAILABLE";
        case ErrorCode::WORKER_LOST: return "WORKER_LOST";
        case ErrorCode::INVALID_HANDLE: return "INVALID_HANDLE";
        case ErrorCode::PROTOCOL_ERROR: return "PROTOCOL_ERROR";
        case ErrorCode::VERSION_MISMATCH: return "VERSION_MISMATCH";
        case ErrorCode::BAD_DESTINATION: return "BAD_DESTINATION";
    }
    return "UNKNOWN";
}

// Código desconhecido vindo da rede vira PROTOCOL_ERROR (nunca NONE).
inline ErrorCode error_code_from_string(const std::string& s) {
    for (ErrorCode c : {ErrorCode::TASK_FAILED, ErrorCode::UNKNOWN_FUNCTION, ErrorCode::TIMEOUT,
                        ErrorCode::WORKER_UNAVAILABLE, ErrorCode::WORKER_LOST, ErrorCode::INVALID_HANDLE,
                        ErrorCode::PROTOCOL_ERROR, ErrorCode::VERSION_MISMATCH, ErrorCode::BAD_DESTINATION}) {
        if (s == to_string(c)) return c;
    }
    return ErrorCode::PROTOCOL_ERROR;
}

struct TaskError {
    ErrorCode code = ErrorCode::NONE;
    std::string message;
};

struct TaskHandle {
    std::uint64_t id = 0;
    std::string task_id;  // "task-<n>", também usado no protocolo
};

struct TaskResult {
    bool ok = false;
    Value value;
    TaskError error;
    std::string task_id;
    std::string executed_by;  // "local:<pid>" ou "<host>:<pid>" do worker

    static TaskResult success(Value v, std::string task_id, std::string by) {
        TaskResult r;
        r.ok = true;
        r.value = std::move(v);
        r.task_id = std::move(task_id);
        r.executed_by = std::move(by);
        return r;
    }
    static TaskResult failure(ErrorCode code, std::string message, std::string task_id, std::string by = {}) {
        TaskResult r;
        r.ok = false;
        r.error = {code, std::move(message)};
        r.task_id = std::move(task_id);
        r.executed_by = std::move(by);
        return r;
    }
};

struct Destination {
    enum class Kind { Local, Remote, Invalid };
    Kind kind = Kind::Local;
    std::string host;
    std::uint16_t port = 0;
    std::string text = "local";   // texto original, para mensagens
    std::string problem;          // motivo, quando Invalid

    static Destination local() { return Destination{}; }

    static Destination remote(std::string host, std::uint16_t port) {
        Destination d;
        d.text = host + ":" + std::to_string(port);
        if (host.empty() || port == 0) {
            d.kind = Kind::Invalid;
            d.problem = "host vazio ou porta 0";
            return d;
        }
        d.kind = Kind::Remote;
        d.host = std::move(host);
        d.port = port;
        return d;
    }

    // "local" (sem diferenciar maiúsculas) ou "host:porta" com porta 1..65535. IPv6 literal não é aceito.
    static Destination parse(const std::string& raw) {
        std::size_t b = raw.find_first_not_of(" \t\r\n");
        std::size_t e = raw.find_last_not_of(" \t\r\n");
        std::string t = (b == std::string::npos) ? std::string() : raw.substr(b, e - b + 1);
        std::string lower;
        for (char c : t) lower += static_cast<char>((c >= 'A' && c <= 'Z') ? c - 'A' + 'a' : c);
        if (lower == "local") return local();
        Destination bad;
        bad.kind = Kind::Invalid;
        bad.text = raw;
        std::size_t colon = t.rfind(':');
        if (t.empty() || colon == std::string::npos || colon == 0 || colon + 1 == t.size() ||
            t.find(':') != colon) {
            bad.problem = "esperado \"local\" ou \"host:porta\"";
            return bad;
        }
        std::string port_txt = t.substr(colon + 1);
        if (port_txt.size() > 5) {
            bad.problem = "porta invalida";
            return bad;
        }
        unsigned long port = 0;
        for (char c : port_txt) {
            if (c < '0' || c > '9') {
                bad.problem = "porta invalida";
                return bad;
            }
            port = port * 10 + static_cast<unsigned long>(c - '0');
        }
        if (port == 0 || port > 65535) {
            bad.problem = "porta fora de 1..65535";
            return bad;
        }
        return remote(t.substr(0, colon), static_cast<std::uint16_t>(port));
    }
};

namespace detail {

inline long current_pid() {
#ifdef _WIN32
    return static_cast<long>(_getpid());
#else
    return static_cast<long>(getpid());
#endif
}

inline std::string local_executor() { return "local:" + std::to_string(current_pid()); }

// Estado compartilhado de uma tarefa: quem executa preenche, quem faz join espera.
struct TaskState {
    std::mutex m;
    std::condition_variable cv;
    bool done = false;
    bool remote = false;
    TaskResult result;
    std::string task_id;
};

// Conclui a tarefa uma única vez (a primeira conclusão vence: resposta x perda de conexão).
inline void complete(const std::shared_ptr<TaskState>& st, TaskResult r) {
    {
        std::lock_guard<std::mutex> lk(st->m);
        if (st->done) return;
        r.task_id = st->task_id;
        st->result = std::move(r);
        st->done = true;
    }
    st->cv.notify_all();
}

struct Registry {
    std::mutex m;
    std::unordered_map<std::string, TaskFn> functions;
    std::unordered_map<std::uint64_t, std::shared_ptr<TaskState>> tasks;
    std::atomic<std::uint64_t> next_id{1};
    std::string build_id = "minipar-dev";

    static Registry& get() {
        // Intencionalmente nunca destruída: tarefas em threads destacadas podem terminar depois do main.
        static Registry* r = new Registry();
        return *r;
    }
};

// Executor de threads persistentes que cresce sob demanda: cada job ganha uma thread livre ou uma nova,
// então tarefas continuam concorrentes como threads próprias. Não usa std::thread::detach: no MinGW-w64
// (winpthreads, G++ 16.2 UCRT64) uma thread destacada às vezes nunca executa o corpo (~1 em 2000 no teste
// de 4000 threads), o que deixava join esperando para sempre. Nunca destruído: threads ociosas acabam
// com o processo.
class Executor {
public:
    static Executor& get() {
        static Executor* e = new Executor();
        return *e;
    }

    // Lança std::system_error só se não existir nenhuma thread capaz de executar o job.
    void submit(std::function<void()> job) {
        std::unique_lock<std::mutex> lk(m_);
        queue_.push_back(std::move(job));
        if (idle_ >= queue_.size()) {
            cv_.notify_one();
            return;
        }
        try {
            threads_.emplace_back([this] { loop(); });
        } catch (const std::system_error&) {
            if (threads_.empty()) {
                queue_.pop_back();
                throw;
            }
            // Sem thread nova: o job espera na fila até uma thread existente ficar livre.
        }
    }

    std::size_t thread_count() {
        std::lock_guard<std::mutex> lk(m_);
        return threads_.size();
    }

private:
    void loop() {
        std::unique_lock<std::mutex> lk(m_);
        for (;;) {
            while (queue_.empty()) {
                ++idle_;
                cv_.wait(lk);
                --idle_;
            }
            auto job = std::move(queue_.front());
            queue_.pop_front();
            lk.unlock();
            job();
            lk.lock();
        }
    }

    std::mutex m_;
    std::condition_variable cv_;
    std::deque<std::function<void()>> queue_;
    std::size_t idle_ = 0;
    std::vector<std::thread> threads_;
};

inline std::optional<TaskFn> find_function(const std::string& id) {
    auto& r = Registry::get();
    std::lock_guard<std::mutex> lk(r.m);
    auto it = r.functions.find(id);
    if (it == r.functions.end()) return std::nullopt;
    return it->second;
}

// Executa a função registrada e converte exceções em TASK_FAILED (RT-08). Usado no local e no worker.
inline TaskResult execute(const std::string& function_id, const TaskArgs& args, const std::string& executor) {
    auto fn = find_function(function_id);
    if (!fn) {
        return TaskResult::failure(ErrorCode::UNKNOWN_FUNCTION, "funcao nao registrada: " + function_id, {}, executor);
    }
    try {
        return TaskResult::success((*fn)(args), {}, executor);
    } catch (const std::exception& ex) {
        return TaskResult::failure(ErrorCode::TASK_FAILED, ex.what(), {}, executor);
    } catch (...) {
        return TaskResult::failure(ErrorCode::TASK_FAILED, "excecao desconhecida", {}, executor);
    }
}

inline std::shared_ptr<TaskState> new_task(TaskHandle& h, bool remote) {
    auto& r = Registry::get();
    auto st = std::make_shared<TaskState>();
    h.id = r.next_id.fetch_add(1);
    h.task_id = "task-" + std::to_string(h.id);
    st->task_id = h.task_id;
    st->remote = remote;
    std::lock_guard<std::mutex> lk(r.m);
    r.tasks.emplace(h.id, st);
    return st;
}

inline int default_remote_timeout_ms() {
    static const int value = [] {
        const char* env = std::getenv("MINIPAR_RT_REMOTE_TIMEOUT_MS");
        if (env && *env) {
            char* end = nullptr;
            long v = std::strtol(env, &end, 10);
            if (end && *end == '\0' && v > 0 && v < 24L * 3600 * 1000) return static_cast<int>(v);
        }
        return 60000;
    }();
    return value;
}

}  // namespace detail

inline void register_function(const std::string& function_id, TaskFn fn) {
    auto& r = detail::Registry::get();
    std::lock_guard<std::mutex> lk(r.m);
    r.functions[function_id] = std::move(fn);
}

inline void set_build_id(std::string build_id) {
    auto& r = detail::Registry::get();
    std::lock_guard<std::mutex> lk(r.m);
    r.build_id = std::move(build_id);
}

inline std::string build_id() {
    auto& r = detail::Registry::get();
    std::lock_guard<std::mutex> lk(r.m);
    return r.build_id;
}

}  // namespace minipar_rt
