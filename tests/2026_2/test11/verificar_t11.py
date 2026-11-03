"""Verificação do Teste 11 pelo pipeline real: MiniPar -> main.py -> g++ -> binário.

Somente stdlib. O compilador hospedeiro só compila; toda a análise da expressão
é feita pelo programa MiniPar. Este script apenas executa o binário e compara o
stdout com os oráculos de C-T11-v1 §3.12 (casos 1 e 3: saída real do professor).

Uso (na raiz do repositório):
    python tests/2026_2/test11/verificar_t11.py
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("minicompilador.minipar")
REFERENCE_OUTPUT = ROOT / "docs/fontes/teste11/Execucao-Saida-okRodounoCPULATOR.txt"
PROMPT = "Digite uma expressão infixada: "

TITLES = {
    "tokens": "🔍 Tokens gerados pelo analisador léxico:",
    "ast": "🌳 Árvore Sintática Abstrata (AST):",
    "tac": "📦 Código de Três Endereços (TAC):",
    "arm": "⚙️ Assembly ARMv7 (CPUlator):",
    "simbolos": "📚 Tabela de Símbolos:",
    "resultado": "🧮 Resultado final da expressão:",
}

# Seções produzidas nesta entrega (T11-01). ARM e tabela de símbolos: T11-02.
SECTIONS = ("tokens", "ast", "tac", "resultado")

# (id, stdin, resultado esperado). Casos obrigatórios de C-T11-v1 §3.1 e entradas
# extras com variação de parênteses, precedência e associatividade.
VALID = [
    ("CASO-1", "((2+4)*7)-(5*4)", "22.0"),
    ("CASO-2", "((10 -8*7)+4)*2", "-84.0"),
    ("CASO-3", "((2+4)*7)-(5*4)", "22.0"),
    ("EXTRA-1", "(7+8)*3", "45.0"),
    ("EXTRA-2", "2*3+4*5", "26.0"),
    ("EXTRA-3", "100-2-3", "95.0"),
    ("EXTRA-4", "2-3*4", "-10.0"),
    ("EXTRA-5", "((1+2)*(3+4))-5", "16.0"),
    ("EXTRA-6", "  2 * ( 3+4 ) # comentário", "14.0"),
    ("EXTRA-7", "7", "7.0"),
    ("EXTRA-8", "0*5", "0.0"),
]

# (id, stdin, trecho obrigatório da mensagem). C-T11-v1 §3.1.
INVALID = [
    ("ERR-VAZIA", "", "entrada vazia"),
    ("ERR-SO-COMENTARIO", "# nada", "entrada vazia"),
    ("ERR-UNARIO", "-5+2", "menos unário"),
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
]


def compile_program() -> Path:
    env = dict(os.environ)
    proc = subprocess.run([sys.executable, str(ROOT / "main.py"), str(SOURCE), "minicompilador_t11"],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env)
    exe = ROOT / "output" / "minicompilador_t11.exe"
    if proc.returncode != 0 or not exe.exists():
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("FAIL: compilação do minicompilador.minipar")
    return exe


def run(exe: Path, stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(exe)], input=(stdin + "\n").encode("utf-8"),
                          capture_output=True, timeout=30)


def lines_of(raw: bytes) -> list[str]:
    return raw.decode("utf-8").replace("\r\n", "\n").split("\n")


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


def reference_case1() -> dict[str, list[str]]:
    # C-T11-v1 §3.12: oráculo dos casos 1 e 3 = linhas 3–59 da saída do professor.
    lines = REFERENCE_OUTPUT.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    return sections(lines[2:59])


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    exe = compile_program()
    oracle = reference_case1()
    failures = 0

    def report(case_id: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'} {case_id}" + (f" — {detail}" if detail else ""))

    for case_id, stdin, expected in VALID:
        proc = run(exe, stdin)
        out = lines_of(proc.stdout)
        found = sections(out)
        problems = []
        if proc.returncode != 0:
            problems.append(f"exit={proc.returncode}")
        if not out[0].startswith(PROMPT):
            problems.append("prompt ausente")
        if found.get("resultado") != ["➡️  " + expected]:
            problems.append(f"resultado {found.get('resultado')} != {expected}")
        missing = [k for k in SECTIONS if k not in found]
        if missing:
            problems.append(f"seções ausentes: {missing}")
        if stdin == "((2+4)*7)-(5*4)":
            for key in SECTIONS:
                if found.get(key) != oracle[key]:
                    problems.append(f"seção {key} difere da saída do professor")
        report(case_id, not problems, "; ".join(problems))

    for case_id, stdin, fragment in INVALID:
        proc = run(exe, stdin)
        text = "\n".join(lines_of(proc.stdout))
        found = sections(lines_of(proc.stdout))
        problems = []
        if "❌ Erro" not in text or fragment not in text:
            problems.append(f"mensagem sem '{fragment}'")
        if "resultado" in found or "arm" in found:
            problems.append("produziu resultado ou Assembly para entrada inválida")
        report(case_id, not problems, "; ".join(problems))

    print(f"\n{len(VALID) + len(INVALID) - failures}/{len(VALID) + len(INVALID)} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
