"""Extrai o Assembly ARMv7 do stdout do MiniCompilador para um arquivo `.arm`.

Regras de C-T11-v1 §3.6 item 2 (as mesmas do download da Web, C-WEB-v1 §1.7):
o bloco é copiado literalmente, da linha seguinte ao título terminado em
`Assembly ARMv7 (CPUlator):` até a primeira linha vazia. O `\\r` do fim de cada
linha é removido antes de reconhecer e copiar. O script não analisa, completa
nem reescreve o Assembly.

Uso (na raiz do repositório):
    python tests/2026_2/test11/extrair_arm.py SAIDA.txt CASO.arm
    python tests/2026_2/test11/extrair_arm.py --casos tests/2026_2/test11/arm
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

TITLE_SUFFIX = "Assembly ARMv7 (CPUlator):"

# C-T11-v1 §3.1: as três execuções obrigatórias do mesmo binário.
CASES = {
    "caso1": "((2+4)*7)-(5*4)",
    "caso2": "((10 -8*7)+4)*2",
    "caso3": "((2+4)*7)-(5*4)",
}


class ExtractionError(ValueError):
    pass


def extract_arm(stdout: str) -> str:
    lines = [line[:-1] if line.endswith("\r") else line for line in stdout.split("\n")]
    titles = [i for i, line in enumerate(lines) if line.endswith(TITLE_SUFFIX)]
    if not titles:
        raise ExtractionError("título do Assembly ausente")
    if len(titles) > 1:
        raise ExtractionError("título do Assembly repetido")
    block = []
    for line in lines[titles[0] + 1:]:
        if line == "":
            break
        block.append(line)
    else:
        raise ExtractionError("bloco do Assembly sem a linha vazia que o fecha")
    if not block:
        raise ExtractionError("bloco do Assembly vazio")
    if block[0] != ".global _start":
        raise ExtractionError("bloco do Assembly não começa com .global _start")
    # Como o arquivo de referência: uma instrução por linha e uma linha em branco no fim.
    return "\n".join(block) + "\n\n"


def write_arm(stdout: str, path: Path) -> str:
    arm = extract_arm(stdout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(arm.encode("utf-8"))
    return arm


def generate_cases(directory: Path) -> None:
    # Import tardio: o modo de arquivo único não precisa compilar nada.
    from verificar_t11 import compile_program, run

    exe = compile_program()
    for name, expression in CASES.items():
        proc = run(exe, expression)
        if proc.returncode != 0:
            raise SystemExit(f"FAIL: {name} terminou com código {proc.returncode}")
        stdout = proc.stdout.decode("utf-8")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{name}.stdout.txt").write_bytes(stdout.replace("\r\n", "\n").encode("utf-8"))
        write_arm(stdout, directory / f"{name}.arm")
        print(f"{name}: {expression} -> {directory / (name + '.arm')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("saida", nargs="?", type=Path, help="arquivo com o stdout do MiniCompilador")
    parser.add_argument("arm", nargs="?", type=Path, help="arquivo .arm de destino")
    parser.add_argument("--casos", type=Path, metavar="DIR",
                        help="compila, executa os três casos obrigatórios e grava casoN.arm e casoN.stdout.txt")
    args = parser.parse_args()
    try:
        if args.casos is not None:
            generate_cases(args.casos)
        elif args.saida is not None and args.arm is not None:
            write_arm(args.saida.read_bytes().decode("utf-8"), args.arm)
        else:
            parser.error("informe SAIDA e ARM, ou --casos DIR")
    except ExtractionError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
