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


def step_unit(exe: Path, env: dict) -> tuple[bool, str]:
    p = run([str(exe)], env)
    return p.returncode == 0, p.stdout + p.stderr


def step_join_or_exit_probe(exe: Path, env: dict) -> tuple[bool, str]:
    p = run([str(exe)], env)
    ok = (p.returncode == 1 and "ok=42" in p.stdout and "NAO DEVERIA" not in p.stdout
          and "[minipar_rt] join task-2 falhou: TASK_FAILED: erro de proposito" in p.stderr)
    return ok, f"exit={p.returncode}\nstdout: {p.stdout.strip()}\nstderr: {p.stderr.strip()}"


STEPS = [
    ("RUN-01 testes locais", "test_local.cpp", step_unit),
    ("RUN-01 join_or_exit encerra com codigo 1", "join_or_exit_probe.cpp", step_join_or_exit_probe),
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

    results = []
    built: dict[str, Path] = {}
    for title, src_name, fn in STEPS:
        if src_name not in built:
            ok, exe, msg = compile_one(cxx, TESTS / src_name, env)
            print(msg)
            if not ok:
                results.append((title, False))
                if not args.keep_going:
                    break
                continue
            built[src_name] = exe
        ok, out = fn(built[src_name], env)
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
