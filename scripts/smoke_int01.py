"""INT-01 — smoke de integração dos três eixos (Eixo C).

Três segmentos independentes, cada um com status próprio
(PASS / FAIL / BLOCKED / PARTIAL / UNTESTED, convenções de AGENTS.md):

  A  Eixos A+C: programa MiniPar com Fork/Join -> CLI (`main.py`: Lexer, Parser,
     Semântico, TAC, C++, g++) -> execução com destino "local" e com um worker
     no loopback (o mesmo .exe em modo `--minipar-worker`).
  B  Eixos A+B: serviço de fases C-WEB-v1 (`src/service.py`, CORE-08/PR #19),
     executado em OUTRA árvore (`--core08-root`), em subprocesso isolado.
  C  Eixo B: Web didática (WEB-03). Só inspeção estática do código; não sobe
     servidor nem abre porta.

Os oráculos são calculados aqui, em Python, a partir dos mesmos parâmetros
usados para gerar os fontes MiniPar; nenhuma saída esperada é fixada à mão.

Resultados: `output/int01/results.json` (output/ é ignorado pelo Git).

Código de saída: 0 quando nenhuma verificação executada falhou (todo segmento
não BLOCKED é PASS, ou PARTIAL formado só por PASS + BLOCKED/UNTESTED);
1 quando houve FAIL; 2 para argumentos inválidos. Segmentos BLOCKED/PARTIAL
significam que o card INT-01 NÃO está concluído, mesmo com exit 0.

Limitação permanente: o worker roda em 127.0.0.1. Loopback prova o protocolo
e a integração compilador+runtime, NÃO a execução entre dois computadores
(RUN-03, PR #10).

Uso (na raiz do repositório):
    python scripts/smoke_int01.py
    python scripts/smoke_int01.py --only A --port-base 7500 --timeout 30
    python scripts/smoke_int01.py --only B --core08-root ../int01-core08
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "int01"
PORT_MIN, PORT_MAX = 7500, 7519          # faixa reservada a este smoke
COMPILE_TIMEOUT = 300                     # g++ -O3 pode levar ~1 min
PHASES = ("lexer", "parser", "semantic", "tac", "cpp", "gpp")
EXEC_KEYS = {"contract", "artifact_id", "ok", "exit_code", "timed_out", "duration_ms", "stdout",
             "stderr", "stdout_truncated", "stderr_truncated", "error"}

# Parâmetros dos programas de prova. O oráculo é derivado deles em Python.
N_SOMA = 100
N_FIB = 30
NOME_STDIN = "int01"


# --------------------------------------------------------------------------- oráculos
def oraculo_soma_quadrados(n: int) -> int:
    return sum(i * i for i in range(n))


def oraculo_fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


FUNCOES_MINIPAR = f"""func soma_quadrados(n) {{
    var s = 0;
    var i = 0;
    while (i < n) {{
        s = s + i * i;
        i = i + 1;
    }}
    return s;
}}
func fib(n) {{
    var a = 0;
    var b = 1;
    var k = 0;
    while (k < n) {{
        var t = a + b;
        a = b;
        b = t;
        k = k + 1;
    }}
    return a;
}}
"""


def fonte_fork() -> str:
    """Duas tarefas; o destino vem do stdin ("local" ou "127.0.0.1:porta")."""
    return FUNCOES_MINIPAR + f"""var destino = input();
var h1 = fork soma_quadrados({N_SOMA}) on destino;
var h2 = fork fib({N_FIB}) on destino;
print(join(h2));
print(join(h1));
"""


def oraculo_fork() -> str:
    # join(h2) é impresso antes de join(h1).
    return f"{oraculo_fib(N_FIB)}\n{oraculo_soma_quadrados(N_SOMA)}\n"


def fonte_sem_fork() -> str:
    return FUNCOES_MINIPAR + f"""var nome = input();
print("ola " + nome);
print(soma_quadrados({N_SOMA}));
print(fib({N_FIB}));
"""


def oraculo_sem_fork(nome: str) -> str:
    return f"ola {nome}\n{oraculo_soma_quadrados(N_SOMA)}\n{oraculo_fib(N_FIB)}\n"


# --------------------------------------------------------------------------- utilidades
def _txt(data) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    return data.replace("\r\n", "\n")


def _tail(text: str, n: int = 1500) -> str:
    return text if len(text) <= n else "…" + text[-n:]


def run(cmd, *, cwd=ROOT, stdin_text=None, timeout=30, env=None) -> dict:
    t0 = time.monotonic()
    try:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd), input=(stdin_text or "").encode("utf-8"),
                           capture_output=True, timeout=timeout, env=env)
        out = dict(exit=p.returncode, stdout=_txt(p.stdout), stderr=_txt(p.stderr), timed_out=False)
    except subprocess.TimeoutExpired as exc:
        out = dict(exit=None, stdout=_txt(exc.stdout), stderr=_txt(exc.stderr), timed_out=True)
    except OSError as exc:
        out = dict(exit=None, stdout="", stderr=f"{type(exc).__name__}: {exc}", timed_out=False)
    out["cmd"] = [str(c) for c in cmd]
    out["duration_ms"] = round((time.monotonic() - t0) * 1000)
    return out


def git_head(path: Path) -> str | None:
    r = run(["git", "-C", path, "rev-parse", "HEAD"], timeout=15)
    return r["stdout"].strip() if r["exit"] == 0 else None


def tool_version(cmd) -> str | None:
    r = run(cmd, timeout=15)
    return (r["stdout"] or r["stderr"]).splitlines()[0].strip() if r["exit"] == 0 else None


def free_ports(base: int, count: int) -> list[int]:
    """Portas livres em 127.0.0.1 dentro de [base, PORT_MAX]."""
    found = []
    for port in range(base, PORT_MAX + 1):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            found.append(port)
        except OSError:
            pass
        finally:
            s.close()
        if len(found) == count:
            break
    return found


class Segment:
    def __init__(self, sid: str, title: str, eixos: str):
        self.sid, self.title, self.eixos = sid, title, eixos
        self.checks: list[dict] = []
        self.notes: list[str] = []
        self.blocked_reason: str | None = None
        self.data: dict = {}

    def check(self, cid: str, desc: str, status: str, evidence=None):
        self.checks.append(dict(id=cid, desc=desc, status=status, evidence=evidence))
        print(f"  [{status:8}] {cid} {desc}")
        return status == "PASS"

    def ok(self, cid, desc, cond: bool, evidence=None):
        return self.check(cid, desc, "PASS" if cond else "FAIL", evidence)

    def block(self, reason: str):
        self.blocked_reason = reason
        print(f"  [BLOCKED ] {reason}")

    @property
    def status(self) -> str:
        st = [c["status"] for c in self.checks]
        if "FAIL" in st:
            return "FAIL"
        if not st:
            return "BLOCKED" if self.blocked_reason else "UNTESTED"
        if all(s == "PASS" for s in st):
            return "BLOCKED" if self.blocked_reason else "PASS"
        if all(s == "BLOCKED" for s in st):
            return "BLOCKED"
        if "PASS" in st:
            return "PARTIAL"
        return "BLOCKED" if "BLOCKED" in st else "UNTESTED"

    def as_dict(self) -> dict:
        return dict(id=self.sid, title=self.title, eixos=self.eixos, status=self.status,
                    blocked_reason=self.blocked_reason, notes=self.notes, checks=self.checks, data=self.data)


# --------------------------------------------------------------------------- segmento A
FORK_RE = re.compile(r"^\s*\S+\s*=\s*fork\s+(\w+)\((.*)\)\s+on\s+\S+\s*$", re.M)
JOIN_RE = re.compile(r"^\s*(?:\S+\s*=\s*)?join\s+\S+", re.M)


def _wait_log(path: Path, pattern: re.Pattern, minimum: int, proc, deadline_s: float) -> list[str]:
    end = time.monotonic() + deadline_s
    while True:
        text = _txt(path.read_bytes()) if path.exists() else ""
        hits = pattern.findall(text)
        if len(hits) >= minimum or time.monotonic() > end or (proc is not None and proc.poll() is not None):
            return hits
        time.sleep(0.1)


def segment_a(args) -> Segment:
    seg = Segment("A", "CLI Fork/Join + runtime (local e worker no loopback)", "A+C")
    seg.notes.append("Worker em 127.0.0.1: prova protocolo/integração no mesmo host, NÃO dois computadores (RUN-03 #10).")
    OUT.mkdir(parents=True, exist_ok=True)
    src = OUT / "segA_fork.minipar"
    src.write_text(fonte_fork(), encoding="utf-8", newline="\n")
    name = "int01_segA"
    tac, cpp, exe = (ROOT / "output" / f"{name}.{ext}" for ext in ("tac", "cpp", "exe"))
    oracle = oraculo_fork()
    seg.data.update(source=str(src.relative_to(ROOT)), oracle=oracle,
                    oracle_def=f"fib({N_FIB}), soma_quadrados({N_SOMA}) calculados em Python")

    comp = run([sys.executable, "-B", "main.py", src.relative_to(ROOT), name], timeout=COMPILE_TIMEOUT)
    (OUT / "segA_compile.log").write_text(f"$ {' '.join(comp['cmd'])}\nexit={comp['exit']}\n--- stdout\n{comp['stdout']}--- stderr\n{comp['stderr']}", encoding="utf-8")
    seg.data["compile"] = dict(cmd=comp["cmd"], exit=comp["exit"], duration_ms=comp["duration_ms"],
                               stdout=_tail(comp["stdout"]), stderr=_tail(comp["stderr"]))
    if comp["exit"] != 0:
        blob = comp["stdout"] + comp["stderr"]
        if re.search(r"ERRO TAC|Fork/Join requer|CORE-06|CORE-07|NotImplementedError", blob):
            seg.check("A1", "CLI compila programa Fork/Join", "BLOCKED", _tail(blob, 600))
            seg.block("Backend/TAC sem Fork/Join nesta base (CORE-06 #17 / CORE-07 #18 ausentes)")
        else:
            seg.ok("A1", "CLI compila programa Fork/Join (exit 0)", False, _tail(blob, 1200))
        return seg
    fases = [f"[Fase {i}]" for i in (1, 2, 3, 4)]
    seg.ok("A1", "CLI exit 0 e percorre Fases 1-4 (léxico/sintático, semântico, TAC, C++/g++)",
           all(f in comp["stdout"] for f in fases) and "[SUCESSO]" in comp["stdout"],
           dict(exit=comp["exit"], fases=[f for f in fases if f in comp["stdout"]]))

    if not seg.ok("A2", "Artefatos TAC, C++ e .exe existem e não estão vazios",
                  all(p.is_file() and p.stat().st_size > 0 for p in (tac, cpp, exe)),
                  {p.name: (p.stat().st_size if p.is_file() else None) for p in (tac, cpp, exe)}):
        return seg
    tac_text = tac.read_text(encoding="utf-8")
    forks = FORK_RE.findall(tac_text)
    joins = JOIN_RE.findall(tac_text)
    seg.ok("A3", "TAC contém fork soma_quadrados/fib ... on <destino> e 2 joins",
           sorted(f[0] for f in forks) == ["fib", "soma_quadrados"] and len(joins) >= 2,
           dict(fork_lines=[l for l in tac_text.splitlines() if " fork " in f" {l} "],
                join_lines=[l for l in tac_text.splitlines() if re.search(r"\bjoin\b", l)]))
    cpp_text = cpp.read_text(encoding="utf-8")
    marks = ['#include "minipar_rt/minipar_rt.hpp"', 'register_function("soma_quadrados"',
             'register_function("fib"', "worker_main_if_requested", "minipar_rt::start(", "set_build_id("]
    seg.ok("A4", "C++ gerado usa a API do runtime (include, register_function, worker, start, build_id)",
           all(m in cpp_text for m in marks), dict(ausentes=[m for m in marks if m not in cpp_text]))

    # Execução local
    loc = run([exe, ], stdin_text="local\n", timeout=args.timeout)
    seg.data["run_local"] = dict(stdin="local", exit=loc["exit"], stdout=loc["stdout"], stderr=_tail(loc["stderr"]),
                                 timed_out=loc["timed_out"], duration_ms=loc["duration_ms"])
    seg.ok("A5", "Destino local: stdout == oráculo, exit 0, stderr vazio",
           loc["exit"] == 0 and loc["stdout"] == oracle and loc["stderr"] == "",
           dict(exit=loc["exit"], stdout=loc["stdout"], esperado=oracle, stderr=_tail(loc["stderr"], 300)))

    # Worker no loopback
    ports = free_ports(args.port_base, 2)
    if len(ports) < 2:
        seg.check("A6", "Worker no loopback", "BLOCKED", f"sem 2 portas livres em {args.port_base}-{PORT_MAX}")
        return seg
    port, dead_port = ports
    log = OUT / "segA_worker.log"
    proc = None
    try:
        with open(log, "wb") as fh:
            proc = subprocess.Popen([str(exe), "--minipar-worker", str(port), "--bind", "127.0.0.1"],
                                    cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=fh)
        seg.data["worker"] = dict(cmd=[str(exe), "--minipar-worker", str(port), "--bind", "127.0.0.1"], pid=proc.pid,
                                  port=port, log=str(log.relative_to(ROOT)))
        ready = _wait_log(log, re.compile(r"escutando em 127\.0\.0\.1:(\d+)"), 1, proc, 15)
        if not ready:
            seg.ok("A6", f"Worker escuta em 127.0.0.1:{port}", False,
                   dict(exit=proc.poll(), log=_tail(_txt(log.read_bytes()), 600)))
            return seg
        dest = f"127.0.0.1:{port}"
        rem = run([exe], stdin_text=dest + "\n", timeout=args.timeout)
        seg.data["run_worker"] = dict(stdin=dest, exit=rem["exit"], stdout=rem["stdout"], stderr=_tail(rem["stderr"]),
                                      timed_out=rem["timed_out"], duration_ms=rem["duration_ms"])
        seg.ok("A6", f"Destino {dest}: stdout == oráculo, exit 0, stderr vazio",
               rem["exit"] == 0 and rem["stdout"] == oracle and rem["stderr"] == "",
               dict(exit=rem["exit"], stdout=rem["stdout"], esperado=oracle, stderr=_tail(rem["stderr"], 300)))
        res_re = re.compile(r"^\[minipar_worker ([^\]]+):(\d+)\] RESULT (\S+) fn=(\w+) (\S+)", re.M)
        _wait_log(log, res_re, 2, proc, 5)
        wlog = _txt(log.read_bytes())
        tasks = re.findall(r"^\[minipar_worker ([^\]]+):(\d+)\] TASK (\S+) fn=(\w+) .*: inicio", wlog, re.M)
        results = res_re.findall(wlog)
        pid = str(proc.pid)
        seg.data["worker_log_excerpt"] = [l for l in wlog.splitlines() if " TASK " in l or " RESULT " in l or "escutando" in l]
        seg.ok("A7", "Log do worker: TASK e RESULT ok de soma_quadrados e fib, emitidos pelo PID do worker",
               sorted(t[3] for t in tasks) == ["fib", "soma_quadrados"]
               and sorted(r[3] for r in results) == ["fib", "soma_quadrados"]
               and all(t[1] == pid for t in tasks) and all(r[1] == pid and r[4] == "ok" for r in results),
               dict(worker_pid=proc.pid, tasks=tasks, results=results))
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()                       # só o processo iniciado aqui (por handle/PID)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                seg.notes.append(f"worker PID {proc.pid} não terminou em 10 s após kill")

    # Controle negativo: destino sem worker não pode cair em execução local silenciosa.
    dest = f"127.0.0.1:{dead_port}"
    neg = run([exe], stdin_text=dest + "\n", timeout=args.timeout)
    seg.data["run_sem_worker"] = dict(stdin=dest, exit=neg["exit"], stdout=neg["stdout"], stderr=_tail(neg["stderr"], 600))
    seg.ok("A8", f"Controle negativo {dest} (sem worker): exit != 0, erro em stderr e sem o resultado do oráculo",
           neg["exit"] not in (0, None) and neg["stdout"] != oracle and neg["stderr"].strip() != "",
           dict(exit=neg["exit"], stdout=neg["stdout"], stderr=_tail(neg["stderr"], 300)))
    return seg


# --------------------------------------------------------------------------- segmento B
SERVICE_HELPER = r"""
import contextlib, hashlib, io, json, sys, traceback
root, out_path = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
req = json.loads(sys.stdin.read())
res = dict(python=sys.version.split()[0])
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        from src import service
        res["service_file"] = service.__file__
        res["service_sha256"] = hashlib.sha256(open(service.__file__, "rb").read()).hexdigest()
        a = service.analyze(req["plain"])
        c = service.compile_program(req["plain"])
        bid = c["artifacts"]["binary_id"]
        e = service.execute(bid, stdin=req["stdin"], timeout_sec=req["timeout"]) if bid else None
        arts = {k: service.get_artifact(c["request_id"], k) for k in ("cpp", "tac", "binary")}
        res.update(analyze=a, compile=c, execute=e, artifacts=arts,
                   execute_invalid=service.execute("../x", "", 10),
                   execute_unknown=service.execute("0" * 32, "", 10),
                   artifact_bad_kind=service.get_artifact(c["request_id"], "arm"))
        fa = service.analyze(req["fork"])
        res["fork_analyze"] = fa
        if fa.get("ok"):
            fc = service.compile_program(req["fork"])
            res["fork_compile"] = fc
            fb = fc["artifacts"]["binary_id"]
            if fb:
                res["fork_execute"] = service.execute(fb, stdin="local\n", timeout_sec=req["timeout"])
except BaseException:
    res["helper_exception"] = traceback.format_exc()
res["captured_stdout"] = buf.getvalue()[-4000:]
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
"""


def resolve_core08(arg: str | None) -> tuple[Path | None, str]:
    if arg:
        return Path(arg).resolve(), "--core08-root"
    if os.environ.get("MINIPAR_CORE08_ROOT"):
        return Path(os.environ["MINIPAR_CORE08_ROOT"]).resolve(), "MINIPAR_CORE08_ROOT"
    sib = ROOT.parent / "int01-core08"
    return (sib.resolve(), "pasta irmã int01-core08") if sib.exists() else (None, "não encontrado")


def _check_envelope(seg, cid, env, operation, source, expect_artifacts):
    problems = []
    if env.get("contract") != "minipar.compile.v1": problems.append("contract")
    if env.get("operation") != operation: problems.append("operation")
    if not re.fullmatch(r"[0-9a-f]{32}", str(env.get("request_id"))): problems.append("request_id")
    if env.get("source_hash") != "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest(): problems.append("source_hash")
    if not isinstance(env.get("duration_ms"), int) or env["duration_ms"] < 0: problems.append("duration_ms")
    phases = env.get("phases", {})
    if list(phases) != list(PHASES): problems.append(f"ordem das fases {list(phases)}")
    for name, ph in phases.items():
        if ph.get("status") not in ("ok", "error", "skipped"): problems.append(f"{name}.status")
        if ("reason" in ph) != (ph.get("status") == "skipped"): problems.append(f"{name}.reason")
    requested = PHASES if operation == "compile" else PHASES[:5]
    if any(phases.get(p, {}).get("status") != "ok" for p in requested): problems.append("fase solicitada != ok")
    if operation == "analyze" and phases.get("gpp") != {"status": "skipped", "reason": "not_requested"}: problems.append("gpp analyze")
    tacp = phases.get("tac", {})
    if not tacp.get("text") or tacp.get("lines") != len(tacp.get("text", "").splitlines()): problems.append("tac.text/lines")
    if not phases.get("cpp", {}).get("text"): problems.append("cpp.text")
    if operation == "compile" and (phases.get("gpp", {}).get("returncode") != 0 or not phases["gpp"].get("command")): problems.append("gpp payload")
    if env.get("diagnostics") != []: problems.append("diagnostics")
    arts = env.get("artifacts", {})
    want = env.get("request_id") if expect_artifacts else None
    if arts != {"cpp_id": want, "tac_id": want, "binary_id": want}: problems.append(f"artifacts={arts}")
    if env.get("ok") is not True: problems.append("ok")
    return seg.ok(cid, f"Envelope minipar.compile.v1 de {operation} conforme C-WEB-v1 §1.3/1.4", not problems,
                  dict(problemas=problems, request_id=env.get("request_id"), duration_ms=env.get("duration_ms"),
                       phases={k: v.get("status") for k, v in phases.items()}))


def _summ(env):
    if not isinstance(env, dict):
        return env
    s = {k: v for k, v in env.items() if k != "phases"}
    if "phases" in env:
        s["phases"] = {k: {kk: (vv if kk in ("status", "reason", "returncode", "command", "lines") else "<omitido>")
                           for kk, vv in v.items()} for k, v in env["phases"].items()}
    return s


def segment_b(args) -> Segment:
    seg = Segment("B", "Serviço C-WEB-v1 (CORE-08, PR #19) em árvore separada", "A+B")
    core08, origin = resolve_core08(args.core08_root)
    seg.data["core08_root"] = str(core08) if core08 else None
    seg.data["core08_origin"] = origin
    if core08 is None or not (core08 / "src" / "service.py").is_file():
        seg.check("B0", "Localizar src/service.py do CORE-08", "BLOCKED",
                  f"{core08} ({origin}) sem src/service.py; informe --core08-root ou MINIPAR_CORE08_ROOT")
        seg.block("Árvore do CORE-08 (#19) indisponível")
        return seg
    seg.data["core08_head"] = git_head(core08)
    seg.data["int01_tem_service"] = (ROOT / "src" / "service.py").is_file()
    OUT.mkdir(parents=True, exist_ok=True)
    out_json = OUT / "segB_service_raw.json"
    if out_json.exists():
        out_json.unlink()
    plain, fork = fonte_sem_fork(), fonte_fork()
    (OUT / "segB_sem_fork.minipar").write_text(plain, encoding="utf-8", newline="\n")
    req = dict(plain=plain, fork=fork, stdin=NOME_STDIN + "\n", timeout=min(max(args.timeout, 1), 30))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    r = run([sys.executable, "-B", "-c", SERVICE_HELPER, core08, out_json], cwd=core08,
            stdin_text=json.dumps(req), timeout=4 * COMPILE_TIMEOUT, env=env)
    seg.data["helper"] = dict(exit=r["exit"], duration_ms=r["duration_ms"], stderr=_tail(r["stderr"], 1500),
                              timed_out=r["timed_out"], cwd=str(core08))
    if r["exit"] != 0 or not out_json.exists():
        seg.ok("B1", "Subprocesso importa src.service do CORE-08", False, seg.data["helper"])
        return seg
    res = json.loads(out_json.read_text(encoding="utf-8"))
    seg.data["service_sha256"] = res.get("service_sha256")
    seg.data["python_core08"] = res.get("python")
    if res.get("helper_exception"):
        seg.ok("B1", "Chamadas ao serviço sem exceção", False, _tail(res["helper_exception"], 1500))
        return seg
    seg.ok("B1", "Subprocesso isolado importa src.service do CORE-08 e chama a API sem exceção", True,
           dict(service_file=res.get("service_file"), cwd=str(core08)))

    a, c, e = res["analyze"], res["compile"], res["execute"]
    seg.data.update(analyze=_summ(a), compile=_summ(c), execute=e, artifacts=res["artifacts"],
                    execute_invalid=res["execute_invalid"], execute_unknown=res["execute_unknown"],
                    artifact_bad_kind=res["artifact_bad_kind"])
    _check_envelope(seg, "B2", a, "analyze", plain, expect_artifacts=False)
    _check_envelope(seg, "B3", c, "compile", plain, expect_artifacts=True)
    seg.ok("B4", "request_id distintos e source_hash igual entre analyze e compile",
           a.get("request_id") != c.get("request_id") and a.get("source_hash") == c.get("source_hash"),
           dict(analyze=a.get("request_id"), compile=c.get("request_id"), source_hash=c.get("source_hash")))
    oracle = oraculo_sem_fork(NOME_STDIN)
    seg.data["oracle_sem_fork"] = oracle
    exec_ok = (isinstance(e, dict) and set(e) == EXEC_KEYS and e["contract"] == "minipar.execute.v1"
               and e["artifact_id"] == c.get("request_id") and e["ok"] is True and e["exit_code"] == 0
               and e["timed_out"] is False and e["stdout"] == oracle and e["stderr"] == ""
               and e["stdout_truncated"] is False and e["stderr_truncated"] is False and e["error"] is None)
    seg.ok("B5", "execute: envelope minipar.execute.v1 completo e stdout == oráculo", exec_ok,
           dict(stdout=(e or {}).get("stdout"), esperado=oracle, exit_code=(e or {}).get("exit_code"),
                chaves_extras_ou_faltando=sorted(set(e or {}) ^ EXEC_KEYS)))
    rid = c.get("request_id") or ""
    ext = ".exe" if os.name == "nt" else ""
    media = {"cpp": "text/x-c++src", "tac": "text/plain", "binary": "application/octet-stream"}
    fname = {"cpp": ".cpp", "tac": ".tac", "binary": ext}
    art_ok = all(res["artifacts"][k].get("ok") is True and res["artifacts"][k].get("media_type") == media[k]
                 and res["artifacts"][k].get("filename") == f"minipar_{rid[:8]}{fname[k]}"
                 and Path(res["artifacts"][k].get("path", "")).parent.name == rid
                 and Path(res["artifacts"][k]["path"]).is_file() for k in media)
    seg.ok("B6", "get_artifact cpp/tac/binary: nome, media_type e arquivo no diretório do request_id (§1.7)",
           art_ok, res["artifacts"])
    inv, unk, bad = res["execute_invalid"], res["execute_unknown"], res["artifact_bad_kind"]
    seg.ok("B7", "Erros contratuais: id inválido -> INVALID_ARGUMENT; id desconhecido -> ARTIFACT_NOT_FOUND; kind 'arm' -> INVALID_ARGUMENT",
           inv.get("ok") is False and inv.get("exit_code") is None and (inv.get("error") or {}).get("code") == "INVALID_ARGUMENT"
           and unk.get("ok") is False and (unk.get("error") or {}).get("code") == "ARTIFACT_NOT_FOUND"
           and bad.get("ok") is False and (bad.get("error") or {}).get("code") == "INVALID_ARGUMENT",
           dict(invalid=inv.get("error"), unknown=unk.get("error"), bad_kind=bad.get("error")))

    # Programa com Fork/Join pelo serviço: #19 sozinho não tem o backend de #17/#18.
    fa = res.get("fork_analyze") or {}
    seg.data["fork_analyze"] = _summ(fa)
    statuses = {k: v.get("status") for k, v in fa.get("phases", {}).items()}
    if fa.get("ok"):
        fe = res.get("fork_execute") or {}
        seg.data.update(fork_compile=_summ(res.get("fork_compile")), fork_execute=fe)
        seg.ok("B8", "Programa Fork/Join pelo serviço: compile + execute(local) == oráculo",
               fe.get("ok") is True and fe.get("stdout") == oraculo_fork(), dict(stdout=fe.get("stdout"), esperado=oraculo_fork()))
    else:
        failed = next((k for k, v in statuses.items() if v == "error"), None)
        front_ok = all(statuses.get(p) == "ok" for p in ("lexer", "parser", "semantic"))
        if front_ok and failed in ("tac", "cpp"):
            seg.check("B8", "Programa Fork/Join pelo serviço", "BLOCKED",
                      dict(motivo="conflito #19 × #17/#18 em src/codegen.py e src/tac.py: o serviço do #19 não "
                                  "tem o TAC/backend Fork/Join; integração cabe ao Eixo A",
                           fase_recusada=failed, phases=statuses, diagnostics=fa.get("diagnostics")))
        else:
            seg.ok("B8", "Programa Fork/Join pelo serviço: frontend (léxico/sintático/semântico) aceita", False,
                   dict(phases=statuses, diagnostics=fa.get("diagnostics")))
    return seg


# --------------------------------------------------------------------------- segmento C
def segment_c(args) -> Segment:
    seg = Segment("C", "Web didática chamando o serviço real (WEB-03)", "B")
    web = ROOT / "web_didatica"
    if not web.is_dir():
        seg.check("C1", "web_didatica/ presente", "BLOCKED", "pasta ausente")
        seg.block("web_didatica/ ausente nesta base")
        return seg
    py_hits, js_hits = [], []
    py_re = re.compile(r"^\s*(from\s+(src\.)?service\s+import|import\s+(src\.)?service\b|from\s+src\s+import\s+.*\bservice\b)|\bcompile_program\s*\(", re.M)
    js_re = re.compile(r"fetch\s*\([^)]*['\"`][^'\"`]*/api/v1/")
    for p in sorted(web.rglob("*")):
        if not p.is_file() or p.suffix not in (".py", ".js", ".html"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if p.suffix == ".py":
            py_hits += [f"{rel}: {m.group(0).strip()}" for m in py_re.finditer(text)]
        else:
            js_hits += [f"{rel}: {m.group(0).strip()}" for m in js_re.finditer(text)]
    server = web / "server.py"
    mock = web / "static" / "js" / "fonte_mock.js"
    seg.data.update(server_py=server.is_file(), fonte_mock=mock.is_file(), py_usa_servico=py_hits, js_chama_api=js_hits,
                    metodo="inspeção estática; nenhum servidor iniciado, nenhuma porta aberta")
    if not server.is_file() and not py_hits and not js_hits:
        seg.check("C1", "Web didática integrada ao serviço real (rotas /api/v1 + src/service.py)", "BLOCKED",
                  dict(motivo="WEB-03 não iniciado: sem web_didatica/server.py, sem import de service/compile_program, "
                              "sem fetch para /api/v1; dados vêm de fixtures via static/js/fonte_mock.js",
                       fonte_mock=mock.is_file()))
        seg.block("WEB-03 não iniciado (Eixo B)")
    else:
        seg.check("C1", "Web didática integrada ao serviço real", "UNTESTED",
                  dict(motivo="indícios de integração encontrados; este smoke não sobe servidor. Validar com o Eixo B "
                              "(cliente de teste Flask sem porta, ou 127.0.0.1:5001 autorizado)",
                       server_py=server.is_file(), py=py_hits, js=js_hits))
    return seg


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="INT-01: smoke de integração dos três eixos")
    ap.add_argument("--port-base", type=int, default=PORT_MIN, help=f"primeira porta do worker ({PORT_MIN}-{PORT_MAX})")
    ap.add_argument("--only", choices=("A", "B", "C"), help="executa só um segmento")
    ap.add_argument("--timeout", type=int, default=30, help="limite (s) de cada execução de programa compilado")
    ap.add_argument("--core08-root", help="raiz da árvore com CORE-08/PR #19 (ou env MINIPAR_CORE08_ROOT)")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if not PORT_MIN <= args.port_base <= PORT_MAX - 1:
        ap.error(f"--port-base deve ficar em {PORT_MIN}-{PORT_MAX - 1}")
    if args.timeout < 1:
        ap.error("--timeout deve ser >= 1")

    OUT.mkdir(parents=True, exist_ok=True)
    meta = dict(card="INT-01", started=_dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                cwd=str(ROOT), int01_head=git_head(ROOT), python=sys.version.split()[0], python_exe=sys.executable,
                gpp=tool_version([shutil.which("g++") or "g++", "--version"]), platform=sys.platform,
                args=vars(args))
    print(f"INT-01 smoke — {meta['started']} — HEAD {meta['int01_head']}")
    print(f"python {meta['python']} | {meta['gpp']}")
    segs = []
    for sid, fn in (("A", segment_a), ("B", segment_b), ("C", segment_c)):
        if args.only and args.only != sid:
            continue
        print(f"\n== Segmento {sid} ==")
        t0 = time.monotonic()
        try:
            seg = fn(args)
        except Exception as exc:          # falha do próprio smoke: registrada como FAIL, nunca PASS
            seg = Segment(sid, f"segmento {sid}", "?")
            seg.ok(f"{sid}!", "smoke executou sem exceção", False, f"{type(exc).__name__}: {exc}")
        seg.data["duration_ms"] = round((time.monotonic() - t0) * 1000)
        segs.append(seg)

    print("\n== Resumo INT-01 ==")
    print(f"{'Seg':<4}{'Eixos':<7}{'Status':<10}Descrição")
    for s in segs:
        print(f"{s.sid:<4}{s.eixos:<7}{s.status:<10}{s.title}")
        if s.blocked_reason:
            print(f"{'':<21}bloqueio: {s.blocked_reason}")
    failed = [s.sid for s in segs if s.status == "FAIL"]
    pending = [s.sid for s in segs if s.status != "PASS"]
    code = 1 if failed else 0
    if pending:
        print(f"\nATENÇÃO: segmentos {', '.join(pending)} não estão PASS. BLOCKED/PARTIAL significam que o card "
              "INT-01 NÃO está concluído; A e B precisam validar seus segmentos.")
    print("Loopback não prova execução entre dois computadores (RUN-03, PR #10).")
    report = dict(meta=meta, exit_code=code, segments=[s.as_dict() for s in segs],
                  summary={s.sid: s.status for s in segs},
                  finished=_dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    (OUT / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados: {(OUT / 'results.json').relative_to(ROOT)} | exit {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
