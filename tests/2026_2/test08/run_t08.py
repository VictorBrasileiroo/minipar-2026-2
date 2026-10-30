"""T08-01: MiniPar T08: 160 avaliacoes em quatro trabalhadores (Eixo C).

Compila `teste8_avaliadores.minipar` pela CLI oficial (`python main.py ...`), executa
os cenarios `seq`, `par` local e `par` remoto (4 workers no loopback) e confere a saida
contra um oraculo independente calculado em Python (forma fechada do LCG).

Uso (da raiz do repositorio ou de qualquer lugar):
    python tests/2026_2/test08/run_t08.py [--carga N] [--port-base P] [--timeout S]

Saida: PASS/FAIL/BLOCKED por verificacao e `output/test08/results.json`.
Codigo de saida: 0 = tudo PASS; 1 = algum FAIL; 2 = BLOCKED (ex.: backend CORE-07 ausente).
Portas usadas: port-base+1..port-base+4 (padrao 7201..7204), somente 127.0.0.1.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "teste8_avaliadores.minipar"
OUTPUT_NAME = "teste8"
EXE = ROOT / "output" / f"{OUTPUT_NAME}.exe"
CPP = ROOT / "output" / f"{OUTPUT_NAME}.cpp"
RESULTS_DIR = ROOT / "output" / "test08"

NUM_ALUNOS = 40
ATIVIDADES_POR_ALUNO = 4
TOTAL = NUM_ALUNOS * ATIVIDADES_POR_ALUNO  # 160
AVALIADORES = ["Professor", "Monitor 1", "Monitor 2", "Monitor 3"]
FATIA = TOTAL // len(AVALIADORES)  # 40
ALLOWED_PORTS = range(7200, 7220)
AGGREGATE_KEYS = ("TOTAL", "UNICOS", "DUPLICADOS", "PERDIDOS", "SOMA_NOTAS")

# ---------------------------------------------------------------------------
# Oraculo independente (Python). Mesmo LCG do nucleo canonico MiniPar:
#   lcg(s) = (75*s + 74) mod 65537
# nota_de(id, carga): s0 = lcg(id+1); passos = carga + s0 % carga; s = lcg^passos(s0); nota = s % 101
# lcg^n(s0) = a^n*s0 + c*(a^n - 1)/(a - 1)  (mod m), m primo -> inverso modular. O(log n) por id.
# ---------------------------------------------------------------------------
A, C, M = 75, 74, 65537
INV_A_1 = pow(A - 1, -1, M)


def lcg(s: int) -> int:
    return (s * A + C) % M


def lcg_pow(s0: int, n: int) -> int:
    an = pow(A, n, M)
    return (an * s0 + C * (an - 1) * INV_A_1) % M


def nota_oraculo(i: int, carga: int) -> int:
    s0 = lcg(i + 1)
    passos = carga + s0 % carga
    return lcg_pow(s0, passos) % 101


def nota_ingenua(i: int, carga: int) -> int:
    s = lcg(i + 1)
    passos = carga + s % carga
    for _ in range(passos):
        s = lcg(s)
    return s % 101


def self_check() -> tuple[bool, str]:
    """Confere a forma fechada contra o laco ingenuo para cargas pequenas."""
    divergencias = []
    for carga in (1, 2, 3, 7, 50, 997):
        for i in range(TOTAL):
            a, b = nota_oraculo(i, carga), nota_ingenua(i, carga)
            if a != b:
                divergencias.append((carga, i, a, b))
    ok = not divergencias
    return ok, ("forma fechada == laco ingenuo para cargas 1,2,3,7,50,997 x 160 ids"
                if ok else f"divergencias: {divergencias[:5]}")


# ---------------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------------
CHECKS: list[dict] = []


def check(nome: str, status: str, detalhe: str = "") -> bool:
    CHECKS.append({"check": nome, "status": status, "detalhe": detalhe})
    print(f"[{status}] {nome}" + (f": {detalhe}" if detalhe else ""), flush=True)
    return status == "PASS"


def ok_fail(nome: str, cond: bool, detalhe: str = "") -> bool:
    return check(nome, "PASS" if cond else "FAIL", detalhe)


def first_line(cmd: list[str]) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (p.stdout or p.stderr).strip().splitlines()[0]
    except Exception as exc:  # informativo apenas
        return f"indisponivel: {exc}"


def compile_program(timeout: float) -> dict:
    cmd = [sys.executable, "main.py", str(SOURCE.relative_to(ROOT)).replace("\\", "/"), OUTPUT_NAME]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = None, str(exc.stdout or ""), f"TIMEOUT apos {timeout}s"
    return {"command": " ".join(cmd), "exit": rc, "stdout": out, "stderr": err,
            "seconds": round(time.monotonic() - t0, 3)}


def run_program(modo: str, carga: int, destinos: list[str], timeout: float) -> dict:
    stdin = "\n".join([modo, str(carga), *destinos]) + "\n"
    t0 = time.monotonic()
    try:
        p = subprocess.run([str(EXE)], input=stdin, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, cwd=ROOT)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc = None
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = f"TIMEOUT apos {timeout}s"
    wall = time.monotonic() - t0
    return {"modo": modo, "stdin": stdin, "exit": rc, "stdout": out, "stderr": err,
            "wall_seconds": round(wall, 3), "t_start": t0, "t_end": t0 + wall}


ITEM_RE = re.compile(r"^\[(.+?)\] Concluiu: Aluno (\d+) - Atividade (\d+) \(id (-?\d+), nota (-?\d+)\)$")
AVAL_RE = re.compile(r"^AVALIADOR (-?\d+) (.+) (-?\d+)$")


def parse_output(stdout: str) -> dict:
    lines = [ln.rstrip("\r") for ln in stdout.splitlines()]
    parsed = {"header": lines[0] if lines else None, "modo": None, "avaliadores": [],
              "itens": [], "agregado": {}, "linhas_nao_reconhecidas": []}
    for ln in lines[1:]:
        if ln.startswith("MODO "):
            parsed["modo"] = ln[5:]
        elif (m := AVAL_RE.match(ln)):
            parsed["avaliadores"].append({"k": int(m[1]), "nome": m[2], "qtd": int(m[3])})
        elif (m := ITEM_RE.match(ln)):
            parsed["itens"].append({"avaliador": m[1], "aluno": int(m[2]), "atividade": int(m[3]),
                                    "id": int(m[4]), "nota": int(m[5])})
        elif ln.split(" ", 1)[0] in AGGREGATE_KEYS and len(ln.split()) == 2:
            key, val = ln.split()
            parsed["agregado"][key] = int(val) if re.fullmatch(r"-?\d+", val) else val
        elif ln:
            parsed["linhas_nao_reconhecidas"].append(ln)
    return parsed


def verify_scenario(nome: str, modo: str, run: dict, carga: int, oraculo: dict) -> dict:
    p = parse_output(run["stdout"])
    run["parsed_agregado"] = p["agregado"]
    run["parsed_avaliadores"] = p["avaliadores"]
    pre = f"{nome}:"
    ok_fail(f"{pre} exit code 0", run["exit"] == 0, f"exit={run['exit']} stderr={run['stderr'][-300:]!r}")
    ok_fail(f"{pre} cabecalho e MODO",
            p["header"] == "=== TESTE 8: 160 avaliacoes, 4 avaliadores ===" and p["modo"] == modo,
            f"header={p['header']!r} modo={p['modo']!r}")
    aval_esperado = [{"k": k, "nome": AVALIADORES[k], "qtd": FATIA} for k in range(len(AVALIADORES))]
    ok_fail(f"{pre} 4 avaliadores (k = 1o elemento devolvido, 40 itens cada)",
            p["avaliadores"] == aval_esperado, f"obtido={p['avaliadores']}")
    ag = p["agregado"]
    esperado = {"TOTAL": TOTAL, "UNICOS": TOTAL, "DUPLICADOS": 0, "PERDIDOS": 0,
                "SOMA_NOTAS": oraculo["soma"]}
    ok_fail(f"{pre} TOTAL=160 UNICOS=160 DUPLICADOS=0 PERDIDOS=0",
            all(ag.get(k) == esperado[k] for k in ("TOTAL", "UNICOS", "DUPLICADOS", "PERDIDOS")),
            f"obtido={ag}")
    ok_fail(f"{pre} SOMA_NOTAS == oraculo Python",
            ag.get("SOMA_NOTAS") == oraculo["soma"], f"obtido={ag.get('SOMA_NOTAS')} oraculo={oraculo['soma']}")
    # Conferencia item a item (ids, aluno/atividade, nota e dono da fatia).
    ids = [it["id"] for it in p["itens"]]
    erros = []
    for it in p["itens"]:
        i = it["id"]
        if not 0 <= i < TOTAL:
            erros.append(f"id fora de faixa {i}")
            continue
        if it["aluno"] != i // ATIVIDADES_POR_ALUNO + 1 or it["atividade"] != i % ATIVIDADES_POR_ALUNO + 1:
            erros.append(f"id {i}: aluno/atividade {it['aluno']}/{it['atividade']}")
        if it["nota"] != oraculo["notas"][i]:
            erros.append(f"id {i}: nota {it['nota']} != {oraculo['notas'][i]}")
        if it["avaliador"] != AVALIADORES[i // FATIA]:
            erros.append(f"id {i}: avaliador {it['avaliador']}")
    ok_fail(f"{pre} 160 itens: ids 0..159 sem perda/duplicata",
            len(ids) == TOTAL and sorted(ids) == list(range(TOTAL)),
            f"linhas={len(ids)} distintos={len(set(ids))}")
    ok_fail(f"{pre} cada item: aluno/atividade/nota/avaliador == oraculo", not erros and len(ids) == TOTAL,
            "; ".join(erros[:5]))
    return p


class Worker:
    """Processo worker (mesmo executavel) com leitura do log em thread e carimbo monotonic."""

    def __init__(self, port: int):
        self.port = port
        self.lines: list[tuple[float, str]] = []
        self.ready = threading.Event()
        self.proc = subprocess.Popen(
            [str(EXE), "--minipar-worker", str(port), "--bind", "127.0.0.1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=ROOT)
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        for raw in iter(self.proc.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            self.lines.append((time.monotonic(), line))
            if "escutando em" in line:
                self.ready.set()

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
        self.thread.join(timeout=5)

    def events(self, kind: str, fn: str = "avaliar_lote"):
        pat = re.compile(rf"^\[minipar_worker (.+):(\d+)\] {kind} (task-\d+) fn={re.escape(fn)}\b(.*)$")
        out = []
        for t, ln in self.lines:
            if (m := pat.match(ln)):
                out.append({"t": t, "host": m[1], "pid": int(m[2]), "task": m[3], "resto": m[4].strip()})
        return out


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def run_remote(carga: int, port_base: int, timeout: float, oraculo: dict) -> dict | None:
    ports = [port_base + k + 1 for k in range(len(AVALIADORES))]
    if any(p not in ALLOWED_PORTS for p in ports):
        check("par remoto: portas na faixa autorizada 7200-7219", "BLOCKED", f"portas={ports}")
        return None
    ocupadas = [p for p in ports if not port_free(p)]
    if ocupadas:
        check("par remoto: portas livres", "BLOCKED", f"ocupadas={ocupadas}")
        return None
    workers = [Worker(p) for p in ports]
    try:
        prontos = all(w.ready.wait(timeout=15) for w in workers)
        if not ok_fail("par remoto: 4 workers escutando no loopback", prontos,
                       f"portas={ports} pids={[w.proc.pid for w in workers]}"):
            return {"workers": [{"port": w.port, "pid": w.proc.pid, "log": [l for _, l in w.lines]} for w in workers]}
        destinos = [f"127.0.0.1:{p}" for p in ports]
        run = run_program("par", carga, destinos, timeout)
        # RESULT e registrado apos o envio; aguarda o log chegar (ate 10 s).
        limite = time.monotonic() + 10
        while time.monotonic() < limite and not all(w.events("RESULT") for w in workers):
            time.sleep(0.05)
    finally:
        for w in workers:
            w.stop()
    parsed = verify_scenario("par remoto", "par", run, carga, oraculo)
    info = []
    for k, w in enumerate(workers):
        tasks, results = w.events("TASK"), w.events("RESULT")
        info.append({"k": k, "port": w.port, "popen_pid": w.proc.pid,
                     "log_pids": sorted({e["pid"] for e in tasks + results}),
                     "tasks": len(tasks), "results": len(results),
                     "results_ok": [r["resto"] for r in results],
                     "task_t_rel": [round(e["t"] - run["t_start"], 3) for e in tasks],
                     "result_t_rel": [round(e["t"] - run["t_start"], 3) for e in results],
                     "log": [l for _, l in w.lines]})
    for it in info:
        ok_fail(f"par remoto: worker {it['k']} (porta {it['port']}) 1 TASK + 1 RESULT ok de fn=avaliar_lote",
                it["tasks"] == 1 and it["results"] == 1 and it["results_ok"][0].startswith("ok"),
                f"TASK={it['tasks']} RESULT={it['results']} {it['results_ok']}")
    log_pids = [p for it in info for p in it["log_pids"]]
    ok_fail("par remoto: 4 PIDs distintos e iguais aos processos iniciados",
            len(log_pids) == 4 and len(set(log_pids)) == 4
            and all(it["log_pids"] == [it["popen_pid"]] for it in info),
            f"pids_log={log_pids} pids_popen={[it['popen_pid'] for it in info]}")
    # Evidencia de paralelismo real: as 4 tarefas chegaram aos workers antes do 1o RESULT.
    t_tasks = [t for it in info for t in it["task_t_rel"]]
    t_results = [t for it in info for t in it["result_t_rel"]]
    if len(t_tasks) == 4 and t_results:
        cond = max(t_tasks) < min(t_results)
        det = f"ultimo TASK em {max(t_tasks):.3f}s, primeiro RESULT em {min(t_results):.3f}s"
        if carga >= 100000:
            ok_fail("par remoto: 4 TASK recebidas antes do primeiro RESULT (fork antes de join)", cond, det)
        else:
            check("par remoto: 4 TASK antes do primeiro RESULT (informativo, carga pequena)", "INFO", det)
    return {"run": run, "parsed": parsed, "workers": info}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carga", type=int, default=2000000)
    ap.add_argument("--port-base", type=int, default=7200)
    ap.add_argument("--timeout", type=float, default=120.0, help="timeout por execucao (s)")
    args = ap.parse_args()
    if args.carga < 1:
        ap.error("--carga deve ser >= 1")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"=== T08-01 runner: carga={args.carga} port-base={args.port_base} ===", flush=True)

    sc_ok, sc_det = self_check()
    ok_fail("oraculo: autoverificacao da forma fechada", sc_ok, sc_det)
    notas = [nota_oraculo(i, args.carga) for i in range(TOTAL)]
    oraculo = {"carga": args.carga, "soma": sum(notas), "notas": notas}
    print(f"[INFO] oraculo Python: SOMA_NOTAS={oraculo['soma']}", flush=True)

    comp = compile_program(timeout=600)
    texto = comp["stdout"] + comp["stderr"]
    report = {"card": "T08-01", "inicio": started, "carga": args.carga, "port_base": args.port_base,
              "ambiente": {"python": sys.version.split()[0], "plataforma": platform.platform(),
                           "cpu_count": os.cpu_count(), "gxx": first_line(["g++", "--version"]),
                           "git_head": first_line(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
                           "git_branch": first_line(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"])},
              "compilacao": comp, "oraculo": {"soma_notas": oraculo["soma"], "notas": notas},
              "cenarios": {}, "checks": CHECKS}

    def finish(code: int) -> int:
        report["fim"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        report["exit_code"] = code
        (RESULTS_DIR / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        cont = {s: sum(1 for c in CHECKS if c["status"] == s) for s in ("PASS", "FAIL", "BLOCKED", "INFO")}
        print(f"\n=== RESUMO T08: {cont} -> exit {code} ===")
        print(f"Evidencias: {RESULTS_DIR / 'results.json'}")
        return code

    if comp["exit"] != 0 or not EXE.exists():
        if re.search(r"(?i)\bfork\b|\bjoin\b|CORE-0[67]|NotImplemented", texto):
            check("compilacao via CLI oficial", "BLOCKED", "backend CORE-07 ausente")
            print("BLOCKED: backend CORE-07 ausente")
            return finish(2)
        ok_fail("compilacao via CLI oficial", False, f"exit={comp['exit']} {texto[-500:]!r}")
        return finish(1)
    ok_fail("compilacao via CLI oficial", True, f"{comp['command']} -> {EXE.relative_to(ROOT)} ({comp['seconds']}s)")
    report["exe_sha256"] = hashlib.sha256(EXE.read_bytes()).hexdigest()
    cpp = CPP.read_text(encoding="utf-8", errors="replace") if CPP.exists() else ""
    ok_fail("C++ gerado usa o runtime minipar_rt (start/join reais)",
            "minipar_rt" in cpp and "avaliar_lote" in cpp, f"{CPP.relative_to(ROOT)}")

    seq = run_program("seq", args.carga, ["local"] * 4, args.timeout)
    report["cenarios"]["seq"] = {"run": seq, "parsed": verify_scenario("seq", "seq", seq, args.carga, oraculo)}
    if not 0.5 <= seq["wall_seconds"] <= 15:
        check("calibracao: seq entre 0.5 s e 15 s", "INFO", f"seq={seq['wall_seconds']}s; ajuste --carga")

    par = run_program("par", args.carga, ["local"] * 4, args.timeout)
    report["cenarios"]["par_local"] = {"run": par, "parsed": verify_scenario("par local", "par", par, args.carga, oraculo)}

    remoto = run_remote(args.carga, args.port_base, args.timeout, oraculo)
    if remoto is not None:
        report["cenarios"]["par_remoto"] = remoto

    agregados = {nome: [ln.rstrip("\r") for ln in c["run"]["stdout"].splitlines()
                        if ln.split(" ", 1)[0] in ("AVALIADOR",) + AGGREGATE_KEYS]
                 for nome, c in report["cenarios"].items() if "run" in c}
    report["linhas_agregadas"] = agregados
    valores = list(agregados.values())
    ok_fail("cenarios produzem linhas agregadas identicas",
            len(valores) == 3 and all(v == valores[0] and v for v in valores),
            f"cenarios={list(agregados)}")

    tempos = {n: c["run"]["wall_seconds"] for n, c in report["cenarios"].items() if "run" in c}
    report["tempos_s"] = tempos
    speedups = {}
    for n in ("par_local", "par_remoto"):
        if n in tempos and tempos[n] > 0:
            speedups[f"seq/{n}"] = round(tempos["seq"] / tempos[n], 2)
    report["speedup_informativo"] = speedups
    check("tempo de parede por cenario (informativo; speedup>1 nao e exigido)", "INFO",
          f"tempos={tempos} speedup={speedups} trabalhadores_efetivos=4")

    falhou = any(c["status"] == "FAIL" for c in CHECKS)
    bloqueado = any(c["status"] == "BLOCKED" for c in CHECKS)
    return finish(1 if falhou else 2 if bloqueado else 0)


if __name__ == "__main__":
    sys.exit(main())
