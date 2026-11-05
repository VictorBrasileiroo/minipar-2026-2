"""Collect already executed checks; refuses to report PASS without their logs."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def log(path):
    data = (ROOT/path).read_bytes()
    return data.decode('utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8')


interfaces = load('output/core09/interfaces.json')
assert interfaces['tests'] == 14 and interfaces['failures'] == interfaces['errors'] == 0
service = load('output/core08/tests-final.json')
assert service['tests'] == 36 and service['failures'] == service['errors'] == 0
checks = []
for name, path, count in [('CORE-02', 'output/core09-core02.log', 5), ('CORE-06', 'output/core09-core06.log', 54), ('CORE-07', 'output/core09-core07.log', 17)]:
    text = log(path)
    assert re.search(r'Ran '+str(count)+r' tests.*?\nOK\b', text, re.S), path
    checks.append(dict(suite=name, tests=count, status='PASS', log=path, excerpt=text[text.rfind('Ran '):].strip()))
baseline = load('output/core01/run-20261105-155948/baseline.json')
http = load('output/core09/http.json')
http['response'].pop('cpp')
http['response'].pop('tac')
assert 'CLI + old Web smoke: PASS' in log('output/core09-legacy-smoke.log')
report = dict(base_commit='59ea77d093deb35877243da3383bcd7036e16448', interfaces=interfaces,
    baseline_probes=load('output/core09/baseline-probes.json'), http=http,
    core=checks, service=service, legacy_smoke='PASS', inherited_baseline=dict(tools=baseline['tools'], overall=baseline['overall']),
    visual=dict(status='BLOCKED', reason='openBrowserPage failed; CUA: The browser access host is unavailable'),
    initial_run=dict(status='FAIL reproduced', log='output/core09-before-detail.log', summary='7 tests: 2 failures, 1 error; stale cpp/tac, menu SystemExit; initial runtime bounds probe exposed inherited core behavior and was replaced with controlled substr failure. See baseline_probes for actual native returncode defect.'),
    hashes={})
report['validation_scope'] = dict(current='CORE-09: 14 tests; filename validation and legitimate endpoints',
    historical='CORE-02/06/07/08, baseline, HTTP and legacy smoke retained from the initial execution; not rerun in this review')
report['privacy'] = dict(repo='<REPO>', toolchain='<TOOLCHAIN>', other_local_paths='<LOCAL>/<basename>',
    note='Local prefixes anonymized; sources, flags, output, oracles and hashes retained.')
for path in ['main.py', 'app.py', 'menu.py', 'static/js/script.js'] + [str(p.relative_to(ROOT)).replace('\\','/') for p in Path(__file__).parent.glob('*.py')]:
    report['hashes'][path] = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def anonymize(value):
    if isinstance(value, dict):
        return {key: anonymize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [anonymize(item) for item in value]
    if not isinstance(value, str):
        return value
    for prefix, replacement in [(str(ROOT), '<REPO>'), (str(Path(interfaces['compiler']).parent), '<TOOLCHAIN>')]:
        for variant in sorted({prefix, prefix.replace('\\', '/'), prefix.replace('\\', '\\\\')}, key=len, reverse=True):
            value = re.sub(re.escape(variant), lambda _: replacement, value, flags=re.I)
    # Also redact any external local path that appears in a diagnostic.
    return re.sub(r'''[A-Za-z]:[\\/]+[^\s'"<>,;\]\)]+''',
                  lambda match: '<LOCAL>/' + re.split(r'[\\/]+', match.group())[-1], value)


serialized = json.dumps(anonymize(report), ensure_ascii=False, indent=2)+'\n'
assert not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]', serialized), 'Unredacted absolute path'
(ROOT/'docs/auditorias/CORE-09_RESULTADOS.json').write_text(serialized, encoding='utf-8')
print('CORE-09 evidence recorded from verified logs.')
