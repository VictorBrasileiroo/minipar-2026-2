"""Verificação do Teste 11 pelo pipeline real: MiniPar -> main.py -> g++ -> binário.

Somente stdlib. O compilador hospedeiro só compila; toda a análise da expressão
é feita pelo programa MiniPar. Este script apenas executa o binário e compara o
stdout com os oráculos de C-T11-v1 §3.12 (casos 1 e 3: saída real do professor;
caso 2: oráculo do contrato) e o `.arm` extraído com o arquivo de referência.

Uso (na raiz do repositório):
    python tests/2026_2/test11/verificar_t11.py
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

from extrair_arm import ExtractionError, extract_arm

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("minicompilador.minipar")
ARM_DIR = Path(__file__).with_name("arm")
EVIDENCE_DIR = Path(__file__).with_name("evidencias")
SOURCES = ROOT / "docs/fontes/teste11"
CONTRACT = ROOT / "docs/02_CONTRATOS_TECNICOS.md"
PROMPT = "Digite uma expressão infixada: "
CASE_1 = "((2+4)*7)-(5*4)"
CASE_2 = "((10 -8*7)+4)*2"

TITLES = {
    "tokens": "🔍 Tokens gerados pelo analisador léxico:",
    "ast": "🌳 Árvore Sintática Abstrata (AST):",
    "tac": "📦 Código de Três Endereços (TAC):",
    "arm": "⚙️ Assembly ARMv7 (CPUlator):",
    "simbolos": "📚 Tabela de Símbolos:",
    "resultado": "🧮 Resultado final da expressão:",
}

# (id, stdin, resultado esperado, linhas que o Assembly precisa conter).
# Casos obrigatórios de C-T11-v1 §3.1 e entradas extras com variação de
# parênteses, operador, precedência, associatividade e desvios de §3.6 item 4.
VALID = [
    ("CASO-1", CASE_1, "22.0", []),
    ("CASO-2", CASE_2, "-84.0", []),
    ("CASO-3", CASE_1, "22.0", []),
    ("EXTRA-1", "(7+8)*3", "45.0", ["    MUL    r4, r2, r3    @ resultado de '((7 + 8) * 3)'"]),
    ("EXTRA-2", "2*3+4*5", "26.0", ["    ADD    r6, r2, r5    @ resultado de '((2 * 3) + (4 * 5))'"]),
    ("EXTRA-3", "100-2-3", "95.0", ["    SUB    r4, r2, r3    @ resultado de '((100 - 2) - 3)'"]),
    ("EXTRA-4", "2-3*4", "-10.0", ["    SUB    r4, r0, r3    @ resultado de '(2 - (3 * 4))'"]),
    ("EXTRA-5", "((1+2)*(3+4))-5", "16.0", []),
    ("EXTRA-6", "  2 * ( 3+4 ) # comentário", "14.0", []),
    ("EXTRA-7", "7", "7.0", ["    MOV    r0, #7"]),
    ("EXTRA-8", "0*5", "0.0", []),
    ("EXTRA-9", "(((((((9)))))))", "9.0", ["    MOV    r0, #9"]),
    ("LDR-1", "300+1", "301.0", ["    LDR    r0, =300", "    MOV    r1, #1"]),
    ("LDR-2", "255*256", "65280.0", ["    MOV    r0, #255", "    LDR    r1, =256"]),
    ("LIMITE-32", "0-2147483647-1", "-2147483648.0", ["    LDR    r1, =2147483647"]),
    ("LIMITE-13-NOS", "1+2+3+4+5+6+7", "28.0", ["    ADD    r12, r10, r11    @ resultado de '((((((1 + 2) + 3) + 4) + 5) + 6) + 7)'"]),
]

# (id, stdin, trecho obrigatório da mensagem). C-T11-v1 §3.1 e §3.6 item 4.
INVALID = [
    ("ERR-VAZIA", "", "entrada vazia"),
    ("ERR-SO-COMENTARIO", "# nada", "entrada vazia"),
    ("ERR-UNARIO", "-5+2", "menos unário"),
    ("ERR-UNARIO-INTERNO", "2*(-3)", "menos unário"),
    ("ERR-DECIMAL", "2.5*2", "decimal"),
    ("ERR-ZERO-ESQUERDA", "010+1", "zero à esquerda"),
    ("ERR-IDENTIFICADOR", "x+1", "identificador"),
    ("ERR-ATRIBUICAO", "x = 2", "identificador"),
    ("ERR-IGUAL", "2=3", "atribuição"),
    ("ERR-DESCONHECIDO", "2@3", "caractere desconhecido"),
    ("ERR-ABRE", "((2+3)*4", "sem ')'"),
    ("ERR-FECHA", "(2+3))", "inesperado"),
    ("ERR-SOBRA", "2 3", "inesperado"),
    ("ERR-INCOMPLETA", "2+", "incompleta"),
    ("ERR-DIVISAO", "8/2", "divisão"),
    ("ERR-PARENTESES-VAZIOS", "()", "esperado número"),
    ("ERR-14-NOS", "1+2+3+4+5+6+7+8", "no máximo 13"),
    ("ERR-CONSTANTE-32", "2147483648+1", "fora do intervalo"),
    ("ERR-CONSTANTE-LONGA", "99999999999", "fora do intervalo"),
    ("ERR-OVERFLOW", "65536*65536", "32 bits"),
    ("ERR-OVERFLOW-NEGATIVO", "0-2147483647-2", "32 bits"),
]

# Regras de extração de C-T11-v1 §3.6 item 2: (id, stdout sintético, erro esperado ou .arm).
EXTRACTION = [
    ("EXT-CRLF", "x\r\n⚙️ Assembly ARMv7 (CPUlator):\r\n.global _start\r\n    b .\r\n\r\nfim\r\n",
     ".global _start\n    b .\n\n"),
    ("EXT-SEM-EMOJI", "Assembly ARMv7 (CPUlator):\n.global _start\n\n", ".global _start\n\n"),
    ("EXT-AUSENTE", "nada\n", "ausente"),
    ("EXT-REPETIDO", "Assembly ARMv7 (CPUlator):\n.global _start\n\nAssembly ARMv7 (CPUlator):\n.global _start\n\n",
     "repetido"),
    ("EXT-VAZIO", "Assembly ARMv7 (CPUlator):\n\n", "vazio"),
    ("EXT-SEM-GLOBAL", "Assembly ARMv7 (CPUlator):\n.text\n\n", ".global _start"),
    ("EXT-SEM-LINHA-VAZIA", "Assembly ARMv7 (CPUlator):\n.global _start\n    b .", "linha vazia"),
]


def compile_program() -> Path:
    proc = subprocess.run([sys.executable, str(ROOT / "main.py"), str(SOURCE), "minicompilador_t11"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ))
    exe = ROOT / "output" / "minicompilador_t11.exe"
    if proc.returncode != 0 or not exe.exists():
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("FAIL: compilação do minicompilador.minipar")
    return exe


def run(exe: Path, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(exe)], input=(stdin + "\n").encode("utf-8"),
                          capture_output=True, timeout=30)


def lines_of(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def sections(lines: list[str]) -> dict[str, list[str]]:
    """Separa o stdout por título de seção; cada seção termina na linha vazia."""
    by_title = {title: key for key, title in TITLES.items()}
    found: dict[str, list[str]] = {}
    current = None
    for line in lines:
        if line in by_title:
            current = by_title[line]
            if current in found:
                raise ValueError(f"seção repetida: {line}")
            found[current] = []
        elif current is not None:
            if line == "":
                current = None
            else:
                found[current].append(line)
    return found


def oracles() -> dict[str, list[str]]:
    """Linhas do stdout a partir de 🔍 Tokens, por expressão (C-T11-v1 §3.12)."""
    reference = lines_of((SOURCES / "Execucao-Saida-okRodounoCPULATOR.txt").read_text(encoding="utf-8"))
    section = CONTRACT.read_text(encoding="utf-8").split("### 3.12 ", 1)[1].split("\n## 4.", 1)[0]
    case_2 = re.search(r"```text\n(.*?)```", section, re.S).group(1)
    return {CASE_1: reference[2:59], CASE_2: lines_of(case_2)}


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    exe = compile_program()
    expected_stdout = oracles()
    reference_arm = lines_of((SOURCES / "Codigo-Assembly-ARMV7.arm").read_text(encoding="utf-8"))
    failures = 0
    total = 0

    def report(case_id: str, problems: list[str]) -> None:
        nonlocal failures, total
        total += 1
        failures += bool(problems)
        print(f"{'FAIL' if problems else 'PASS'} {case_id}" + (f" — {'; '.join(problems)}" if problems else ""))

    for case_id, stdin, expected, arm_lines in VALID:
        proc = run(exe, stdin)
        stdout = proc.stdout.decode("utf-8")
        out = lines_of(stdout)
        found = sections(out)
        problems = []
        if proc.returncode != 0:
            problems.append(f"exit={proc.returncode}")
        if not out or out[0] != PROMPT:
            problems.append("primeira linha não é o prompt")
        if found.get("resultado") != ["➡️  " + expected]:
            problems.append(f"resultado {found.get('resultado')} != {expected}")
        missing = [key for key in TITLES if key not in found]
        if missing:
            problems.append(f"seções ausentes: {missing}")
        try:
            arm = lines_of(extract_arm(stdout))
        except ExtractionError as exc:
            problems.append(f"extração do .arm: {exc}")
            arm = []
        if arm and arm[-1] != "    b .    @ loop infinito para parar o programa":
            problems.append("Assembly não termina em 'b .'")
        problems += [f"Assembly sem a linha {line!r}" for line in arm_lines if line not in arm]
        if stdin in expected_stdout and out[1:] != expected_stdout[stdin]:
            problems.append("stdout difere do oráculo de C-T11-v1 §3.12")
        if stdin == CASE_1 and arm != reference_arm:
            problems.append(".arm difere de docs/fontes/teste11/Codigo-Assembly-ARMV7.arm")
        committed = ARM_DIR / (case_id.lower().replace("-", "") + ".arm")
        if case_id.startswith("CASO-") and (not committed.exists() or committed.read_bytes() != extract_arm(stdout).encode("utf-8")):
            problems.append(f"{committed.relative_to(ROOT).as_posix()} ausente ou diferente da extração atual")
        report(case_id, problems)

    for case_id, stdin, fragment in INVALID:
        proc = run(exe, stdin)
        stdout = proc.stdout.decode("utf-8")
        found = sections(lines_of(stdout))
        problems = []
        if "❌ Erro" not in stdout or fragment not in stdout:
            problems.append(f"mensagem sem '{fragment}'")
        if "resultado" in found or "arm" in found or "tac" in found:
            problems.append("produziu TAC, Assembly ou resultado para entrada inválida")
        report(case_id, problems)

    # T11-03: a execução no CPUlator registrada em evidencias/ vale para estes bytes.
    evidence = (EVIDENCE_DIR / "README.md").read_text(encoding="utf-8")
    for arm_file in sorted(ARM_DIR.glob("*.arm")) + sorted(EVIDENCE_DIR.glob("*.arm")):
        digest = hashlib.sha256(arm_file.read_bytes()).hexdigest()
        report(f"EVID-{arm_file.stem.upper()}",
               [] if digest in evidence else [f"SHA-256 {digest} ausente de evidencias/README.md"])

    for case_id, stdout, expected in EXTRACTION:
        try:
            got = extract_arm(stdout)
            problems = [] if got == expected else [f"extraiu {got!r}"]
        except ExtractionError as exc:
            problems = [] if expected in str(exc) else [f"erro inesperado: {exc}"]
        report(case_id, problems)

    print(f"\n{total - failures}/{total} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
