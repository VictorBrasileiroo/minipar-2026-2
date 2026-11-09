"""Reproduce old Web defects using a read-only Git snapshot and real compilation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
revision = sys.argv[1] if len(sys.argv) > 1 else '59ea77d'
source = subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(), 'show', revision+':app.py'], cwd=ROOT).decode('utf-8')
main_source = subprocess.check_output(['git', '-c', 'safe.directory='+ROOT.as_posix(), 'show', revision+':main.py'], cwd=ROOT).decode('utf-8')
namespace = dict(__name__='app', __file__=str(ROOT/'app.py'))
exec(compile(source, str(ROOT/'app.py'), 'exec'), namespace)
os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')
os.environ['PYTHONPATH'] = str(ROOT/'src') + os.pathsep + str(ROOT)
records = []
previous = Path.cwd()
try:
    with tempfile.TemporaryDirectory(dir=ROOT/'output') as folder:
        os.chdir(folder)
        for name in ('output', 'temp_code', 'tests'):
            Path(name).mkdir()
        Path('main.py').write_text(main_source, encoding='utf-8')
        with namespace['app'].test_client() as client:
            def request(code):
                return client.post('/api/compile', json=dict(code=code, filename='baseline.minipar')).get_json()
            good = request('print(6 * 7);')
            assert good['success'] and '\n42\n' in good['stdout'], good
            bad = request('print("broken')
            assert not bad['success'] and bad['cpp'] == good['cpp'] and bad['tac'] == good['tac'], bad
            records.append(dict(case='stale artifacts', status='FAIL reproduced', source='print("broken', success=bad['success'], same_cpp=True, same_tac=True))
            bad = request('print("before failure"); print(substr("abc", 9, 1));')
            assert bad['success'] and 'Erro de execucao' in bad['stdout'], bad
            records.append(dict(case='native error reported as success', status='FAIL reproduced', success=bad['success'], stdout=bad['stdout'], stderr=bad['stderr']))
        os.chdir(previous)
finally:
    os.chdir(previous)
out = ROOT/'output/core09'
out.mkdir(exist_ok=True)
(out/'baseline-probes.json').write_text(json.dumps(dict(revision=revision, records=records), ensure_ascii=False, indent=2), encoding='utf-8')
print('Two original Web defects reproduced with real native builds.')
