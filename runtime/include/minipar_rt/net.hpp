// minipar_rt — sockets TCP portáveis (Winsock/POSIX) e frames com tamanho (C-FJ-v1 §2.6).
// Frame = 4 bytes de tamanho big-endian + payload; 1 <= tamanho <= 8 MiB. send_all/recv_exact
// toleram envio/recebimento parcial (fragmentação).
#pragma once

#include <cstdint>
#include <cstring>
#include <mutex>
#include <string>
#include <utility>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#else
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#include <cerrno>
#endif

namespace minipar_rt::net {

#ifdef _WIN32
using socket_t = SOCKET;
inline constexpr socket_t kInvalidSocket = INVALID_SOCKET;
#else
using socket_t = int;
inline constexpr socket_t kInvalidSocket = -1;
#endif

inline constexpr std::uint32_t kMaxFrame = 8u * 1024u * 1024u;

inline void ensure_init() {
#ifdef _WIN32
    static const bool ok = [] {
        WSADATA wsa;
        return WSAStartup(MAKEWORD(2, 2), &wsa) == 0;
    }();
    (void)ok;
#endif
}

inline int last_error() {
#ifdef _WIN32
    return WSAGetLastError();
#else
    return errno;
#endif
}

inline std::string error_text(int code) {
#ifdef _WIN32
    return "erro de socket " + std::to_string(code);
#else
    return std::string(std::strerror(code)) + " (" + std::to_string(code) + ")";
#endif
}

class Socket {
public:
    Socket() = default;
    explicit Socket(socket_t s) : s_(s) {}
    Socket(const Socket&) = delete;
    Socket& operator=(const Socket&) = delete;
    Socket(Socket&& o) noexcept : s_(std::exchange(o.s_, kInvalidSocket)) {}
    Socket& operator=(Socket&& o) noexcept {
        if (this != &o) {
            close();
            s_ = std::exchange(o.s_, kInvalidSocket);
        }
        return *this;
    }
    ~Socket() { close(); }

    socket_t get() const { return s_; }
    bool valid() const { return s_ != kInvalidSocket; }

    // Acorda quem está bloqueado em recv/send nesse socket, sem liberar o descritor.
    void shutdown_both() {
        if (!valid()) return;
#ifdef _WIN32
        ::shutdown(s_, SD_BOTH);
#else
        ::shutdown(s_, SHUT_RDWR);
#endif
    }
    void close() {
        if (!valid()) return;
#ifdef _WIN32
        ::closesocket(s_);
#else
        ::close(s_);
#endif
        s_ = kInvalidSocket;
    }

private:
    socket_t s_ = kInvalidSocket;
};

inline bool set_nonblocking(socket_t s, bool on) {
#ifdef _WIN32
    u_long mode = on ? 1 : 0;
    return ioctlsocket(s, FIONBIO, &mode) == 0;
#else
    int flags = fcntl(s, F_GETFL, 0);
    if (flags < 0) return false;
    return fcntl(s, F_SETFL, on ? (flags | O_NONBLOCK) : (flags & ~O_NONBLOCK)) == 0;
#endif
}

// 0 = sem limite.
inline void set_recv_timeout(socket_t s, int ms) {
#ifdef _WIN32
    DWORD v = static_cast<DWORD>(ms < 0 ? 0 : ms);
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&v), sizeof v);
#else
    timeval tv{};
    tv.tv_sec = ms / 1000;
    tv.tv_usec = (ms % 1000) * 1000;
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
#endif
}

// Limite para um send sem progresso (buffer cheio porque o outro lado parou de ler). 0 = sem limite.
// Estourado, o send falha e quem envia deve fechar a conexão: o estado do socket fica indefinido.
inline void set_send_timeout(socket_t s, int ms) {
#ifdef _WIN32
    DWORD v = static_cast<DWORD>(ms < 0 ? 0 : ms);
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, reinterpret_cast<const char*>(&v), sizeof v);
#else
    timeval tv{};
    tv.tv_sec = ms / 1000;
    tv.tv_usec = (ms % 1000) * 1000;
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
#endif
}

inline void set_nodelay(socket_t s) {
    int one = 1;
    setsockopt(s, IPPROTO_TCP, TCP_NODELAY, reinterpret_cast<const char*>(&one), sizeof one);
}

// Conecta com limite de tempo. Em falha devolve Socket inválido e preenche err.
inline Socket connect_tcp(const std::string& host, std::uint16_t port, int timeout_ms, std::string& err) {
    ensure_init();
    addrinfo hints{};
    hints.ai_family = AF_INET;  // IPv4 (C-FJ-v1: IPv6 literal não é aceito no destino)
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;
    addrinfo* res = nullptr;
    std::string port_txt = std::to_string(port);
    int rc = getaddrinfo(host.c_str(), port_txt.c_str(), &hints, &res);
    if (rc != 0 || !res) {
        err = "host nao resolvido: " + host;
        return Socket();
    }
    err = "sem endereco utilizavel";
    for (addrinfo* ai = res; ai; ai = ai->ai_next) {
        Socket s(::socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol));
        if (!s.valid()) {
            err = "socket(): " + error_text(last_error());
            continue;
        }
        set_nonblocking(s.get(), true);
        int c = ::connect(s.get(), ai->ai_addr, static_cast<int>(ai->ai_addrlen));
        bool connected = (c == 0);
        if (!connected) {
            int e = last_error();
#ifdef _WIN32
            bool in_progress = (e == WSAEWOULDBLOCK || e == WSAEINPROGRESS);
#else
            bool in_progress = (e == EINPROGRESS);
#endif
            if (!in_progress) {
                err = "connect(): " + error_text(e);
                continue;
            }
            fd_set wfds, efds;
            FD_ZERO(&wfds);
            FD_ZERO(&efds);
            FD_SET(s.get(), &wfds);
            FD_SET(s.get(), &efds);
            timeval tv{};
            tv.tv_sec = timeout_ms / 1000;
            tv.tv_usec = (timeout_ms % 1000) * 1000;
            int n = ::select(static_cast<int>(s.get() + 1), nullptr, &wfds, &efds, &tv);
            if (n == 0) {
                err = "tempo de conexao esgotado (" + std::to_string(timeout_ms) + " ms)";
                continue;
            }
            int so_error = 0;
            socklen_t len = sizeof so_error;
            getsockopt(s.get(), SOL_SOCKET, SO_ERROR, reinterpret_cast<char*>(&so_error), &len);
            if (n < 0 || so_error != 0 || FD_ISSET(s.get(), &efds)) {
                err = "conexao recusada ou inalcancavel: " + error_text(so_error ? so_error : last_error());
                continue;
            }
            connected = true;
        }
        set_nonblocking(s.get(), false);
        set_nodelay(s.get());
        freeaddrinfo(res);
        err.clear();
        return s;
    }
    freeaddrinfo(res);
    return Socket();
}

// Escuta em bind_address:port (IPv4). port 0 = porta livre escolhida pelo SO (use local_port).
inline Socket listen_tcp(const std::string& bind_address, std::uint16_t port, std::string& err) {
    ensure_init();
    Socket s(::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP));
    if (!s.valid()) {
        err = "socket(): " + error_text(last_error());
        return Socket();
    }
    int one = 1;
#ifdef _WIN32
    setsockopt(s.get(), SOL_SOCKET, SO_EXCLUSIVEADDRUSE, reinterpret_cast<const char*>(&one), sizeof one);
#else
    setsockopt(s.get(), SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
#endif
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    if (inet_pton(AF_INET, bind_address.c_str(), &addr.sin_addr) != 1) {
        err = "endereco de bind invalido: " + bind_address;
        return Socket();
    }
    if (::bind(s.get(), reinterpret_cast<sockaddr*>(&addr), sizeof addr) != 0) {
        err = "bind(" + bind_address + ":" + std::to_string(port) + "): " + error_text(last_error());
        return Socket();
    }
    if (::listen(s.get(), 16) != 0) {
        err = "listen(): " + error_text(last_error());
        return Socket();
    }
    return s;
}

inline std::uint16_t local_port(socket_t s) {
    sockaddr_in addr{};
    socklen_t len = sizeof addr;
    if (getsockname(s, reinterpret_cast<sockaddr*>(&addr), &len) != 0) return 0;
    return ntohs(addr.sin_port);
}

inline Socket accept_tcp(socket_t listener, std::string& peer) {
    sockaddr_in addr{};
    socklen_t len = sizeof addr;
    Socket s(::accept(listener, reinterpret_cast<sockaddr*>(&addr), &len));
    if (s.valid()) {
        char buf[INET_ADDRSTRLEN] = {0};
        inet_ntop(AF_INET, &addr.sin_addr, buf, sizeof buf);
        peer = std::string(buf) + ":" + std::to_string(ntohs(addr.sin_port));
        set_nodelay(s.get());
    }
    return s;
}

inline bool send_all(socket_t s, const char* data, std::size_t len) {
#ifdef MSG_NOSIGNAL
    const int flags = MSG_NOSIGNAL;
#else
    const int flags = 0;
#endif
    while (len > 0) {
        int chunk = len > (1u << 30) ? (1 << 30) : static_cast<int>(len);
        int n = ::send(s, data, chunk, flags);
        if (n <= 0) return false;
        data += n;
        len -= static_cast<std::size_t>(n);
    }
    return true;
}

inline bool recv_exact(socket_t s, char* data, std::size_t len) {
    while (len > 0) {
        int chunk = len > (1u << 30) ? (1 << 30) : static_cast<int>(len);
        int n = ::recv(s, data, chunk, 0);
        if (n <= 0) return false;  // 0 = conexão fechada; <0 = erro ou timeout
        data += n;
        len -= static_cast<std::size_t>(n);
    }
    return true;
}

enum class FrameStatus { Ok, Closed, Invalid };

inline bool write_frame(socket_t s, const std::string& payload) {
    if (payload.empty() || payload.size() > kMaxFrame) return false;
    std::uint32_t n = static_cast<std::uint32_t>(payload.size());
    std::string buf;
    buf.reserve(4 + payload.size());
    buf += static_cast<char>((n >> 24) & 0xFF);
    buf += static_cast<char>((n >> 16) & 0xFF);
    buf += static_cast<char>((n >> 8) & 0xFF);
    buf += static_cast<char>(n & 0xFF);
    buf += payload;
    return send_all(s, buf.data(), buf.size());
}

inline FrameStatus read_frame(socket_t s, std::string& out, std::string& err) {
    unsigned char hdr[4];
    if (!recv_exact(s, reinterpret_cast<char*>(hdr), 4)) {
        err = "conexao encerrada";
        return FrameStatus::Closed;
    }
    std::uint32_t n = (std::uint32_t(hdr[0]) << 24) | (std::uint32_t(hdr[1]) << 16) | (std::uint32_t(hdr[2]) << 8) |
                      std::uint32_t(hdr[3]);
    if (n == 0 || n > kMaxFrame) {
        err = "tamanho de frame invalido: " + std::to_string(n) + " (permitido 1.." + std::to_string(kMaxFrame) + ")";
        return FrameStatus::Invalid;
    }
    out.assign(n, '\0');
    if (!recv_exact(s, out.data(), n)) {
        err = "conexao encerrada no meio de um frame";
        return FrameStatus::Closed;
    }
    return FrameStatus::Ok;
}

inline std::string hostname() {
    ensure_init();
    char buf[256] = {0};
    if (gethostname(buf, sizeof buf - 1) != 0) return "host-desconhecido";
    return buf;
}

}  // namespace minipar_rt::net
