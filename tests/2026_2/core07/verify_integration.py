"""CORE-07 integration: official CLI and CORE-08, real loopback worker/failure.

Run from repo root with CXX/PATH configured for the local toolchain.
Evidence is written to output/core07/integration/e2e.json; no physical-host claim.
"""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src import service

SOURCE = '''
func twice(x) { return x * 2; }
func slow(n) { var x=0.0; for(var i=0;i<n;i=i+1){x=x+exp(0.001);} return x; }
var destination=input(); var mode=input();
if(mode=="slow"){var h=fork slow(2000000000) on destination;print(join(h,10000));}
else {var a=fork twice(21) on destination;var b=fork twice(7) on destination;print(join(b),join(a));}
'''
OUT = ROOT / 'output/core07/integration'
OUT.mkdir(parents=True, exist_ok=True)
WORK = Path(tempfile.mkdtemp(prefix='official-', dir=OUT))
records = []


def record(name, **data):
    records.append(dict(name=name, **data))
    (OUT/'e2e.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')


def checked_run(exe, stdin):
    result = subprocess.run([str(exe)], input=stdin, capture_output=True, text=True, timeout=15)
    record('binary', command=result.args, stdin=stdin, exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
    assert (result.returncode, result.stdout, result.stderr) == (0, '14 42\n', ''), records[-1]


def worker(exe, crash=False):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    logfile = WORK / ('crash-worker.log' if crash else 'worker.log')
    log = logfile.open('w', encoding='utf-8')
    command = [str(exe), '--minipar-worker', str(port), '--bind', '127.0.0.1']
    proc = subprocess.Popen(command, stdout=log, stderr=log, stdin=subprocess.DEVNULL)
    try:
        for _ in range(100):
            assert proc.poll() is None, 'worker exited before ready'
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1', port)) == 0: break
            time.sleep(.05)
        else: raise AssertionError('worker readiness timeout')
        destination = f'127.0.0.1:{port}'
        if not crash:
            checked_run(exe, destination+'\nnormal\n')
            assert proc.poll() is None
        else:
            client = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                client.stdin.write(destination+'\nslow\n'); client.stdin.flush()
                for _ in range(200):
                    if 'fn=slow' in logfile.read_text(encoding='utf-8'): break
                    assert client.poll() is None, 'client finished before worker failure'
                    time.sleep(.025)
                else: raise AssertionError('no evidence of pending task on worker')
                proc.terminate(); proc.wait(timeout=5)
                stdout, stderr = client.communicate(timeout=15)
                record('worker_crash', command=command, exit=client.returncode, stdout=stdout, stderr=stderr,
                       worker_log=logfile.read_text(encoding='utf-8'), scope='loopback', status='PASS' if client.returncode==1 and 'WORKER_LOST' in stderr else 'FAIL')
                assert client.returncode == 1 and 'WORKER_LOST' in stderr, records[-1]
            finally:
                if client.poll() is None: client.kill(); client.communicate(timeout=5)
        record('worker', command=command, log=logfile.read_text(encoding='utf-8'), scope='loopback', status='PASS')
    finally:
        if proc.poll() is None: proc.terminate()
        proc.wait(timeout=5); log.close()


def main():
    source = WORK/'program.minipar'; source.write_text(SOURCE, encoding='utf-8')
    command = [sys.executable, '-B', str(ROOT/'main.py'), str(source), 'program']
    compiled = subprocess.run(command, cwd=WORK, capture_output=True, text=True, timeout=120)
    record('official_cli', command=command, source=SOURCE, exit=compiled.returncode, stdout=compiled.stdout, stderr=compiled.stderr)
    assert compiled.returncode == 0, compiled.stderr
    tac = (WORK/'output/program.tac').read_text(encoding='utf-8')
    assert ' = capture 21\n' in tac and ' = fork twice(' in tac and ' = join b\n' in tac
    exe = WORK/'output/program.exe'
    checked_run(exe, 'local\nnormal\n')
    worker(exe)
    worker(exe, crash=True)
    analyzed = service.analyze(SOURCE)
    assert analyzed['ok'], analyzed
    assert list(analyzed['phases']) == list(service.PHASES)
    compiled = service.compile_program(SOURCE)
    assert compiled['ok'], compiled
    assert all(p['status']=='ok' for p in compiled['phases'].values())
    artifacts = {kind:service.get_artifact(compiled['request_id'],kind) for kind in ('cpp','tac','binary')}
    assert all(a['ok'] for a in artifacts.values()), artifacts
    executed = service.execute(compiled['request_id'], 'local\nnormal\n')
    record('core08_same_source', analyze=analyzed, compile=compiled, artifacts=artifacts, execute=executed)
    assert executed['ok'] and executed['stdout']=='14 42\n' and executed['stderr']=='', executed
    record('summary', status='PASS', scope='CLI + API + loopback; physical RUN-03 not assessed', work=str(WORK))
    print('PASS: official CLI, two handles, loopback, pending-worker crash, CORE-08 same source/artifacts')


if __name__ == '__main__':
    main()
