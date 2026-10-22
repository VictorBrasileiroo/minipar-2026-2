// minipar_rt — processo worker (C-FJ-v1 §2.6). Executa só funções registradas no próprio binário.
// Cada conexão: HELLO obrigatório -> HELLO_OK; cada TASK roda em uma thread e responde RESULT quando termina.
// Frame/JSON inválido ou versão diferente: ERROR e fecha SÓ aquela conexão; o worker continua aceitando outras.
#pragma once

#include <chrono>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <string>

#include "core.hpp"
#include "json.hpp"
#include "net.hpp"
#include "remote.hpp"

namespace minipar_rt {

namespace detail {

inline const std::string& worker_id() {
    static const std::string id = net::hostname() + ":" + std::to_string(current_pid());
    return id;
}

inline void worker_log(const char* fmt, ...) {
    static std::mutex m;
    std::lock_guard<std::mutex> lk(m);
    std::fprintf(stderr, "[minipar_worker %s] ", worker_id().c_str());
    va_list ap;
    va_start(ap, fmt);
    std::vfprintf(stderr, fmt, ap);
    va_end(ap);
    std::fputc('\n', stderr);
    std::fflush(stderr);
}

struct WorkerConnection {
    net::Socket sock;
    std::mutex write_m;
    std::string peer;

    bool send(const Json& msg) {
        std::lock_guard<std::mutex> lk(write_m);
        return net::write_frame(sock.get(), msg.dump());
    }
    void reject(ErrorCode code, const std::string& message) {
        worker_log("conexao %s rejeitada: %s: %s", peer.c_str(), to_string(code), message.c_str());
        send(make_error_message(code, message));
        std::lock_guard<std::mutex> lk(write_m);
        sock.shutdown_both();
    }
};

inline void run_task(const std::shared_ptr<WorkerConnection>& c, std::string request_id, std::string task_id,
                     std::string function_id, TaskArgs args) {
    worker_log("TASK %s fn=%s de %s: inicio", task_id.c_str(), function_id.c_str(), c->peer.c_str());
    auto t0 = std::chrono::steady_clock::now();
    TaskResult r = execute(function_id, args, worker_id());
    long long ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - t0).count();
    Json::Object fields{{"request_id", request_id}, {"task_id", task_id}};
    if (r.ok) {
        try {
            Json result = Json::from_value(r.value);
            fields.emplace_back("status", "ok");
            fields.emplace_back("result", std::move(result));
        } catch (const JsonError& ex) {
            r = TaskResult::failure(ErrorCode::TASK_FAILED, std::string("resultado nao pode cruzar a rede: ") + ex.what(), {});
        }
    }
    if (!r.ok) {
        fields.emplace_back("status", "error");
        fields.emplace_back("error", Json(Json::Object{{"code", to_string(r.error.code)}, {"message", r.error.message}}));
    }
    fields.emplace_back("worker_id", worker_id());
    std::string payload = make_message("RESULT", std::move(fields)).dump();
    bool sent = false;
    if (payload.size() <= net::kMaxFrame) {
        std::lock_guard<std::mutex> lk(c->write_m);
        sent = net::write_frame(c->sock.get(), payload);
    }
    worker_log("RESULT %s fn=%s %s em %lld ms%s", task_id.c_str(), function_id.c_str(),
               r.ok ? "ok" : to_string(r.error.code), ms, sent ? "" : " (nao entregue: conexao fechada)");
}

inline void serve_connection(std::shared_ptr<WorkerConnection> c) {
    net::socket_t fd = c->sock.get();
    std::string frame, err;

    net::set_recv_timeout(fd, 10000);  // HELLO precisa chegar em 10 s
    net::FrameStatus fs = net::read_frame(fd, frame, err);
    if (fs == net::FrameStatus::Invalid) return c->reject(ErrorCode::PROTOCOL_ERROR, err);
    if (fs == net::FrameStatus::Closed) {
        worker_log("conexao %s encerrada antes do HELLO", c->peer.c_str());
        return;
    }
    try {
        Json hello = Json::parse(frame);
        if (hello.at("type").str() != "HELLO")
            return c->reject(ErrorCode::PROTOCOL_ERROR, "primeira mensagem deve ser HELLO");
        if (hello.at("protocol_version").integer() != kProtocolVersion)
            return c->reject(ErrorCode::VERSION_MISMATCH,
                             "protocol_version " + std::to_string(hello.at("protocol_version").integer()) +
                                 " nao suportada (worker usa " + std::to_string(kProtocolVersion) + ")");
        if (hello.at("build_id").str() != build_id())
            return c->reject(ErrorCode::VERSION_MISMATCH,
                             "build_id do coordenador difere do worker (" + build_id() + ")");
    } catch (const JsonError& ex) {
        return c->reject(ErrorCode::PROTOCOL_ERROR, ex.what());
    }
    if (!c->send(make_message("HELLO_OK", {{"worker_id", worker_id()},
                                           {"host", net::hostname()},
                                           {"pid", static_cast<long long>(current_pid())},
                                           {"build_id", build_id()}}))) {
        return;
    }
    net::set_recv_timeout(fd, 0);
    worker_log("conexao de %s aceita (build_id ok)", c->peer.c_str());

    for (;;) {
        fs = net::read_frame(fd, frame, err);
        if (fs == net::FrameStatus::Closed) {
            worker_log("conexao de %s encerrada", c->peer.c_str());
            return;
        }
        if (fs == net::FrameStatus::Invalid) return c->reject(ErrorCode::PROTOCOL_ERROR, err);
        std::string request_id, task_id, function_id;
        TaskArgs args;
        try {
            Json msg = Json::parse(frame);
            if (msg.at("type").str() != "TASK")
                return c->reject(ErrorCode::PROTOCOL_ERROR, "mensagem inesperada: " + msg.at("type").str());
            request_id = msg.at("request_id").str();
            task_id = msg.at("task_id").str();
            function_id = msg.at("function_id").str();
            for (const auto& a : msg.at("args").array()) args.push_back(a.to_value());
        } catch (const JsonError& ex) {
            return c->reject(ErrorCode::PROTOCOL_ERROR, ex.what());
        }
        try {
            Executor::get().submit([c, request_id, task_id, function_id, args = std::move(args)]() mutable {
                run_task(c, std::move(request_id), std::move(task_id), std::move(function_id), std::move(args));
            });
        } catch (const std::system_error& ex) {
            return c->reject(ErrorCode::TASK_FAILED, std::string("worker sem threads: ") + ex.what());
        }
    }
}

}  // namespace detail

// Escuta e atende coordenadores até o processo terminar. Só retorna (com 2) se não conseguir escutar.
inline int run_worker(std::uint16_t port, const std::string& bind_address = "127.0.0.1") {
    std::string err;
    net::Socket listener = net::listen_tcp(bind_address, port, err);
    if (!listener.valid()) {
        std::fprintf(stderr, "[minipar_worker] nao foi possivel escutar: %s\n", err.c_str());
        return 2;
    }
    detail::worker_log("escutando em %s:%u (host=%s pid=%ld build_id=%s)", bind_address.c_str(),
                       static_cast<unsigned>(net::local_port(listener.get())), net::hostname().c_str(),
                       detail::current_pid(), build_id().c_str());
    for (;;) {
        std::string peer;
        net::Socket s = net::accept_tcp(listener.get(), peer);
        if (!s.valid()) continue;
        auto c = std::make_shared<detail::WorkerConnection>();
        c->sock = std::move(s);
        c->peer = peer;
        try {
            detail::Executor::get().submit([c] { detail::serve_connection(c); });
        } catch (const std::system_error&) {
            c->reject(ErrorCode::WORKER_UNAVAILABLE, "worker sem threads");
        }
    }
}

// `programa --minipar-worker <porta> [--bind <ip>]` vira worker; sem a flag devolve -1 (C-FJ-v1 §2.2.3).
inline int worker_main_if_requested(int argc, char** argv) {
    int port = -1;
    std::string bind = "127.0.0.1";
    bool requested = false;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--minipar-worker") == 0) {
            requested = true;
            if (i + 1 < argc) {
                char* end = nullptr;
                long v = std::strtol(argv[i + 1], &end, 10);
                if (end && *end == '\0' && v > 0 && v <= 65535) port = static_cast<int>(v);
                ++i;
            }
        } else if (std::strcmp(argv[i], "--bind") == 0 && i + 1 < argc) {
            bind = argv[++i];
        }
    }
    if (!requested) return -1;
    if (port < 0) {
        std::fprintf(stderr, "uso: %s --minipar-worker <porta 1..65535> [--bind <ip>]\n", argc > 0 ? argv[0] : "programa");
        return 2;
    }
    return run_worker(static_cast<std::uint16_t>(port), bind);
}

}  // namespace minipar_rt
