"""Prova direta do backend CORE-07; nao substitui a CLI nem ignora TAC nela."""
from pathlib import Path
import argparse
import os
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CppCodeGenerator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output_name', nargs='?', default='demo')
    args = parser.parse_args()
    source = args.source.read_text(encoding='utf-8')
    program = Parser(Lexer(source).tokenize()).parse()
    semantic = SemanticAnalyzer()
    if not semantic.analyze(program): return 1
    work = ROOT/'output/core07/repro'
    work.mkdir(parents=True,exist_ok=True)
    previous = Path.cwd()
    try:
        os.chdir(work)
        return 0 if CppCodeGenerator().generate(program,args.output_name,semantic,source) else 1
    finally: os.chdir(previous)


if __name__ == '__main__': sys.exit(main())
