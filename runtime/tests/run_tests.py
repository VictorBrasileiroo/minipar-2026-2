"""Compila e executa os testes do runtime minipar_rt (Eixo C).

Uso (da raiz do repositório):
    python runtime/tests/run_tests.py [--cxx CAMINHO_GPP] [--keep-going]

Usa só a biblioteca padrão. Binários em output/runtime-tests/ (ignorado pelo Git).
Exit 0 somente se todas as etapas passarem.
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent
REPO = RUNTIME.parent
TESTS = RUNTIME / "tests"
INCLUDE = RUNTIME / "include"
OUT = REPO / "output" / "runtime-tests"
DEFAULT_GPP = Path(r"C:\msys64\ucrt64\bin\g++.exe")
EXE = ".exe" if os.name == "nt" else ""


def find_cxx(arg: str | None) -> str:
    cand = arg or os.environ.get("CXX") or (str(DEFAULT_GPP) if DEFAULT_GPP.is_file() else "g++")
    found = shutil.which(cand) or cand
    return found


def make_env(cxx: str) -> dict:
    env = dict(os.environ)
    # DLLs do runtime do compilador (ex.: UCRT64) só no PATH deste processo e dos filhos.
    parent = Path(cxx).parent
    if parent.is_dir():
        env["PATH"] = str(parent) + os.pathsep + env.get("PATH", "")
    return env


def compile_one(cxx: str, src: Path, env: dict) -> tuple[bool, Path, str]:
    exe = OUT / (src.stem + EXE)
    cmd = [cxx, "-std=c++20", "-O2", "-Wall", "-Wextra", "-Werror", "-pthread", f"-I{INCLUDE}", str(src), "-o", str(exe)]
    if os.name == "nt":
        cmd.append("-lws2_32")
    t0 = time.perf_counter()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    msg = f"compilar {src.name}: exit={p.returncode} ({time.perf_counter() - t0:.1f} s)"
    if p.returncode != 0:
        msg += "\n" + p.stdout + p.stderr
    return p.returncode == 0, exe, msg


def run(cmd: list[str], env: dict, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, timeout=timeout)


def step_unit(exe: Path, ctx: dict) -> tuple[bool, str]:
    p = run([str(exe)], ctx["env"])
    return p.returncode == 0, p.stdout + p.stderr


def step_join_or_exit_probe(exe: Path, ctx: dict) -> tuple[bool, str]:
    p = run([str(exe)], ctx["env"])
    ok = (p.returncode == 1 and "ok=42" in p.stdout and "NAO DEVERIA" not in p.stdout
          and "[minipar_rt] join task-2 falhou: TASK_FAILED: erro de proposito" in p.stderr)
    return ok, f"exit={p.returncode}\nstdout: {p.stdout.strip()}\nstderr: {p.stderr.strip()}"


def free_ports(n: int) -> list[int]:
    socks, ports = [], []
    for _ in range(n):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        socks.append(s)
        ports.append(s.getsockname()[1])
    for s in socks:
        s.close()
    return ports


def start_worker(exe: Path, port: int, log: Path, env: dict) -> subprocess.Popen:
    fh = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen([str(exe), "--minipar-worker", str(port)], stdout=subprocess.DEVNULL, stderr=fh, env=env)
    deadline = time.time() + 10
    while time.time() < deadline:
        if proc.poll() is not None:
            break
        if "escutando em" in log.read_text(encoding="utf-8", errors="replace"):
            return proc
        time.sleep(0.05)
    proc.kill()
    raise RuntimeError(f"worker na porta {port} nao ficou pronto; log: {log.read_text(errors='replace')}")


def step_remote(exe: Path, ctx: dict) -> tuple[bool, str]:
    """Dois processos worker (A e B) no loopback; o teste derruba B de propósito (morrer -> exit 3)."""
    ok_w, worker_exe, msg = compile_one(ctx["cxx"], TESTS / "test_worker.cpp", ctx["env"])
    if not ok_w:
        return False, msg
    port_a, port_b, port_dead = free_ports(3)
    log_a, log_b = OUT / "worker_A.log", OUT / "worker_B.log"
    wa = start_worker(worker_exe, port_a, log_a, ctx["env"])
    wb = start_worker(worker_exe, port_b, log_b, ctx["env"])
    env = dict(ctx["env"], MINIPAR_TEST_PORT_A=str(port_a), MINIPAR_TEST_PORT_B=str(port_b),
               MINIPAR_TEST_PORT_DEAD=str(port_dead))
    try:
        p = run([str(exe)], env, timeout=180)
        try:
            b_exit = wb.wait(timeout=5)
        except subprocess.TimeoutExpired:
            b_exit = None
        a_alive = wa.poll() is None
    finally:
        for w in (wa, wb):
            if w.poll() is None:
                w.kill()
                w.wait(timeout=5)
    log_a_txt = log_a.read_text(encoding="utf-8", errors="replace")
    log_b_txt = log_b.read_text(encoding="utf-8", errors="replace")
    ok = p.returncode == 0 and b_exit == 3 and a_alive
    report = (p.stdout + p.stderr).rstrip() + "\n"
    report += (f"worker A (porta {port_a}): vivo no fim={a_alive}; linhas TASK={log_a_txt.count('] TASK ')}, "
               f"conexoes rejeitadas={log_a_txt.count('rejeitada')}\n")
    report += f"worker B (porta {port_b}): exit={b_exit} (esperado 3, morte proposital); linhas TASK={log_b_txt.count('] TASK ')}\n"
    report += "primeiras linhas do log do worker A:\n" + "\n".join(log_a_txt.splitlines()[:4])
    return ok, report


STEPS = [
    ("RUN-01 testes locais", "tests/test_local.cpp", step_unit),
    ("RUN-01 join_or_exit encerra com codigo 1", "tests/join_or_exit_probe.cpp", step_join_or_exit_probe),
    ("RUN-02 codec JSON e frames", "tests/test_protocol.cpp", step_unit),
    ("RUN-02 coordenador <-> 2 workers (processos no loopback)", "tests/test_remote.cpp", step_remote),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cxx")
    ap.add_argument("--keep-going", action="store_true", help="continua depois de uma falha")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cxx = find_cxx(args.cxx)
    env = make_env(cxx)
    OUT.mkdir(parents=True, exist_ok=True)
    ver = run([cxx, "--version"], env).stdout.splitlines()
    print(f"# minipar_rt — {platform.platform()} — {ver[0] if ver else cxx}")

    ctx = {"cxx": cxx, "env": env}
    results = []
    built: dict[str, Path] = {}
    for title, src_name, fn in STEPS:
        if src_name not in built:
            ok, exe, msg = compile_one(cxx, RUNTIME / src_name, env)
            print(msg)
            if not ok:
                results.append((title, False))
                if not args.keep_going:
                    break
                continue
            built[src_name] = exe
        try:
            ok, out = fn(built[src_name], ctx)
        except (subprocess.TimeoutExpired, RuntimeError) as exc:
            ok, out = False, f"erro: {exc}"
        print(f"\n## {title}: {'PASS' if ok else 'FAIL'}\n{out.rstrip()}\n")
        results.append((title, ok))
        if not ok and not args.keep_going:
            break

    print("# Resumo")
    for title, ok in results:
        print(f"- {'PASS' if ok else 'FAIL'}: {title}")
    all_ok = len(results) == len(STEPS) and all(ok for _, ok in results)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
