"""INT-02: regressão integral T01–T11 e das três interfaces (Eixo B).

Orquestra os verificadores que já existem no repositório, sem reimplementar
oráculos: cada etapa é um processo separado com o Python deste interpretador,
log próprio e o JSON do verificador copiado para a pasta da rodada.

Etapas (na ordem):
  T01-T07   scripts/baseline_t01_t07.py --repeat N   (oráculos do CORE-01/CORE-10)
  T08       tests/2026_2/test08/run_t08.py
  T09       tests/2026_2/test09/run_t09.py
  T10       tests/2026_2/test10/run_t10.py
  T11       tests/2026_2/test11/verificar_t11.py
  IF-TERM   tests/2026_2/core09/test_interfaces.py   (terminal + Web original, sem porta)
  IF-WEB1   tests/2026_2/core09/smoke_http.py        (main.py opção 2 -> HTTP real em 127.0.0.1:5000)
  IF-WEB2   unittest de web_didatica/tests            (Web didática, cliente de teste do Flask)
  INT-01    scripts/smoke_int01.py                    (CLI Fork/Join -> runtime; serviço; Web didática)
  SUITES    testes de unidade/integração do núcleo (CORE-02, 06, 07, 08, DEF-01)

Uso (na raiz, com o Python do .venv, que tem Flask):
    .venv\\Scripts\\python.exe -B scripts/regressao_int02.py [--repeat 10] [--only T08,T11]

Resultado: output/int02/run-<data>/results.json e um .log por etapa (output/ é ignorado pelo Git).
Código de saída: 0 só se todas as etapas executadas forem PASS; 1 se houver FAIL;
3 se não houver FAIL mas alguma etapa ficar BLOCKED/PARTIAL.

Só usa 127.0.0.1. Não prova execução entre computadores nem no CPUlator: essas
provas são as dos cards RUN-03/RUN-05/RUN-06 e T11-03 e são citadas no relatório
do INT-02, não refeitas aqui.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "int02"
PY = sys.executable


def _exit_map(mapping: dict[int, str]):
    return lambda code: "PASS" if code == 0 else mapping.get(code, "FAIL")


# id, descrição, comando (relativo à raiz), timeout (s), JSON do verificador, mapeamento do exit
def steps(repeat: int) -> list[dict]:
    unit = _exit_map({})
    return [
        dict(id="T01-T07", desc="Testes herdados T01–T07 (oráculos CORE-01/CORE-10)",
             cmd=[PY, "-B", "scripts/baseline_t01_t07.py", "--repeat", str(repeat)],
             timeout=3600, json="core01-latest", status=_exit_map({2: "BLOCKED"})),
        dict(id="T08", desc="T08: 160 avaliações em 4 trabalhos (seq, par local, par remoto loopback)",
             cmd=[PY, "-B", "tests/2026_2/test08/run_t08.py"],
             timeout=1800, json="output/test08/results.json", status=_exit_map({2: "BLOCKED"})),
        dict(id="T09", desc="T09: T08 + Mandelbrot ASCII (5 trabalhos)",
             cmd=[PY, "-B", "tests/2026_2/test09/run_t09.py"],
             timeout=1800, json="output/test09/results.json", status=_exit_map({2: "BLOCKED"})),
        dict(id="T10", desc="T10: T09 + Sierpinski (6 trabalhos)",
             cmd=[PY, "-B", "tests/2026_2/test10/run_t10.py"],
             timeout=1800, json="output/test10/results.json", status=_exit_map({2: "BLOCKED"})),
        dict(id="T11", desc="T11: MiniCompilador em MiniPar (3 casos, inválidos, .arm = evidência CPUlator)",
             cmd=[PY, "-B", "tests/2026_2/test11/verificar_t11.py"],
             timeout=900, json=None, status=unit),
        dict(id="IF-TERM", desc="Interface 1 (terminal) e Web original sem porta (CORE-09)",
             cmd=[PY, "-B", "tests/2026_2/core09/test_interfaces.py"],
             timeout=1800, json="output/core09/interfaces.json", status=unit),
        dict(id="IF-WEB1", desc="Interface 2 (Web original): main.py opção 2 -> HTTP real 127.0.0.1:5000",
             cmd=[PY, "-B", "tests/2026_2/core09/smoke_http.py"],
             timeout=600, json="output/core09/http.json", status=unit),
        dict(id="IF-WEB2", desc="Interface 3 (Web didática): rotas C-WEB-v1 com serviço e g++ reais",
             cmd=[PY, "-B", "-m", "unittest", "discover", "-s", "web_didatica/tests", "-v"],
             timeout=1800, json=None, status=unit),
        dict(id="INT-01", desc="Smoke dos três eixos (CLI Fork/Join -> runtime; serviço; Web didática)",
             cmd=[PY, "-B", "scripts/smoke_int01.py"],
             timeout=1800, json="output/int01/results.json", status=_exit_map({3: "PARTIAL"})),
        dict(id="S-CORE02", desc="Suíte CORE-02 (TAC do T07 derivado da AST)",
             cmd=[PY, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_core02_tac.py", "-v"],
             timeout=900, json=None, status=unit),
        dict(id="S-CORE06", desc="Suíte CORE-06 (TAC de Fork/Join)",
             cmd=[PY, "-B", "-m", "unittest", "discover", "-s", "tests/2026_2/core06", "-v"],
             timeout=900, json=None, status=unit),
        dict(id="S-CORE07", desc="Suíte CORE-07 (backend C++ + runtime, print atômico)",
             cmd=[PY, "-B", "-m", "unittest", "discover", "-s", "tests/2026_2/core07", "-v"],
             timeout=1800, json=None, status=unit),
        dict(id="S-CORE08", desc="Suíte CORE-08 (serviço de fases)",
             cmd=[PY, "-B", "tests/2026_2/core08/verify_core08.py"],
             timeout=1800, json="output/core08/tests-final.json", status=unit),
        dict(id="S-DEF01", desc="Suíte DEF-01 (canal TCP herdado do T01)",
             cmd=[PY, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_def01_channel.py", "-v"],
             timeout=900, json=None, status=unit),
    ]


def first_line(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ROOT)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception as exc:  # noqa: BLE001 - só identificação do ambiente
        return f"indisponível: {exc}"


def latest_core01(after: float) -> Path | None:
    runs = [p for p in (ROOT / "output" / "core01").glob("run-*/baseline.json") if p.stat().st_mtime >= after]
    return max(runs, key=lambda p: p.stat().st_mtime) if runs else None


def tail(text: str, n: int = 30) -> list[str]:
    return text.splitlines()[-n:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repeat", type=int, default=10, help="execuções de T01 e T02 (intermitência histórica)")
    ap.add_argument("--only", default="", help="IDs separados por vírgula, ex.: T08,IF-WEB2")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    plan = [s for s in steps(args.repeat) if not only or s["id"] in only]
    if only and len(plan) != len(only):
        ap.error(f"IDs desconhecidos: {sorted(only - {s['id'] for s in plan})}")

    gpp = shutil.which(os.environ.get("CXX") or "g++")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if gpp:
        env["CXX"] = gpp
        env["PATH"] = str(Path(gpp).parent) + os.pathsep + env.get("PATH", "")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = OUT / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "card": "INT-02",
        "inicio": datetime.now().astimezone().isoformat(timespec="seconds"),
        "repeat_t01_t02": args.repeat,
        "ambiente": {
            "git_head": first_line(["git", "rev-parse", "HEAD"]),
            "git_branch": first_line(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "git_status_curto": subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                               cwd=ROOT).stdout.splitlines(),
            "python": sys.version.split()[0], "python_exe": Path(PY).name,
            "plataforma": platform.platform(), "cpus_logicas": os.cpu_count(),
            "gxx": first_line([gpp or "g++", "--version"]),
        },
        "etapas": [],
    }
    print(f"=== INT-02: {len(plan)} etapas, HEAD {report['ambiente']['git_head'][:12]} -> {run_dir.relative_to(ROOT)}",
          flush=True)

    for step in plan:
        started = time.time()
        log_path = run_dir / f"{step['id']}.log"
        print(f"\n--- {step['id']}: {step['desc']}", flush=True)
        try:
            proc = subprocess.run(step["cmd"], cwd=ROOT, env=env, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=step["timeout"])
            code, out, err = proc.returncode, proc.stdout, proc.stderr
            status = step["status"](code)
        except subprocess.TimeoutExpired as exc:
            code, status = None, "FAIL"
            out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            err = f"TIMEOUT após {step['timeout']} s"
        seconds = round(time.time() - started, 1)
        log_path.write_text(f"$ {' '.join(step['cmd'][1:])}\n\n[stdout]\n{out}\n[stderr]\n{err}\n", encoding="utf-8")

        runner_json = None
        src = latest_core01(started) if step["json"] == "core01-latest" else (
            ROOT / step["json"] if step["json"] else None)
        if src and src.exists() and src.stat().st_mtime >= started:
            runner_json = run_dir / f"{step['id']}.json"
            shutil.copyfile(src, runner_json)
        elif step["json"]:
            status = "FAIL" if status == "PASS" else status  # verificador não gravou evidência nesta rodada

        rec = {"id": step["id"], "descricao": step["desc"], "comando": " ".join(["python"] + step["cmd"][1:]),
               "exit": code, "segundos": seconds, "status": status,
               "log": log_path.relative_to(ROOT).as_posix(),
               "json_verificador": runner_json.relative_to(ROOT).as_posix() if runner_json else None,
               "fonte_json": src.relative_to(ROOT).as_posix() if src else None,
               "stdout_final": tail(out, 15), "stderr_final": tail(err, 15)}
        if step["id"] == "T01-T07" and runner_json:
            base = json.loads(runner_json.read_text(encoding="utf-8"))
            rec["por_teste"] = base.get("overall", {})
            rec["execucoes"] = {cid: f"{sum(r['status'] == 'PASS' for r in base['results'] if r['id'] == cid)}/"
                                     f"{sum(1 for r in base['results'] if r['id'] == cid)}"
                                for cid in rec["por_teste"]}
            rec["verificacoes_t07"] = [{k: c.get(k) for k in ("check", "status", "reason")}
                                       for c in base.get("extra_checks", [])]
            # O exit do baseline é 1 para qualquer não-PASS (inclusive PARTIAL): o status da etapa
            # é o pior status por teste, para não rotular um PARTIAL como FAIL.
            todos = list(rec["por_teste"].values()) + [c["status"] for c in rec["verificacoes_t07"]
                                                       if c["status"] != "INFO"]
            rec["status"] = next((s for s in ("FAIL", "BLOCKED", "PARTIAL", "UNTESTED") if s in todos), "PASS")
            status = rec["status"]
        report["etapas"].append(rec)
        print(f"{step['id']}: {status} (exit={code}, {seconds} s) -> {rec['log']}", flush=True)
        (run_dir / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    report["fim"] = datetime.now().astimezone().isoformat(timespec="seconds")
    statuses = [e["status"] for e in report["etapas"]]
    report["exit_code"] = 1 if "FAIL" in statuses else 3 if any(s != "PASS" for s in statuses) else 0
    (run_dir / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== RESUMO INT-02")
    for e in report["etapas"]:
        extra = f"  {e['por_teste']} {e['execucoes']}" if "por_teste" in e else ""
        print(f"  {e['id']:<9} {e['status']:<8} exit={e['exit']} {e['segundos']} s{extra}")
    print(f"Evidência: {(run_dir / 'results.json').relative_to(ROOT)} -> exit {report['exit_code']}")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
