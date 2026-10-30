"""Reproducoes dirigidas: cache contextual e pendencia de retorno implicito.

Mede tempo real de analise em subprocesso limitado; nao executa tarefas FJ.
Uso: python -B tests/2026_2/core0405/measure_final_review.py --output output/metrics.json
"""
from contextlib import redirect_stderr
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer


def chain(depth):
    source = 'func g0(x){return 1;}\n'
    for n in range(1, depth + 1):
        source += f'func g{n}(x){{return g{n-1}(x)+g{n-1}([x])+g{n-1}([x,x]);}}\n'
    return source + f'func t(n){{return g{depth}(n);}}var k=fork t(1);'


def measure(source):
    tree = Parser(Lexer(source).tokenize()).parse()
    sem = SemanticAnalyzer()
    err = io.StringIO()
    start = perf_counter()
    with redirect_stderr(err):
        ok = sem.analyze(tree)
    return dict(seconds=perf_counter() - start, accepted=ok,
                diagnostics=err.getvalue(), contexts=len(sem._function_cache),
                unresolved=sem.unresolved_fj,
                source_sha256=hashlib.sha256(source.encode()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depth', type=int, action='append')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', type=int)
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(measure(chain(args.worker))))
        return
    results = []
    for depth in args.depth or [10, 16]:
        try:
            process = subprocess.run([sys.executable, '-B', __file__, '--worker', str(depth)],
                                     cwd=ROOT, capture_output=True, text=True, timeout=90)
            if process.returncode:
                raise RuntimeError(process.stderr)
            result = dict(depth=depth, **json.loads(process.stdout))
        except subprocess.TimeoutExpired:
            result = dict(depth=depth, status='BLOCKED', reason='timeout 90s')
        results.append(result)
        print(json.dumps(result), flush=True)
    source = 'func f(x){if(x>0){return 1;}}print(join(fork f(0))+1);'
    implicit = dict(source=source, **measure(source))
    implicit['status'] = 'KNOWN_LIMITATION' if implicit['accepted'] else 'REJECTED'
    print('implicit_none: ' + json.dumps(implicit), flush=True)
    data = dict(python=sys.version, timings=results, implicit_none=implicit,
                timing_scope='semantic analysis only; parsing outside timer',
                semantic_sha256=hashlib.sha256((ROOT / 'src/semantic.py').read_text(encoding='utf-8').encode()).hexdigest())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(not result.get('accepted', False) for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
