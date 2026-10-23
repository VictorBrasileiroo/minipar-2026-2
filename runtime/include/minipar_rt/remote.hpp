// minipar_rt — lado coordenador do protocolo remoto (C-FJ-v1 §2.6).
// Uma conexão persistente por destino; conexão, HELLO e envio dos TASK acontecem fora do start (RT-01):
// o start só enfileira, e uma thread escritora por conexão envia. RESULT é associado pelo task_id (RT-04);
// queda da conexão ou envio parado além do limite conclui as pendentes com WORKER_LOST (RT-09).
#pragma once

#include <condition_variable>
#include <cstdlib>
#include <deque>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "core.hpp"
#include "json.hpp"
#include "net.hpp"

namespace minipar_rt {

inline constexpr int kProtocolVersion = 1;

namespace detail {

inline const std::string& run_request_id() {
    static const std::string id = "run-" + std::to_string(current_pid());
    return id;
}

// Limite de um envio sem progresso (worker que parou de ler); estourado, a conexão é encerrada.
inline int send_timeout_ms() {
    static const int value = [] {
        const char* env = std::getenv("MINIPAR_RT_SEND_TIMEOUT_MS");
        if (env && *env) {
            char* end = nullptr;
            long v = std::strtol(env, &end, 10);
            if (end && *end == '\0' && v > 0 && v < 24L * 3600 * 1000) return static_cast<int>(v);
        }
        return 10000;
    }();
    return value;
}

// Toda mensagem recebida (não só o HELLO) precisa ter a versão do protocolo deste binário.
inline bool same_protocol_version(const Json& msg) {
    const Json* v = msg.find("protocol_version");
    return v && v->is_int() && v->integer() == kProtocolVersion;
}

inline Json make_message(const char* type, Json::Object fields) {
    Json::Object o;
    o.emplace_back("protocol_version", kProtocolVersion);
    o.emplace_back("type", type);
    for (auto& f : fields) o.push_back(std::move(f));
    return Json(std::move(o));
}

inline Json make_error_message(ErrorCode code, const std::string& message) {
    return make_message("ERROR", {{"error", Json(Json::Object{{"code", to_string(code)}, {"message", message}})}});
}

// Converte um RESULT recebido em TaskResult. Lança JsonError se faltar campo obrigatório.
inline TaskResult result_from_message(const Json& msg, const std::string& fallback_worker) {
    const Json* w = msg.find("worker_id");
    std::string by = (w && w->is_string()) ? w->str() : fallback_worker;
    const std::string& status = msg.at("status").str();
    if (status == "ok") return TaskResult::success(msg.at("result").to_value(), {}, by);
    if (status == "error") {
        const Json& e = msg.at("error");
        return TaskResult::failure(error_code_from_string(e.at("code").str()), e.at("message").str(), {}, by);
    }
    throw JsonError("status desconhecido: " + status);
}

class ConnectionPool;

class RemoteConnection : public std::enable_shared_from_this<RemoteConnection> {
public:
    explicit RemoteConnection(Destination d) : dest_(std::move(d)), key_(dest_.host + ":" + std::to_string(dest_.port)) {}

    const std::string& key() const { return key_; }

    void begin() {
        auto self = shared_from_this();
        try {
            Executor::get().submit([self] { self->run(); });
        } catch (const std::system_error& ex) {
            fail_all(ErrorCode::WORKER_UNAVAILABLE, std::string("sem thread para a conexao: ") + ex.what());
        }
    }

    void submit(const std::shared_ptr<TaskState>& st, std::string payload) {
        std::unique_lock<std::mutex> lk(m_);
        if (state_ == State::Dead) {
            TaskResult r = TaskResult::failure(dead_code_, dead_msg_, st->task_id, worker_id_);
            lk.unlock();
            complete(st, std::move(r));
            return;
        }
        pending_[st->task_id] = st;
        // Nunca envia aqui: um worker que parou de ler bloquearia o start (RT-01). A escritora envia.
        queued_.push_back(std::move(payload));
        lk.unlock();
        send_cv_.notify_one();
    }

private:
    enum class State { Connecting, Ready, Dead };

    void run();
    void write_loop(net::socket_t fd);
    void fail_all(ErrorCode code, const std::string& msg);

    Destination dest_;
    std::string key_;
    std::mutex m_;
    State state_ = State::Connecting;
    std::unordered_map<std::string, std::shared_ptr<TaskState>> pending_;
    std::deque<std::string> queued_;
    std::condition_variable send_cv_;
    ErrorCode dead_code_ = ErrorCode::WORKER_LOST;
    std::string dead_msg_;
    std::string worker_id_;
    std::mutex sock_m_;  // protege só a atribuição e o shutdown de sock_; os envios usam o fd sem trava
    net::Socket sock_;
};

class ConnectionPool {
public:
    static ConnectionPool& get() {
        static ConnectionPool* p = new ConnectionPool();  // nunca destruído (threads de leitura vivas)
        return *p;
    }

    std::shared_ptr<RemoteConnection> connection_for(const Destination& d) {
        std::string key = d.host + ":" + std::to_string(d.port);
        std::lock_guard<std::mutex> lk(m_);
        auto it = conns_.find(key);
        if (it != conns_.end()) return it->second;
        auto c = std::make_shared<RemoteConnection>(d);
        conns_.emplace(key, c);
        c->begin();
        return c;
    }

    void remove(const std::string& key, const RemoteConnection* which) {
        std::lock_guard<std::mutex> lk(m_);
        auto it = conns_.find(key);
        if (it != conns_.end() && it->second.get() == which) conns_.erase(it);
    }

private:
    std::mutex m_;
    std::unordered_map<std::string, std::shared_ptr<RemoteConnection>> conns_;
};

inline void RemoteConnection::fail_all(ErrorCode code, const std::string& msg) {
    std::unordered_map<std::string, std::shared_ptr<TaskState>> victims;
    std::string by;
    {
        std::lock_guard<std::mutex> lk(m_);
        if (state_ != State::Dead) {
            state_ = State::Dead;
            dead_code_ = code;
            dead_msg_ = msg;
        }
        victims.swap(pending_);
        queued_.clear();
        by = worker_id_;
    }
    send_cv_.notify_all();  // a escritora vê Dead e termina
    ConnectionPool::get().remove(key_, this);  // próximo start para o destino abre conexão nova
    {
        // Não espera envio em curso: shutdown acorda a leitura e faz um send bloqueado falhar.
        std::lock_guard<std::mutex> lk(sock_m_);
        sock_.shutdown_both();
    }
    for (auto& kv : victims) complete(kv.second, TaskResult::failure(code, msg, kv.first, by));
}

inline void RemoteConnection::run() {
    std::string err;
    net::Socket s = net::connect_tcp(dest_.host, dest_.port, 3000, err);
    if (!s.valid()) {
        fail_all(ErrorCode::WORKER_UNAVAILABLE, "worker " + key_ + " indisponivel: " + err);
        return;
    }
    net::socket_t fd = s.get();
    net::set_send_timeout(fd, send_timeout_ms());
    {
        std::lock_guard<std::mutex> lk(sock_m_);
        sock_ = std::move(s);
    }

    // Handshake: HELLO -> HELLO_OK (ou ERROR VERSION_MISMATCH), com limite de 5 s.
    net::set_recv_timeout(fd, 5000);
    Json hello = make_message("HELLO", {{"build_id", build_id()}, {"request_id", run_request_id()}});
    if (!net::write_frame(fd, hello.dump())) {
        fail_all(ErrorCode::WORKER_UNAVAILABLE, "falha ao enviar HELLO para " + key_);
        return;
    }
    std::string frame;
    net::FrameStatus fs = net::read_frame(fd, frame, err);
    if (fs != net::FrameStatus::Ok) {
        fail_all(fs == net::FrameStatus::Invalid ? ErrorCode::PROTOCOL_ERROR : ErrorCode::WORKER_UNAVAILABLE,
                 "handshake com " + key_ + " falhou: " + err);
        return;
    }
    std::string worker_id;
    try {
        Json reply = Json::parse(frame);
        const std::string& type = reply.at("type").str();
        if (type == "ERROR") {
            const Json& e = reply.at("error");
            fail_all(error_code_from_string(e.at("code").str()), "worker " + key_ + ": " + e.at("message").str());
            return;
        }
        if (!same_protocol_version(reply)) {
            fail_all(ErrorCode::VERSION_MISMATCH, "protocol_version do worker " + key_ + " difere");
            return;
        }
        if (type != "HELLO_OK") {
            fail_all(ErrorCode::PROTOCOL_ERROR, "resposta inesperada ao HELLO de " + key_ + ": " + type);
            return;
        }
        if (reply.at("build_id").str() != build_id()) {
            fail_all(ErrorCode::VERSION_MISMATCH, "build_id do worker " + key_ + " difere");
            return;
        }
        worker_id = reply.at("worker_id").str();
    } catch (const JsonError& ex) {
        fail_all(ErrorCode::PROTOCOL_ERROR, "HELLO_OK invalido de " + key_ + ": " + ex.what());
        return;
    }
    net::set_recv_timeout(fd, 0);

    {
        std::lock_guard<std::mutex> lk(m_);
        if (state_ == State::Dead) return;
        state_ = State::Ready;
        worker_id_ = worker_id;
    }
    auto self = shared_from_this();
    try {
        Executor::get().submit([self, fd] { self->write_loop(fd); });
    } catch (const std::system_error& ex) {
        fail_all(ErrorCode::WORKER_LOST, std::string("sem thread de envio para ") + key_ + ": " + ex.what());
        return;
    }

    // Leitura dos RESULT até a conexão cair.
    for (;;) {
        fs = net::read_frame(fd, frame, err);
        if (fs == net::FrameStatus::Closed) {
            fail_all(ErrorCode::WORKER_LOST, "conexao com o worker " + worker_id + " (" + key_ + ") perdida: " + err);
            return;
        }
        if (fs == net::FrameStatus::Invalid) {
            fail_all(ErrorCode::PROTOCOL_ERROR, "frame invalido de " + key_ + ": " + err);
            return;
        }
        try {
            Json msg = Json::parse(frame);
            if (!same_protocol_version(msg)) {
                fail_all(ErrorCode::VERSION_MISMATCH, "mensagem de " + key_ + " com protocol_version diferente");
                return;
            }
            const std::string& type = msg.at("type").str();
            if (type == "RESULT") {
                std::string task_id = msg.at("task_id").str();
                TaskResult r = result_from_message(msg, worker_id);
                std::shared_ptr<TaskState> st;
                {
                    std::lock_guard<std::mutex> lk(m_);
                    auto it = pending_.find(task_id);
                    if (it != pending_.end()) {
                        st = it->second;
                        pending_.erase(it);
                    }
                }
                if (!st) {
                    fail_all(ErrorCode::PROTOCOL_ERROR, "RESULT para tarefa desconhecida: " + task_id);
                    return;
                }
                complete(st, std::move(r));
            } else if (type == "ERROR") {
                const Json& e = msg.at("error");
                fail_all(error_code_from_string(e.at("code").str()), "worker " + key_ + ": " + e.at("message").str());
                return;
            } else {
                fail_all(ErrorCode::PROTOCOL_ERROR, "mensagem inesperada de " + key_ + ": " + type);
                return;
            }
        } catch (const std::exception& ex) {
            fail_all(ErrorCode::PROTOCOL_ERROR, "mensagem invalida de " + key_ + ": " + ex.what());
            return;
        }
    }
}

// Única thread que envia TASK nesta conexão, na ordem do start. Um envio que não progride por
// send_timeout_ms() falha (SO_SNDTIMEO) e encerra a conexão: o coordenador nunca fica preso no send.
inline void RemoteConnection::write_loop(net::socket_t fd) {
    for (;;) {
        std::string payload;
        {
            std::unique_lock<std::mutex> lk(m_);
            send_cv_.wait(lk, [this] { return state_ == State::Dead || !queued_.empty(); });
            if (state_ == State::Dead) return;
            payload = std::move(queued_.front());
            queued_.pop_front();
        }
        if (!net::write_frame(fd, payload)) {
            fail_all(ErrorCode::WORKER_LOST, "envio de TASK para " + key_ + " falhou ou ficou parado por mais de " +
                                                 std::to_string(send_timeout_ms()) + " ms");
            return;
        }
    }
}

inline void start_remote(const std::shared_ptr<TaskState>& st, const std::string& function_id, TaskArgs args,
                         const Destination& where) {
    std::string payload;
    try {
        Json::Array jargs;
        jargs.reserve(args.size());
        for (const auto& a : args) jargs.push_back(Json::from_value(a));
        payload = make_message("TASK", {{"request_id", run_request_id()},
                                        {"task_id", st->task_id},
                                        {"function_id", function_id},
                                        {"args", Json(std::move(jargs))}})
                      .dump();
    } catch (const JsonError& ex) {
        complete(st, TaskResult::failure(ErrorCode::TASK_FAILED, std::string("argumento nao pode cruzar a rede: ") + ex.what(),
                                         st->task_id));
        return;
    }
    if (payload.size() > net::kMaxFrame) {
        complete(st, TaskResult::failure(ErrorCode::TASK_FAILED, "argumentos excedem o frame maximo de 8 MiB", st->task_id));
        return;
    }
    ConnectionPool::get().connection_for(where)->submit(st, std::move(payload));
}

}  // namespace detail
}  // namespace minipar_rt
