"""CORE-01 — baseline reprodutível dos testes herdados T01–T07.

Executa cada programa pelo caminho real do compilador (main.py -> TAC/C++ -> G++ -> binário),
roda o binário com stdin fixo e confere a saída contra um oráculo explícito.
Não altera src/ nem tests/. Artefatos e logs JSON ficam em output/core01/run-<data>/ (ignorado pelo Git).

Uso:
    python scripts/baseline_t01_t07.py [--cxx CAMINHO_GPP] [--repeat 10] [--only T01,T07]

Exit: 0 quando todos os casos terminaram com PASS; 1 se algum FAIL/PARTIAL; 2 se algum BLOCKED.
O exit do script é só um resumo: o status de cada caso, com o motivo, está no relatório impresso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TESTS = REPO / "tests"
EXPECTED = TESTS / "expected_results"
DEFAULT_GPP = Path(r"C:\msys64\ucrt64\bin\g++.exe")
COMPILE_TIMEOUT = 240
RUN_TIMEOUT = 30


def norm(text: str) -> str:
    """Minúsculas, sem acentos e sem espaços duplicados (o código MiniPar herdado imprime sem acento)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_proc(cmd: list[str], cwd: Path, stdin: str | None, timeout: int, env: dict) -> dict:
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, input=stdin, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=env,
        )
        return {
            "cmd": cmd, "stdin": stdin, "returncode": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr, "timed_out": False,
            "duration_s": round(time.perf_counter() - start, 3),
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "cmd": cmd, "stdin": stdin, "returncode": None, "stdout": out,
            "stderr": err, "timed_out": True, "duration_s": round(time.perf_counter() - start, 3),
        }


def ports_free(ports: list[int]) -> bool:
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return False
    return True


# ---------------------------------------------------------------------------
# Oráculos. Cada um recebe o stdout do binário (e o caso) e devolve (status, motivo).
# ---------------------------------------------------------------------------

def oracle_t01(out: str, case: dict) -> tuple[str, str]:
    m = re.search(r"Resultado:\s*(-?\d+(?:\.\d+)?)", out)
    srv = "servidor recebeu: + 2 3" in norm(out)
    if m and abs(float(m.group(1)) - 5.0) < 1e-9 and srv:
        return "PASS", "servidor recebeu '+ 2 3' pelo canal 5101 e cliente recebeu 5 pelo canal 5102 (loopback)"
    return "FAIL", f"esperado servidor '+ 2 3' e Resultado 5; obtido resultado={m.group(1) if m else None}, servidor={srv}"


def oracle_t02(out: str, case: dict) -> tuple[str, str]:
    # As duas tarefas do `par` imprimem concorrentemente e `print` com vários argumentos não é atômico:
    # o valor do fatorial pode sair depois do rótulo "Fibonacci:". O oráculo confere os valores, não o layout.
    if "Fatorial de 5:" not in out or "Fibonacci:" not in out:
        return "FAIL", "rótulos 'Fatorial de 5:' e/ou 'Fibonacci:' ausentes"
    body = out.replace("Fatorial de 5:", " ")  # o 5 do rótulo não é resultado
    nums = [int(x) for x in re.findall(r"(?m)(?<![\w.])-?\d+(?![\w.])", body)]
    if 120 not in nums:
        if any("120" in str(n) for n in nums):
            return "FAIL", (f"saída corrompida: o 120 do fatorial foi impresso colado a um número do Fibonacci "
                            f"(print não atômico entre threads do par); números lidos: {nums}")
        return "FAIL", f"fatorial 120 ausente; números lidos: {nums}"
    rest = list(nums)
    rest.remove(120)
    if rest != [0, 1, 1, 2, 3, 5, 8, 13]:
        return "FAIL", f"série de Fibonacci incorreta: {rest}"
    interleaved = not re.search(r"Fatorial de 5:\s*120", out)
    note = " (saídas das duas tarefas intercaladas: print não atômico entre threads)" if interleaved else ""
    return "PASS", "fatorial 5 = 120 e Fibonacci 0,1,1,2,3,5,8,13" + note


def _t03_iterations(out: str) -> dict[int, dict[str, float]]:
    its: dict[int, dict[str, float]] = {}
    cur = None
    for ln in out.splitlines():
        m = re.match(r"\s*Iteracao:\s*(\d+)", ln)
        if m:
            cur = int(m.group(1))
            its[cur] = {}
            continue
        m = re.match(r"\s*(Saida|Erro|Peso entrada|Peso bias):\s*(-?[\d.]+(?:e-?\d+)?)", ln)
        if m and cur is not None:
            its[cur][m.group(1)] = float(m.group(2))
    return its


def oracle_t03(out: str, case: dict) -> tuple[str, str]:
    # O .expected.txt veio da referência Python e usa outro formato de texto ("Peso:", "####", 4 casas).
    # O oráculo compara os VALORES das iterações registradas no esperado (1, 50, 51) com tolerância de
    # arredondamento de 4 casas, a convergência e o valor desejado.
    its = _t03_iterations(out)
    want = {1: (1, -1, 0.5, 0.5), 50: (1, -1, 0.01, 0.01), 51: (0, 0, 0.0, 0.0)}
    problems = []
    for it, (saida, erro, peso, bias) in want.items():
        got = its.get(it)
        if not got:
            problems.append(f"iteração {it} ausente")
            continue
        if got.get("Saida") != saida or got.get("Erro") != erro:
            problems.append(f"it {it}: saída/erro {got.get('Saida')}/{got.get('Erro')} != {saida}/{erro}")
        if abs(got.get("Peso entrada", 99) - peso) > 5e-5 or abs(got.get("Peso bias", 99) - bias) > 5e-5:
            problems.append(f"it {it}: pesos {got.get('Peso entrada')}/{got.get('Peso bias')} != {peso}/{bias}")
    if max(its, default=0) != 51:
        problems.append(f"última iteração {max(its, default=0)} != 51")
    if not re.search(r"Valor desejado:\s*0\b", out) or "aprendeu" not in out:
        problems.append("fechamento (aprendeu / valor desejado 0) ausente")
    if not problems:
        return "PASS", ("iterações 1, 50 e 51 com saída/erro/pesos iguais ao esperado (4 casas), convergência na 51 "
                        "e valor desejado 0; formato textual difere do .expected.txt da referência Python")
    return "FAIL", "; ".join(problems)


def oracle_t04(out: str, case: dict) -> tuple[str, str]:
    ref = {(0, 0): 0.0089, (0, 1): 0.9769, (1, 0): 0.9758, (1, 1): 0.0291}
    got: dict[tuple[int, int], float] = {}
    for m in re.finditer(r"\[(\d),\s*(\d)\][^\d-]*?(-?\d+(?:\.\d+)?(?:e-?\d+)?)\s*$", out, re.M):
        got[(int(m.group(1)), int(m.group(2)))] = float(m.group(3))
    if set(got) != set(ref):
        return "FAIL", f"saída sem as 4 entradas XOR; lido: {got}"
    classif = all((v >= 0.5) == (a ^ b == 1) for (a, b), v in got.items())
    diffs = {k: round(abs(got[k] - ref[k]), 4) for k in ref}
    detail = "; ".join(f"{a}{b}: {got[(a, b)]:.4f} (ref {ref[(a, b)]}, |d|={diffs[(a, b)]})" for a, b in sorted(ref))
    if not classif:
        return "FAIL", f"classificação XOR errada: {detail}"
    return "PARTIAL", ("classificação XOR correta nas 4 entradas; valores numéricos divergem da referência "
                       f"e não há tolerância acordada (doc 05 §2, T04): {detail}")


def oracle_t05(out: str, case: dict) -> tuple[str, str]:
    exp_lines = (EXPECTED / "teste5_recomendacao.expected.txt").read_text(encoding="utf-8").splitlines()[1:]
    expected = {norm(x) for x in exp_lines if x.strip()}
    after = out.split("Produtos recomendados para voce:", 1)
    if len(after) != 2:
        return "FAIL", "cabeçalho 'Produtos recomendados' ausente"
    got = set()
    probs = []
    for ln in after[1].splitlines():
        m = re.match(r"\s*(.+?)\s+probabilidade:\s*(-?\d+(?:\.\d+)?)", ln)
        if m:
            got.add(norm(m.group(1)))
            probs.append(float(m.group(2)))
    if got == expected and all(0.55 < p <= 1.0 for p in probs):
        return "PASS", ("12 produtos recomendados iguais ao esperado (comparação sem acento), "
                        "probabilidades em (0.55, 1]; entrada derivada (ver relatório)")
    return "FAIL", f"faltam={sorted(expected - got)}, sobram={sorted(got - expected)}"


def oracle_t06(out: str, case: dict) -> tuple[str, str]:
    m = re.search(r"Vetor ordenado:\s*(\[.*?\])", out)
    if m and m.group(1).replace(" ", "") == "[-100,-40,-3,10,70,80]":
        return "PASS", "vetor 10 -3 -40 80 70 -100 ordenado como [-100, -40, -3, 10, 70, 80]"
    return "FAIL", f"vetor ordenado obtido: {m.group(1) if m else None}"


def oracle_t07(out: str, case: dict) -> tuple[str, str]:
    m = re.search(r"Array ordenado:\s*(\[.*?\])", out)
    if m and m.group(1).replace(" ", "") == "[5,12,33,61,98]":
        return "PASS", "array [33, 12, 98, 5, 61] ordenado como [5, 12, 33, 61, 98] (somente a ordenação; TAC avaliado à parte)"
    return "FAIL", f"array obtido: {m.group(1) if m else None}"


# T05: o esperado lista 12 dos 16 produtos; os 4 ausentes (índices 0 Smartphone, 5 Jeans, 9 Micro-ondas,
# 12 Ficção) são os "já comprados". Entrada derivada do esperado, não registrada na base 2026.1.
T05_STDIN = "\n".join(["1", "0", "0", "0", "0", "1", "0", "0", "0", "1", "0", "0", "1", "0", "0", "0"]) + "\n"

CASES = [
    {"id": "T01", "src": "teste1_calculadora_cliente_servidor.minipar", "stdin": "+\n2\n3\n", "oracle": oracle_t01,
     "ports": [5101, 5102], "concurrent": True},
    {"id": "T02", "src": "teste2_fatorial_fibonacci_par.minipar", "stdin": "", "oracle": oracle_t02, "concurrent": True},
    {"id": "T03", "src": "teste3_neuronio.minipar", "stdin": "", "oracle": oracle_t03},
    {"id": "T04", "src": "teste4_rede_neural_xor.minipar", "stdin": "", "oracle": oracle_t04},
    {"id": "T05", "src": "teste5_recomendacao.minipar", "stdin": T05_STDIN, "oracle": oracle_t05},
    {"id": "T06", "src": "teste6_quicksort_classes.minipar", "stdin": "10 -3 -40 80 70 -100\n", "oracle": oracle_t06},
    {"id": "T07", "src": "teste7_quicksort_iterativo_tac.minipar", "stdin": "", "oracle": oracle_t07},
]


def compile_case(case_dir: Path, src: Path, name: str, env: dict) -> dict:
    (case_dir / "output").mkdir(parents=True, exist_ok=True)
    res = run_proc([sys.executable, "-B", str(REPO / "main.py"), str(src), name], case_dir, None, COMPILE_TIMEOUT, env)
    exe = case_dir / "output" / f"{name}.exe"
    res["exe"] = str(exe) if exe.is_file() else None
    res["exe_sha256"] = sha256(exe)
    res["tac_sha256"] = sha256(case_dir / "output" / f"{name}.tac")
    return res


def run_case(case: dict, run_dir: Path, env: dict, attempt: int) -> dict:
    name = case["id"].lower() + (f"_r{attempt}" if attempt else "")
    case_dir = run_dir / name
    case_dir.mkdir(parents=True, exist_ok=True)
    src = TESTS / case["src"]
    record: dict = {"id": case["id"], "attempt": attempt, "source": str(src.relative_to(REPO)),
                    "source_sha256": sha256(src)}
    if case.get("ports") and not ports_free(case["ports"]):
        record.update(status="BLOCKED", reason=f"portas {case['ports']} em uso no loopback; nenhum processo encerrado")
        return record
    comp = compile_case(case_dir, src, name, env)
    record["compile"] = comp
    if comp["timed_out"] or comp["returncode"] != 0 or not comp["exe"]:
        record.update(status="FAIL", reason=f"compilação falhou (exit={comp['returncode']}, timeout={comp['timed_out']})")
        return record
    run = run_proc([comp["exe"]], case_dir, case["stdin"], RUN_TIMEOUT, env)
    record["run"] = run
    if run["timed_out"]:
        record.update(status="FAIL", reason=f"execução excedeu {RUN_TIMEOUT}s")
        return record
    if run["returncode"] != 0:
        record.update(status="FAIL", reason=f"binário terminou com exit={run['returncode']}")
        return record
    status, reason = case["oracle"](run["stdout"], case)
    record.update(status=status, reason=reason)
    return record


def t07_extra_checks(run_dir: Path, env: dict, cxx: str) -> list[dict]:
    """Prova adversarial do TAC (doc 05 §2, T07) e verificação de limites do C++ gerado."""
    checks = []
    base_dir = run_dir / "t07"
    expected_tac = (EXPECTED / "teste7_quicksort_iterativo_tac.expected.tac").read_text(encoding="utf-8")
    gen_tac_path = base_dir / "output" / "t07.tac"
    if gen_tac_path.is_file():
        gen = gen_tac_path.read_text(encoding="utf-8")
        checks.append({"check": "T07-TAC-igual-ao-esperado", "status": "INFO",
                       "reason": f"TAC gerado {'idêntico' if gen.strip() == expected_tac.strip() else 'diferente'} ao .expected.tac"})

    # Mutação: mesmo nome de função, corpo diferente (só retorna o vetor). Um TAC derivado da AST tem de mudar.
    mut_dir = run_dir / "t07_mutado"
    mut_dir.mkdir(parents=True, exist_ok=True)
    mut_src = mut_dir / "t07_mutado.minipar"
    mut_src.write_text(
        "func quicksort_iterativo(arr) {\n    var x = 1;\n    return arr;\n}\n\n"
        "seq {\n    var array = [33, 12, 98, 5, 61];\n    var r = quicksort_iterativo(array);\n"
        "    print(\"Array:\", r);\n}\n", encoding="utf-8")
    comp = compile_case(mut_dir, mut_src, "t07_mutado", env)
    mut_tac = mut_dir / "output" / "t07_mutado.tac"
    if mut_tac.is_file():
        same = mut_tac.read_text(encoding="utf-8").strip() == expected_tac.strip()
        checks.append({"check": "T07-TAC-mutacao", "status": "FAIL" if same else "PASS", "compile_exit": comp["returncode"],
                       "reason": ("programa mutado (mesmo nome, corpo trivial) recebeu o TAC fixo do Quicksort: "
                                  "TAC não é derivado da AST (EXPECTED_QUICKSORT_TAC em src/tac.py)") if same else
                                 "TAC do programa mutado difere do TAC fixo"})
    else:
        checks.append({"check": "T07-TAC-mutacao", "status": "BLOCKED", "reason": "TAC do programa mutado não foi gerado",
                       "compile": comp})

    # Limites: recompilar o C++ gerado pelo compilador com asserções da libstdc++ (sem tocar em src/).
    cpp = base_dir / "output" / "t07.cpp"
    if cpp.is_file():
        exe = base_dir / "output" / "t07_assert.exe"
        cmd = [cxx, "-std=c++20", "-O0", "-g", "-D_GLIBCXX_ASSERTIONS", str(cpp), "-o", str(exe), "-pthread"]
        if os.name == "nt":
            cmd.append("-lws2_32")
        c = run_proc(cmd, base_dir, None, COMPILE_TIMEOUT, env)
        if c["returncode"] != 0:
            checks.append({"check": "T07-limites", "status": "BLOCKED", "reason": "recompilação com _GLIBCXX_ASSERTIONS falhou",
                           "compile": c})
        else:
            r = run_proc([str(exe)], base_dir, "", RUN_TIMEOUT, env)
            ok = r["returncode"] == 0 and not r["timed_out"]
            checks.append({"check": "T07-limites", "status": "PASS" if ok else "FAIL", "run": r,
                           "reason": "C++ gerado roda sem violação com -D_GLIBCXX_ASSERTIONS" if ok else
                           f"C++ gerado aborta com -D_GLIBCXX_ASSERTIONS (exit={r['returncode']}): acesso fora dos limites; "
                           f"stderr: {r['stderr'].strip()[:200]}"})
    return checks


def tool_versions(cxx: str, env: dict) -> dict:
    v = run_proc([cxx, "--version"], REPO, None, 30, env)
    return {"python": sys.version.split()[0], "platform": platform.platform(), "cxx": cxx,
            "cxx_version": (v["stdout"].splitlines() or ["?"])[0]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cxx", default=os.environ.get("CXX") or (str(DEFAULT_GPP) if DEFAULT_GPP.is_file() else "g++"))
    ap.add_argument("--repeat", type=int, default=10,
                    help="execuções dos testes concorrentes T01/T02 (comportamento intermitente já observado)")
    ap.add_argument("--only", default="", help="lista de IDs, ex.: T01,T07")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cxx_path = shutil.which(args.cxx) or args.cxx
    env = dict(os.environ)
    env["CXX"] = cxx_path
    env["PYTHONIOENCODING"] = "utf-8"
    # DLLs do runtime do G++ (ex.: UCRT64) só no PATH deste processo e de seus filhos.
    env["PATH"] = str(Path(cxx_path).parent) + os.pathsep + env.get("PATH", "")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = REPO / "output" / "core01" / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}

    results = []
    for case in CASES:
        if only and case["id"] not in only:
            continue
        attempts = args.repeat if case.get("concurrent") else 1
        for attempt in range(1, attempts + 1) if attempts > 1 else [0]:
            rec = run_case(case, run_dir, env, attempt)
            results.append(rec)
            print(f"{rec['id']}{'#' + str(attempt) if attempt else ''}: {rec['status']} — {rec['reason']}", flush=True)
            if case.get("ports") and attempts > 1:
                time.sleep(1.0)  # deixa os sockets do loopback saírem de uso

    extras = t07_extra_checks(run_dir, env, cxx_path) if (not only or "T07" in only) else []
    for chk in extras:
        print(f"{chk['check']}: {chk['status']} — {chk['reason']}", flush=True)

    # Um caso repetido só é PASS se TODAS as execuções passaram (não declarar estabilidade por um acerto).
    overall: dict[str, str] = {}
    for case_id in dict.fromkeys(r["id"] for r in results):
        sts = [r["status"] for r in results if r["id"] == case_id]
        if all(s == "PASS" for s in sts):
            overall[case_id] = "PASS"
        elif "BLOCKED" in sts and "PASS" not in sts:
            overall[case_id] = "BLOCKED"
        elif len(sts) > 1 and "PASS" in sts:
            overall[case_id] = "FAIL"
            print(f"{case_id} (consolidado): FAIL — intermitente, {sts.count('PASS')}/{len(sts)} execuções PASS")
        else:
            overall[case_id] = sts[0]

    summary = {"generated_at": datetime.now().isoformat(timespec="seconds"), "repo": str(REPO),
               "tools": tool_versions(cxx_path, env), "overall": overall, "results": results, "extra_checks": extras}
    (run_dir / "baseline.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nEvidência: {run_dir.relative_to(REPO) / 'baseline.json'}")
    print(f"Ferramentas: {summary['tools']}")

    statuses = list(overall.values()) + [c["status"] for c in extras if c["status"] != "INFO"]
    if "BLOCKED" in statuses:
        return 2
    return 0 if all(s == "PASS" for s in statuses) else 1


if __name__ == "__main__":
    sys.exit(main())
