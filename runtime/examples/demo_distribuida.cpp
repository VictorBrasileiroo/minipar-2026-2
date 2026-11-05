// RUN-03 — demonstração do minipar_rt em DOIS COMPUTADORES (coordenador no host A, worker no host B).
// O mesmo binário, compilado do mesmo fonte nas duas máquinas, faz os dois papéis:
//   host B:  demo_distribuida --minipar-worker 7000 --bind <IP-de-B-na-rede-local>
//   host A:  demo_distribuida --coordenador <IP-de-B>:7000 [--sem-queda]
// O coordenador confere: (1) worker em outro host/processo, (2) duas tarefas com entradas diferentes calculadas no
// worker e conferidas contra o cálculo local, (3) comparação com execução local, (4) join devolve erro (sem travar)
// quando o worker cai no meio de uma tarefa. Rodar em loopback (127.0.0.1) prova só o roteiro, NÃO duas máquinas.
#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "minipar_rt/minipar_rt.hpp"

using namespace minipar_rt;
using Clock = std::chrono::steady_clock;

namespace {

// Soma de quadrados módulo um primo: cálculo real, determinístico e sem estouro de inteiro.
long long soma_quadrados(long long inicio, long long fim) {
    const long long p = 1000000007LL;
    long long s = 0;
    for (long long i = inicio; i < fim; ++i) {
        long long x = i % 1000003;
        s = (s + x * x) % p;
    }
    return s;
}

long long ms_since(Clock::time_point t0) {
    return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - t0).count();
}

std::vector<std::string> local_ipv4() {
    std::vector<std::string> out;
    addrinfo hints{};
    hints.ai_family = AF_INET;
    addrinfo* res = nullptr;
    if (getaddrinfo(net::hostname().c_str(), nullptr, &hints, &res) == 0) {
        for (addrinfo* ai = res; ai; ai = ai->ai_next) {
            char buf[INET_ADDRSTRLEN] = {0};
            inet_ntop(AF_INET, &reinterpret_cast<sockaddr_in*>(ai->ai_addr)->sin_addr, buf, sizeof buf);
            out.emplace_back(buf);
        }
        freeaddrinfo(res);
    }
    return out;
}

void register_demo_functions() {
    set_build_id("minipar-demo-run03-v1");
    register_function("soma_quadrados", [](const TaskArgs& a) {
        return Value(soma_quadrados(a.at(0).as_int(), a.at(1).as_int()));
    });
    register_function("identidade", [](const TaskArgs&) {
        return Value(Value::List{Value(net::hostname()), Value(static_cast<long long>(detail::current_pid()))});
    });
    // trabalho_longo(ms): cálculo de verdade até o tempo acabar (usado para derrubar o worker no meio).
    register_function("trabalho_longo", [](const TaskArgs& a) {
        auto t0 = Clock::now();
        long long voltas = 0, acc = 0;
        while (ms_since(t0) < a.at(0).as_int()) {
            acc = (acc + soma_quadrados(0, 10000)) % 1000000007LL;
            ++voltas;
        }
        return Value(Value::List{Value(voltas), Value(acc)});
    });
}

struct Check {
    std::string nome;
    bool ok;
    std::string detalhe;
};

int coordenador(const std::string& destino_txt, bool com_queda) {
    std::vector<Check> checks;
    Destination dest = Destination::parse(destino_txt);
    std::string ips;
    for (const auto& ip : local_ipv4()) ips += (ips.empty() ? "" : ", ") + ip;
    std::printf("[coordenador] host=%s pid=%ld IPv4 locais=[%s] build_id=%s\n", net::hostname().c_str(),
                detail::current_pid(), ips.c_str(), build_id().c_str());
    std::printf("[coordenador] destino=%s\n", destino_txt.c_str());
    if (dest.kind != Destination::Kind::Remote) {
        std::printf("destino precisa ser host:porta\n");
        return 2;
    }

    // 1) Quem é o worker.
    TaskResult who = join(start("identidade", {}, dest), 10000);
    if (!who.ok) {
        std::printf("[coordenador] worker inacessivel: %s: %s\n", to_string(who.error.code), who.error.message.c_str());
        return 1;
    }
    std::string w_host = who.value.as_list().at(0).as_string();
    long long w_pid = who.value.as_list().at(1).as_int();
    bool outro_host = w_host != net::hostname();
    std::printf("[coordenador] worker respondeu: host=%s pid=%lld executed_by=%s\n", w_host.c_str(), w_pid,
                who.executed_by.c_str());
    checks.push_back({"worker em outro computador (hostname diferente)", outro_host,
                      outro_host ? w_host + " != " + net::hostname()
                                 : "MESMO HOST " + w_host + ": isto NAO prova duas maquinas"});

    // 2) Duas tarefas remotas com entradas diferentes, conferidas contra o cálculo local.
    const long long N = 40000000;
    auto t_remoto = Clock::now();
    TaskHandle h1 = start("soma_quadrados", {0, N}, dest);
    TaskHandle h2 = start("soma_quadrados", {N, 2 * N}, dest);
    TaskResult r1 = join(h1, 120000), r2 = join(h2, 120000);
    long long ms_remoto = ms_since(t_remoto);
    long long e1 = soma_quadrados(0, N), e2 = soma_quadrados(N, 2 * N);
    bool ok_calc = r1.ok && r2.ok && r1.value.as_int() == e1 && r2.value.as_int() == e2 && e1 != e2;
    std::printf("[coordenador] %s soma_quadrados(0,%lld) = %s (esperado %lld) por %s\n", h1.task_id.c_str(), N,
                r1.ok ? r1.value.to_display().c_str() : to_string(r1.error.code), e1, r1.executed_by.c_str());
    std::printf("[coordenador] %s soma_quadrados(%lld,%lld) = %s (esperado %lld) por %s\n", h2.task_id.c_str(), N, 2 * N,
                r2.ok ? r2.value.to_display().c_str() : to_string(r2.error.code), e2, r2.executed_by.c_str());
    checks.push_back({"duas tarefas remotas com resultados corretos e IDs certos", ok_calc,
                      "remoto " + std::to_string(ms_remoto) + " ms"});
    checks.push_back({"tarefas executadas pelo processo do worker",
                      r1.executed_by == who.executed_by && r2.executed_by == who.executed_by, r1.executed_by});

    // 3) Mesmo trabalho com destino local, para comparação (doc 05 §4, passo 8).
    auto t_local = Clock::now();
    TaskHandle hl1 = start("soma_quadrados", {0, N});  // mesma concorrência do caso remoto: dispara as duas
    TaskHandle hl2 = start("soma_quadrados", {N, 2 * N});
    TaskResult l1 = join(hl1), l2 = join(hl2);
    long long ms_local = ms_since(t_local);
    bool ok_local = l1.ok && l2.ok && l1.value.as_int() == e1 && l2.value.as_int() == e2;
    std::printf("[coordenador] mesmo trabalho local: %lld ms (remoto %lld ms, inclui rede)\n", ms_local, ms_remoto);
    checks.push_back({"execucao local equivalente confere", ok_local, std::to_string(ms_local) + " ms"});

    // 4) Queda do worker durante uma tarefa.
    if (com_queda) {
        TaskHandle longa = start("trabalho_longo", {60000}, dest);
        std::printf("AGUARDANDO_QUEDA: encerre AGORA o worker no outro computador (Ctrl+C na janela dele). "
                    "Tarefa %s pendente; join com limite de 90 s.\n",
                    longa.task_id.c_str());
        std::fflush(stdout);
        auto t_q = Clock::now();
        TaskResult q = join(longa, 90000);
        long long ms_q = ms_since(t_q);
        std::printf("[coordenador] join(%s) apos a queda: %s: %s (em %lld ms)\n", longa.task_id.c_str(),
                    q.ok ? "OK" : to_string(q.error.code), q.ok ? "" : q.error.message.c_str(), ms_q);
        checks.push_back({"queda do worker vira erro no join, sem bloqueio infinito",
                          !q.ok && (q.error.code == ErrorCode::WORKER_LOST || q.error.code == ErrorCode::TIMEOUT),
                          q.ok ? "a tarefa terminou: o worker nao foi encerrado" : to_string(q.error.code)});
    }

    std::printf("\n== Resumo RUN-03 ==\n");
    bool all = true;
    for (const auto& c : checks) {
        std::printf("[%s] %s — %s\n", c.ok ? "PASS" : "FAIL", c.nome.c_str(), c.detalhe.c_str());
        all = all && c.ok;
    }
    std::fflush(stdout);
    return all ? 0 : 1;
}

}  // namespace

int main(int argc, char** argv) {
    register_demo_functions();
    int rc = worker_main_if_requested(argc, argv);
    if (rc >= 0) return rc;
    std::string destino;
    bool com_queda = true;
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--coordenador") == 0 && i + 1 < argc) destino = argv[++i];
        else if (std::strcmp(argv[i], "--sem-queda") == 0) com_queda = false;
    }
    if (destino.empty()) {
        std::fprintf(stderr,
                     "uso:\n  %s --minipar-worker <porta> [--bind <ip>]\n  %s --coordenador <host:porta> [--sem-queda]\n",
                     argv[0], argv[0]);
        return 2;
    }
    rc = coordenador(destino, com_queda);
    std::fflush(stdout);
    std::_Exit(rc);  // há threads de conexão bloqueadas; encerra sem esperar por elas
}
