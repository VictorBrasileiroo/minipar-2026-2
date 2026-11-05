"""Launch main.py -> choice 2 -> real loopback HTTP -> native execution."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'output/core09'
OUT.mkdir(exist_ok=True)
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 5000))  # Do not reuse or terminate an existing server.
with tempfile.TemporaryDirectory(dir=ROOT/'output') as folder, (OUT/'http-server.log').open('w', encoding='utf-8') as log:
    Path(folder, 'tests').mkdir()
    Path(folder, 'tests/http.minipar').write_text('print(42);', encoding='utf-8')
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    command = [sys.executable, '-B', str(ROOT/'main.py')]
    proc = subprocess.Popen(command, cwd=folder, env=env, stdin=subprocess.PIPE, stdout=log, stderr=log, text=True, encoding='utf-8')
    try:
        proc.stdin.write('2\n')
        proc.stdin.close()
        for attempt in range(100):
            try:
                with urllib.request.urlopen('http://127.0.0.1:5000/', timeout=1) as response:
                    html = response.read().decode('utf-8')
                    assert response.status == 200 and 'Minipar IDE' in html
                break
            except OSError:
                if proc.poll() is not None:
                    raise RuntimeError('Server exited before HTTP readiness')
                time.sleep(.1)
        else:
            raise RuntimeError('Server did not become ready')
        payload = json.dumps(dict(filename='http.minipar', code='print(42);')).encode()
        request = urllib.request.Request('http://127.0.0.1:5000/api/compile', data=payload, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request, timeout=140) as response:
            result = json.load(response)
        assert result['success'] and '\n42\n' in result['stdout'] and '42' in result['cpp'] and '42' in result['tac'], result
        (OUT/'http.json').write_text(json.dumps(dict(status='PASS', command=command, stdin='2\n', bind='127.0.0.1:5000', source='print(42);', response=result), ensure_ascii=False, indent=2), encoding='utf-8')
        print('main.py -> Web -> real HTTP compile/run: PASS (42)')
    finally:
        proc.terminate()
        proc.wait(timeout=10)
