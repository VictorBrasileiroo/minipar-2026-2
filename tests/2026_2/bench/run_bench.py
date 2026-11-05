"""RUN-05: benchmarks e falhas distribuidas repetiveis (Eixo C).

Usa o programa do Teste 8 (160 avaliacoes em 4 trabalhadores) como carga. Os modos `seq` e
`par` fazem exatamente as mesmas 160 avaliacoes com as mesmas fatias; cada execucao e conferida
contra o oraculo Python do `run_t08.py` antes de o tempo entrar na estatistica.

Cenarios de tempo (rodadas intercaladas: seq, par_local, par_loopback[, par_rede] em cada rodada):
  seq          4 chamadas diretas, um processo, uma thread
  par_local    4 fork com destino `local` (threads do mesmo processo)
  par_loopback 4 fork para 4 workers (processos) em 127.0.0.1 nesta maquina
  par_rede     4 fork para workers ja iniciados em outro computador (--destinos-rede)

Falhas repetiveis (cada uma --reps-falhas vezes):
  F1 worker indisponivel      destinos sem ninguem escutando -> WORKER_UNAVAILABLE, exit 1
  F2 worker morto na tarefa   mata o worker 0 depois do TASK  -> WORKER_LOST, exit 1, sem travar
  F3 worker silencioso        aceita HELLO e TASK e nunca responde -> TIMEOUT do join, exit 1

Uso (da raiz do repositorio):
    python tests/2026_2/bench/run_bench.py                    # carga 2000000, 5 rodadas
    python tests/2026_2/bench/run_bench.py --rapido           # smoke: carga 200000, 2 rodadas
    python tests/2026_2/bench/run_bench.py --destinos-rede 192.168.0.20:7501,...  (4 destinos)

Saida: PASS/FAIL/BLOCKED/INFO por verificacao, `output/bench/<data>/bench.json` e `resumo.md`.
Codigo de saida: 0 = tudo PASS; 1 = algum FAIL; 2 = algum BLOCKED.
Portas: port-base+1..port-base+13 em 127.0.0.1 (padrao 7501..7513).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import ipaddress
import json
import os
import platform
import socket
import statistics
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
T08_RUNNER = HERE.parent / "test08" / "run_t08.py"
OUTPUT_NAME = "bench_t08"
OUT_BASE = ROOT / "output" / "bench"
WORKERS = 4


def carregar_t08():
    """Importa o run_t08.py (oraculo, parser, compilacao e Worker) e aponta para um executavel proprio."""
    spec = importlib.util.spec_from_file_location("run_t08", T08_RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUTPUT_NAME = OUTPUT_NAME
    mod.EXE = ROOT / "output" / f"{OUTPUT_NAME}.exe"
    mod.CPP = ROOT / "output" / f"{OUTPUT_NAME}.cpp"
    return mod


t08 = carregar_t08()

CHECKS: list[dict] = []


def check(nome: str, status: str, detalhe: str = "") -> bool:
    CHECKS.append({"nome": nome, "status": status, "detalhe": detalhe})
    print(f"[{status}] {nome}" + (f": {detalhe}" if detalhe else ""), flush=True)
    return status == "PASS"


def ok_fail(nome: str, cond: bool, detalhe: str = "") -> bool:
    return check(nome, "PASS" if cond else "FAIL", detalhe)


# ---------------------------------------------------------------------------
# Ambiente: nucleos fisicos != threads logicas != workers
# ---------------------------------------------------------------------------
def cmd_saida(cmd: list[str], timeout: float = 30) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
        return (p.stdout or p.stderr).strip()
    except Exception as exc:  # informativo
        return f"indisponivel: {exc}"


def info_cpu() -> dict:
    info = {"modelo": None, "nucleos_fisicos": None, "threads_logicas": os.cpu_count()}
    if sys.platform == "win32":
        txt = cmd_saida(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,"
                         "NumberOfLogicalProcessors | ConvertTo-Json -Compress"])
        try:
            dados = json.loads(txt)
            dados = dados if isinstance(dados, list) else [dados]
            info["modelo"] = " / ".join(d["Name"].strip() for d in dados)
            info["nucleos_fisicos"] = sum(int(d["NumberOfCores"]) for d in dados)
            info["threads_logicas"] = sum(int(d["NumberOfLogicalProcessors"]) for d in dados)
        except Exception:
            info["erro"] = txt[:200]
        energia = cmd_saida(["powercfg", "/getactivescheme"])
        info["plano_energia"] = energia.split("(")[-1].rstrip(")") if "(" in energia else energia
    else:
        txt = cmd_saida(["lscpu"])
        campos = {k.strip(): v.strip() for k, v in
                  (ln.split(":", 1) for ln in txt.splitlines() if ":" in ln)}
        info["modelo"] = campos.get("Model name")
        try:
            info["nucleos_fisicos"] = int(campos["Core(s) per socket"]) * int(campos["Socket(s)"])
        except (KeyError, ValueError):
            pass
    return info


def sanitizar(texto: str, em_json: bool = False) -> str:
    """Tira da evidencia o caminho do repositorio (traz o usuario) e o hostname (aparece no worker_id)."""
    trocas = [(str(ROOT), "<repo>"), (socket.gethostname(), "<host>")]
    for original, troca in trocas:
        if original:
            texto = texto.replace(json.dumps(original)[1:-1] if em_json else original, troca)
    return texto


def mascarar(destino: str) -> str:
    """192.168.0.20:7501 -> 192.168.x.20:7501; loopback e `local` ficam como estao."""
    if destino == "local":
        return destino
    host, _, porta = destino.rpartition(":")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return f"<host>:{porta}"
    if ip.is_loopback:
        return destino
    o = host.split(".")
    return f"{o[0]}.{o[1]}.x.{o[3]}:{porta}"


# ---------------------------------------------------------------------------
# Tempos: so entram execucoes conferidas contra o oraculo
# ---------------------------------------------------------------------------
def conferir(run: dict, modo: str, oraculo: dict) -> tuple[bool, str]:
    """Saida igual ao oraculo: exit 0, MODO certo, 160 ids unicos e notas/soma corretas."""
    if run["exit"] != 0:
        return False, f"exit={run['exit']} stderr={run['stderr'][-200:]!r}"
    p = t08.parse_output(run["stdout"])
    ag = p["agregado"]
    ids = sorted(it["id"] for it in p["itens"])
    erradas = [it["id"] for it in p["itens"]
               if 0 <= it["id"] < t08.TOTAL and it["nota"] != oraculo["notas"][it["id"]]]
    ok = (p["modo"] == modo and ids == list(range(t08.TOTAL)) and not erradas
          and ag.get("TOTAL") == t08.TOTAL and ag.get("UNICOS") == t08.TOTAL
          and ag.get("DUPLICADOS") == 0 and ag.get("PERDIDOS") == 0
          and ag.get("SOMA_NOTAS") == oraculo["soma"])
    return ok, f"modo={p['modo']} itens={len(ids)} notas_erradas={len(erradas)} agregado={ag}"


def estatistica(valores: list[float]) -> dict:
    if not valores:
        return {"n": 0}
    return {"n": len(valores), "mediana": round(statistics.median(valores), 3),
            "media": round(statistics.mean(valores), 3),
            "desvio": round(statistics.stdev(valores), 3) if len(valores) > 1 else 0.0,
            "min": round(min(valores), 3), "max": round(max(valores), 3)}


def iniciar_workers(portas: list[int]) -> list | None:
    workers = [t08.Worker(p) for p in portas]
    if not all(w.ready.wait(15) for w in workers):
        for w in workers:
            w.stop()
        return None
    return workers


def portas_livres(portas: list[int]) -> bool:
    return all(t08.port_free(p) for p in portas)


def medir(args, oraculo: dict, report: dict) -> None:
    portas = [args.port_base + 1 + k for k in range(WORKERS)]
    cenarios = {"seq": ("seq", ["local"] * WORKERS), "par_local": ("par", ["local"] * WORKERS)}
    workers = None
    if not portas_livres(portas):
        check("par_loopback: portas livres", "BLOCKED", f"portas {portas} ocupadas; use --port-base")
    else:
        workers = iniciar_workers(portas)
        if workers is None:
            check("par_loopback: 4 workers escutando", "BLOCKED", "worker nao ficou pronto em 15 s")
        else:
            cenarios["par_loopback"] = ("par", [f"127.0.0.1:{p}" for p in portas])
    if args.destinos_rede:
        cenarios["par_rede"] = ("par", args.destinos_rede)

    tempos = {nome: [] for nome in cenarios}
    execucoes = {nome: [] for nome in cenarios}
    try:
        # Aquecimento (descartado): carrega o executavel e abre as conexoes uma vez.
        for modo, destinos in cenarios.values():
            t08.run_program(modo, args.carga, destinos, args.timeout)
        for rodada in range(1, args.reps + 1):
            for nome, (modo, destinos) in cenarios.items():
                run = t08.run_program(modo, args.carga, destinos, args.timeout)
                ok, det = conferir(run, modo, oraculo)
                execucoes[nome].append({"rodada": rodada, "ok": ok, "wall_s": run["wall_seconds"],
                                        "exit": run["exit"], "detalhe": det,
                                        "stderr": run["stderr"][-300:]})
                if ok:
                    tempos[nome].append(run["wall_seconds"])
                print(f"  rodada {rodada} {nome:<12} {run['wall_seconds']:7.3f} s  {'ok' if ok else 'ERRO'}",
                      flush=True)
    finally:
        if workers:
            for w in workers:
                w.stop()

    for nome in cenarios:
        erradas = [e for e in execucoes[nome] if not e["ok"]]
        ok_fail(f"{nome}: {args.reps} rodadas iguais ao oraculo (160 ids, notas e SOMA_NOTAS)",
                not erradas, "; ".join(e["detalhe"] for e in erradas[:2]))
    if workers:
        tasks = [len(w.events("TASK")) for w in workers]
        esperado = args.reps + 1
        ok_fail("par_loopback: cada worker recebeu 1 TASK por rodada (+ aquecimento)",
                tasks == [esperado] * WORKERS, f"TASK por worker={tasks} esperado={esperado}")

    stats = {nome: estatistica(v) for nome, v in tempos.items()}
    base = stats["seq"].get("mediana")
    comparacao = {}
    for nome, st in stats.items():
        if nome == "seq" or not base or not st.get("mediana"):
            continue
        tpar = st["mediana"]
        comparacao[nome] = {"speedup": round(base / tpar, 2),
                            "reducao_pct": round(100 * (base - tpar) / base, 1)}
    report["cenarios"] = {nome: {"modo": m, "destinos": [mascarar(d) for d in ds]}
                          for nome, (m, ds) in cenarios.items()}
    report["execucoes"] = execucoes
    report["tempos_s"] = stats
    report["comparacao_com_seq"] = comparacao
    check("tempos (mediana) e speedup = Tseq/Tpar", "INFO", json.dumps(comparacao))


# ---------------------------------------------------------------------------
# Falhas
# ---------------------------------------------------------------------------
def iniciar_coordenador(destinos: list[str], carga: int, env: dict | None = None):
    stdin = "\n".join(["par", str(carga), *destinos]) + "\n"
    p = subprocess.Popen([str(t08.EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, cwd=ROOT, env=env)
    saida: dict = {}

    def comunicar():
        out, err = p.communicate(stdin.encode())
        saida["stdout"] = out.decode("utf-8", "replace")
        saida["stderr"] = err.decode("utf-8", "replace")

    th = threading.Thread(target=comunicar, daemon=True)
    th.start()
    return p, th, saida


def esperar(p, th, limite: float) -> tuple[int | None, bool]:
    """Espera o coordenador ate `limite` s. Se passar, mata (so este processo) e marca travado."""
    th.join(limite)
    if th.is_alive():
        p.kill()
        th.join(10)
        return None, True
    return p.returncode, False


def falha_indisponivel(args, portas: list[int]) -> dict:
    t0 = time.monotonic()
    p, th, saida = iniciar_coordenador([f"127.0.0.1:{q}" for q in portas], args.carga)
    rc, travou = esperar(p, th, 30)
    dur = time.monotonic() - t0
    err = saida.get("stderr", "")
    ok = not travou and rc == 1 and "WORKER_UNAVAILABLE" in err
    return {"ok": ok, "exit": rc, "travou": travou, "duracao_s": round(dur, 3), "stderr": err[-300:]}


def falha_worker_morto(args, portas: list[int]) -> dict:
    workers = iniciar_workers(portas)
    if workers is None:
        return {"ok": False, "bloqueado": True, "detalhe": "workers nao ficaram prontos"}
    carga = max(args.carga, 2_000_000) * 3  # tarefa longa o bastante para o kill cair no meio
    saida: dict = {}
    try:
        p, th, saida = iniciar_coordenador([f"127.0.0.1:{q}" for q in portas], carga)
        limite = time.monotonic() + 15
        while time.monotonic() < limite and not workers[0].events("TASK"):
            time.sleep(0.02)
        if not workers[0].events("TASK"):
            p.kill()
            th.join(10)
            return {"ok": False, "detalhe": "worker 0 nao recebeu TASK em 15 s"}
        time.sleep(0.2)
        ja_terminou = bool(workers[0].events("RESULT"))
        t_kill = time.monotonic()
        workers[0].proc.kill()  # so o processo criado por este script
        rc, travou = esperar(p, th, 60)
        dur = time.monotonic() - t_kill
    finally:
        for w in workers:
            w.stop()
    if ja_terminou:
        return {"ok": False, "detalhe": "a tarefa terminou antes do kill (inconclusivo); aumente --carga"}
    err = saida.get("stderr", "")
    ok = not travou and rc == 1 and "WORKER_LOST" in err
    return {"ok": ok, "exit": rc, "travou": travou, "s_ate_sair_apos_kill": round(dur, 3), "stderr": err[-300:]}


class WorkerSilencioso:
    """Servidor falso: responde HELLO_OK (C-FJ-v1 §2.6) e depois le os TASK sem nunca responder."""

    def __init__(self, porta: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", porta))
        self.sock.listen(4)
        self.tasks = 0
        self.conns: list[socket.socket] = []
        threading.Thread(target=self._aceitar, daemon=True).start()

    @staticmethod
    def _ler_exato(c: socket.socket, n: int) -> bytes | None:
        buf = b""
        while len(buf) < n:
            parte = c.recv(n - len(buf))
            if not parte:
                return None
            buf += parte
        return buf

    def _ler(self, c: socket.socket) -> dict | None:
        cab = self._ler_exato(c, 4)
        if cab is None:
            return None
        corpo = self._ler_exato(c, struct.unpack(">I", cab)[0])
        return None if corpo is None else json.loads(corpo)

    def _aceitar(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            self.conns.append(c)
            threading.Thread(target=self._atender, args=(c,), daemon=True).start()

    def _atender(self, c: socket.socket):
        try:
            hello = self._ler(c)
            if not hello or hello.get("type") != "HELLO":
                return
            resp = json.dumps({"type": "HELLO_OK", "protocol_version": hello.get("protocol_version"),
                               "worker_id": "silencioso:0", "host": "silencioso", "pid": 0,
                               "build_id": hello.get("build_id")}).encode()
            c.sendall(struct.pack(">I", len(resp)) + resp)
            while (msg := self._ler(c)) is not None:
                if msg.get("type") == "TASK":
                    self.tasks += 1
        except (OSError, ValueError):
            return

    def fechar(self):
        self.sock.close()
        for c in self.conns:
            try:
                c.close()
            except OSError:
                pass


def falha_silencioso(args, porta: int, timeout_ms: int) -> dict:
    srv = WorkerSilencioso(porta)
    env = dict(os.environ, MINIPAR_RT_REMOTE_TIMEOUT_MS=str(timeout_ms))
    try:
        t0 = time.monotonic()
        p, th, saida = iniciar_coordenador([f"127.0.0.1:{porta}"] * WORKERS, args.carga, env)
        rc, travou = esperar(p, th, timeout_ms / 1000 + 30)
        dur = time.monotonic() - t0
    finally:
        srv.fechar()
    err = saida.get("stderr", "")
    ok = (not travou and rc == 1 and "TIMEOUT" in err and srv.tasks == WORKERS
          and dur >= timeout_ms / 1000)
    return {"ok": ok, "exit": rc, "travou": travou, "duracao_s": round(dur, 3),
            "tasks_recebidas": srv.tasks, "stderr": err[-300:]}


def falhas(args, report: dict) -> None:
    portas_f1 = [args.port_base + 5 + k for k in range(WORKERS)]
    portas_f2 = [args.port_base + 9 + k for k in range(WORKERS)]
    porta_f3 = args.port_base + 13
    if not portas_livres(portas_f1 + portas_f2 + [porta_f3]):
        check("falhas: portas livres", "BLOCKED", "portas de falha ocupadas; use --port-base")
        return
    timeout_ms = 3000
    res = {"F1_indisponivel": [], "F2_worker_morto": [], "F3_silencioso": []}
    for i in range(args.reps_falhas):
        res["F1_indisponivel"].append(falha_indisponivel(args, portas_f1))
        res["F2_worker_morto"].append(falha_worker_morto(args, portas_f2))
        res["F3_silencioso"].append(falha_silencioso(args, porta_f3, timeout_ms))
        print(f"  falhas rodada {i + 1}: " + " ".join(f"{k}={'ok' if v[-1]['ok'] else 'ERRO'}"
                                                     for k, v in res.items()), flush=True)
    descr = {"F1_indisponivel": "destino sem worker -> WORKER_UNAVAILABLE, exit 1, < 30 s",
             "F2_worker_morto": "worker 0 morto depois do TASK -> WORKER_LOST, exit 1, sem travar",
             "F3_silencioso": f"worker que nunca responde -> TIMEOUT ({timeout_ms} ms), exit 1"}
    for k, lista in res.items():
        if any(r.get("bloqueado") for r in lista):
            check(f"{k}: {descr[k]}", "BLOCKED", "; ".join(r.get("detalhe", "") for r in lista))
            continue
        ruins = [r for r in lista if not r["ok"]]
        ok_fail(f"{k}: {descr[k]} ({len(lista)}x)", not ruins,
                "; ".join(str({c: r.get(c) for c in ("exit", "travou", "detalhe", "stderr")}) for r in ruins[:2]))
    report["falhas"] = res


# ---------------------------------------------------------------------------
def resumo_md(report: dict) -> str:
    amb = report["ambiente"]
    cpu = amb["cpu"]
    linhas = [f"# RUN-05 — resumo da rodada {report['inicio']}", "",
              f"- Commit: `{amb['git_head']}` · SO: {amb['plataforma']} · G++: {amb['gxx']}",
              f"- CPU: {cpu.get('modelo')} · núcleos físicos: {cpu.get('nucleos_fisicos')} · "
              f"threads lógicas: {cpu.get('threads_logicas')} · energia: {cpu.get('plano_energia', '-')}",
              f"- Flags: `{amb['flags']}` · carga: {report['carga']} · rodadas: {report['reps']} "
              f"(+1 aquecimento descartado) · SHA-256 do binário: `{report.get('exe_sha256', '-')[:16]}`", "",
              "| Cenário | Destinos | n | Mediana (s) | Mín | Máx | Desvio | Speedup | Redução |",
              "|---|---|---|---|---|---|---|---|---|"]
    for nome, st in report.get("tempos_s", {}).items():
        comp = report["comparacao_com_seq"].get(nome)
        dest = ", ".join(sorted(set(report["cenarios"][nome]["destinos"])))
        linhas.append(f"| `{nome}` | {dest} | {st.get('n')} | {st.get('mediana')} | {st.get('min')} | "
                      f"{st.get('max')} | {st.get('desvio')} | {comp['speedup'] if comp else '—'} | "
                      f"{str(comp['reducao_pct']) + ' %' if comp else '—'} |")
    linhas += ["", "| Verificação | Status | Detalhe |", "|---|---|---|"]
    for c in report["checks"]:
        linhas.append(f"| {c['nome']} | {c['status']} | {c['detalhe'][:160].replace('|', '/')} |")
    return "\n".join(linhas) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carga", type=int, default=2_000_000)
    ap.add_argument("--reps", type=int, default=5, help="rodadas medidas por cenario (padrao 5)")
    ap.add_argument("--reps-falhas", type=int, default=3, help="repeticoes de cada falha (padrao 3)")
    ap.add_argument("--port-base", type=int, default=7500)
    ap.add_argument("--timeout", type=float, default=180.0, help="timeout por execucao (s)")
    ap.add_argument("--destinos-rede", type=lambda s: [d.strip() for d in s.split(",") if d.strip()],
                    help="4 destinos IP:porta de workers ja iniciados em outro computador")
    ap.add_argument("--sem-falhas", action="store_true", help="so os tempos")
    ap.add_argument("--rapido", action="store_true", help="smoke: carga 200000, 2 rodadas, 1 repeticao de falha")
    args = ap.parse_args()
    if args.rapido:
        args.carga, args.reps, args.reps_falhas = 200_000, 2, 1
    if args.carga < 1 or args.reps < 1:
        ap.error("--carga e --reps devem ser >= 1")
    if args.destinos_rede is not None and len(args.destinos_rede) != WORKERS:
        ap.error(f"--destinos-rede precisa de {WORKERS} destinos")

    inicio = dt.datetime.now().astimezone()
    out_dir = OUT_BASE / inicio.strftime("run-%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"=== RUN-05 bench: carga={args.carga} reps={args.reps} port-base={args.port_base} ===", flush=True)

    notas = [t08.nota_oraculo(i, args.carga) for i in range(t08.TOTAL)]
    oraculo = {"soma": sum(notas), "notas": notas}
    sc_ok, sc_det = t08.self_check()
    ok_fail("oraculo do T08: forma fechada == laco ingenuo", sc_ok, sc_det)

    report = {"card": "RUN-05", "inicio": inicio.isoformat(timespec="seconds"), "carga": args.carga,
              "reps": args.reps, "reps_falhas": args.reps_falhas, "workers": WORKERS,
              "ambiente": {"python": sys.version.split()[0], "plataforma": platform.platform(),
                           "cpu": info_cpu(), "gxx": t08.first_line(["g++", "--version"]),
                           "flags": "-std=c++20 -O3 -pthread -I runtime/include"
                                    + (" -lws2_32" if sys.platform == "win32" else "")
                                    + " (src/codegen.py)",
                           "git_head": t08.first_line(["git", "-C", str(ROOT), "rev-parse", "HEAD"])},
              "oraculo_soma_notas": oraculo["soma"], "checks": CHECKS}

    def fim(code: int) -> int:
        report["fim"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        report["exit_code"] = code
        (out_dir / "bench.json").write_text(
            sanitizar(json.dumps(report, indent=2, ensure_ascii=False), em_json=True), encoding="utf-8")
        (out_dir / "resumo.md").write_text(sanitizar(resumo_md(report)), encoding="utf-8")
        cont = {s: sum(1 for c in CHECKS if c["status"] == s) for s in ("PASS", "FAIL", "BLOCKED", "INFO")}
        print(f"\n=== RESUMO RUN-05: {cont} -> exit {code} ===\nEvidencias: {out_dir}")
        return code

    comp = t08.compile_program(timeout=600)
    if comp["exit"] != 0 or not t08.EXE.exists():
        ok_fail("compilacao do T08 via CLI oficial", False, f"exit={comp['exit']} {comp['stderr'][-300:]!r}")
        return fim(1)
    ok_fail("compilacao do T08 via CLI oficial", True, f"{comp['command']} ({comp['seconds']} s)")
    report["exe_sha256"] = hashlib.sha256(t08.EXE.read_bytes()).hexdigest()

    medir(args, oraculo, report)
    if not args.sem_falhas:
        falhas(args, report)

    falhou = any(c["status"] == "FAIL" for c in CHECKS)
    bloqueado = any(c["status"] == "BLOCKED" for c in CHECKS)
    return fim(1 if falhou else 2 if bloqueado else 0)


if __name__ == "__main__":
    sys.exit(main())
