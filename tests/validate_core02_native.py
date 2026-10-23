"""CORE-02: ordenação com tamanhos/dados variados no pipeline real e com assertions.

Uso: python -B tests/validate_core02_native.py [--cxx CAMINHO_GPP]
Fontes, TAC, C++, binários e evidência JSON em output/core02/run-<data>/.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import random
import re
import shutil
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from baseline_t01_t07 import (COMPILE_TIMEOUT, DEFAULT_GPP, RUN_TIMEOUT,
                             compile_case, run_proc, sha256, tool_versions)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cxx", default=os.environ.get("CXX") or
                    (str(DEFAULT_GPP) if DEFAULT_GPP.is_file() else "g++"))
    args = ap.parse_args()
    cxx = shutil.which(args.cxx) or args.cxx
    env = dict(os.environ, CXX=cxx, PYTHONIOENCODING="utf-8")
    env["PATH"] = str(Path(cxx).parent) + os.pathsep + env.get("PATH", "")
    run_dir = REPO / "output" / "core02" / datetime.now().strftime("run-%Y%m%d-%H%M%S-%f")
    run_dir.mkdir(parents=True)
    active = REPO / "tests" / "teste7_quicksort_iterativo_tac.minipar"
    function, _ = active.read_text(encoding="utf-8").split("\nseq {", 1)
    cases = {
        "official": [33, 12, 98, 5, 61], "empty": [], "single": [7],
        "pair": [2, 1], "sorted": list(range(12)), "reversed": list(range(12, 0, -1)),
        "equal": [4] * 15, "duplicates": [3, 1, 3, 2, 1, 0, 3],
        "negative": [0, -3, -40, 80, 70, -100],
        "fractional": [1.5, -2.5, 0.25, 1.5, -7.75, 3.125],
    }
    rng = random.Random(202602)
    for n in (3, 4, 6, 17, 31, 64, 127):
        cases[f"random_{n}"] = [rng.randint(-100, 100) for _ in range(n)]
    statements = []
    for i, (name, values) in enumerate(cases.items()):
        statements.extend((f"var a{i} = {json.dumps(values)};",
                           f"var r{i} = quicksort_iterativo(a{i});",
                           f'print("{name}", r{i});'))
    source = run_dir / "variants.minipar"
    source.write_text(function + "\nseq {\n" + "\n".join(statements) + "\n}\n", encoding="utf-8")
    report = {"source": str(source.relative_to(REPO)), "source_sha256": sha256(source),
              "active_source_sha256": sha256(active), "tools": tool_versions(cxx, env),
              "inputs": cases, "expected": {k: sorted(v) for k, v in cases.items()}, "checks": []}
    comp = compile_case(run_dir, source, "variants", env)
    report["pipeline_compile"] = comp
    if comp["returncode"] != 0 or comp["timed_out"] or not comp["exe"]:
        report["checks"].append({"check": "pipeline_compile", "status": "FAIL"})
    else:
        cpp = run_dir / "output" / "variants.cpp"
        checked = run_dir / "output" / "variants_assert.exe"
        command = [cxx, "-std=c++20", "-O0", "-g", "-D_GLIBCXX_ASSERTIONS",
                   str(cpp), "-o", str(checked), "-pthread"]
        if os.name == "nt":
            command.append("-lws2_32")
        assertion_compile = run_proc(command, run_dir, None, COMPILE_TIMEOUT, env)
        report["assertion_compile"] = assertion_compile
        builds = [("native", comp["exe"])]
        if assertion_compile["returncode"] == 0 and not assertion_compile["timed_out"] and checked.is_file():
            builds.append(("assertions", str(checked)))
        else:
            report["checks"].append({"check": "assertion_compile", "status": "BLOCKED"})
        for build, exe in builds:
            run = run_proc([exe], run_dir, "", RUN_TIMEOUT, env)
            got = {}
            for line in run["stdout"].splitlines():
                match = re.fullmatch(r"(\w+) (\[.*\])", line)
                if match:
                    got[match[1]] = json.loads(match[2])
            ok = (run["returncode"] == 0 and not run["timed_out"] and not run["stderr"]
                  and got == report["expected"] and len(run["stdout"].splitlines()) == len(cases))
            report["checks"].append({"check": build, "status": "PASS" if ok else "FAIL",
                                     "cases": len(cases), "run": run, "actual": got,
                                     "binary_sha256": sha256(Path(exe))})
    path = run_dir / "validation.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for check in report["checks"]:
        print(f"{check['check']}: {check['status']} ({check.get('cases', 0)} casos)")
    print(f"Evidencia: {path.relative_to(REPO)}")
    return 0 if all(c["status"] == "PASS" for c in report["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
