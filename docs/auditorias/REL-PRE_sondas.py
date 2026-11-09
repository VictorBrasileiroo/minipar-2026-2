"""Sondas documentais REL-PRE; não modifica compilador, runtime ou fontes oficiais.

Uso: .venv/Scripts/python.exe -B docs/auditorias/REL-PRE_sondas.py
Requer CXX e DLLs da toolchain no PATH do processo. Artefatos em output/rel_pre/.
Não decide aceite: divergência contra a referência histórica do XOR é registrada.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]


def xor_model():
    # Tradução independente escalar: mesmos pesos, ordem de amostras e atualizações.
    weights = [[0.2, -0.4, 0.0], [-0.3, 0.6, 0.1], [0.7, 0.5, -0.2]]
    output = [0.4, -0.5, 0.3, 0.0]
    samples = [(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]
    def sigmoid(x):
        return 1 / (1 + math.exp(0 - x))
    def forward(x1, x2):
        h = [sigmoid(x1 * w[0] + x2 * w[1] + w[2]) for w in weights]
        return h, sigmoid(h[0] * output[0] + h[1] * output[1] + h[2] * output[2] + output[3])
    for _ in range(20000):
        for x1, x2, target in samples:
            h, predicted = forward(x1, x2)
            delta = (target - predicted) * (predicted * (1 - predicted))
            previous = output[:3]
            for i in range(3):
                output[i] = output[i] + ((h[i] * delta) * 0.5)
            output[3] = output[3] + delta * 0.5
            for i in range(3):
                hidden_delta = (delta * previous[i]) * (h[i] * (1 - h[i]))
                weights[i][0] = weights[i][0] + ((x1 * hidden_delta) * 0.5)
                weights[i][1] = weights[i][1] + ((x2 * hidden_delta) * 0.5)
                weights[i][2] = weights[i][2] + hidden_delta * 0.5
    return [forward(a, b)[1] for a, b, _ in samples]


def main():
    out = ROOT / 'output' / 'rel_pre' / datetime.now().strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True, exist_ok=False)
    report = {'base': '8d07433', 'python': platform.python_version(), 'checks': {}}
    def run(cmd, cwd=ROOT, stdin=None):
        p = subprocess.run(cmd, cwd=cwd, input=stdin, text=True, encoding='utf-8',
                           errors='replace', capture_output=True, timeout=180)
        return {'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    def compile_and_run(source, name, stdin=''):
        directory = out / name
        directory.mkdir()
        build = run([sys.executable, '-B', str(ROOT / 'main.py'), str(ROOT / source), name], directory)
        exe = directory / 'output' / (name + '.exe')
        if build['exit'] or not exe.is_file():
            raise RuntimeError(build)
        execution = run([str(exe)], directory, stdin)
        return {'source': source, 'source_sha256': hashlib.sha256((ROOT / source).read_bytes()).hexdigest(),
                'binary_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(), 'build': build,
                'execution': execution}
    xor = compile_and_run('tests/teste4_rede_neural_xor.minipar', 'xor')
    report['xor'] = xor
    got = [float(v) for v in re.findall(r'Predicted Output:\s*([0-9.eE+-]+)', xor['execution']['stdout'])]
    model = xor_model()
    reference = [float(v) for v in re.findall(r'Predicted Output:\s*([0-9.eE+-]+)',
                 (ROOT / 'tests/expected_results/teste4_rede_neural_xor.expected.txt').read_text())]
    if len(got) != 4 or len(reference) != 4:
        raise RuntimeError('XOR sem quatro resultados')
    rows = []
    for y, m, r in zip(got, model, reference):
        # std::ostream defaultfloat: 6 algarismos significativos, meia unidade final.
        rounding = 0.5 * 10 ** (math.floor(math.log10(abs(m))) - 5)
        rows.append({'native': y, 'model': m, 'reference': r,
                     'absolute_difference': abs(y-r), 'relative_difference': abs(y-r)/abs(r),
                     'model_difference': abs(y-m), 'print_rounding_bound': rounding,
                     'matches_model': abs(y-m) <= rounding + 1e-12,
                     'matches_reference_4_decimals': abs(y-r) <= 0.00005 + rounding})
    xor['comparison'] = rows
    report['checks']['xor_model'] = all(r['matches_model'] for r in rows) and xor['execution']['exit'] == 0
    report['checks']['xor_classification'] = all((v >= 0.5) == bool(t) and math.isfinite(v) and 0 <= v <= 1
                                               for v, t in zip(got, [0, 1, 1, 0]))
    xor['historical_numeric_status'] = 'PASS' if all(r['matches_reference_4_decimals'] for r in rows) else 'FAIL'
    xor['acceptance_status'] = 'PARTIAL'
    spec = importlib.util.spec_from_file_location('t10', ROOT / 'tests/2026_2/test10/run_t10.py')
    t10 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(t10)
    t10_record = compile_and_run('tests/2026_2/test10/teste10_dois_fractais.minipar', 't10',
                                 'seq\n1000\n50\n20\n100\n4\n' + 'local\n' * 6)
    report['t10_degree4'] = t10_record
    text = t10_record['execution']['stdout']
    carpet = text.split('=== SIERPINSKI grau=4 ===\n', 1)[1].split('\n=== FIM SIERPINSKI ===', 1)[0].splitlines()
    t10_record['dimensions'] = [len(carpet), len(carpet[0])]
    t10_record['filled_cells'] = sum(line.count('#') for line in carpet)
    report['checks']['t10_degree4'] = (t10_record['execution']['exit'] == 0 and
        carpet == t10.sierpinski_recursivo(4) and t10_record['filled_cells'] == 4096 and
        len(carpet) == 81 and all(len(line) == 81 for line in carpet))
    report['status'] = 'PASS' if all(report['checks'].values()) else 'FAIL'
    # Retira caminhos pessoais dos comandos/diagnósticos antes de versionar o JSON.
    def sanitize(value):
        if isinstance(value, dict):
            return {key: sanitize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, str):
            for path, replacement in [(str(ROOT), '<repo>'), (ROOT.as_posix(), '<repo>'),
                                      (str(Path.home()), '<home>')]:
                value = value.replace(path.replace('\\', '\\\\'), replacement).replace(path, replacement)
        return value
    serialized = json.dumps(sanitize(report), ensure_ascii=False, indent=2)
    (out / 'results.json').write_text(serialized + '\n', encoding='utf-8')
    print(serialized)
    print('Evidence:', (out / 'results.json').relative_to(ROOT))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
