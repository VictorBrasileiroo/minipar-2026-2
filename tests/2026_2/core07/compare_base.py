"""Comparacao pontual CORE-07 contra origin/dev, sem checkout/merge/alterar a base.

Exporta somente fontes necessarias para output/core07/base-comparison/. T01 e
executado apenas numa copia C++ com bind restrito a loopback: PARTIAL.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/core07/base-comparison'
OUT.mkdir(parents=True, exist_ok=True)
GIT = ['git', '-c', 'safe.directory='+ROOT.as_posix()]
BASE = subprocess.check_output(GIT+['rev-parse', 'origin/dev'], text=True).strip()
CXX = os.environ.get('CXX', 'g++')
ENV = dict(os.environ)
ENV['PATH'] = str(Path(CXX).parent)+os.pathsep+ENV.get('PATH','')
spec = importlib.util.spec_from_file_location('baseline', ROOT/'scripts/baseline_t01_t07.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
report = dict(base=BASE, results=[])


def command(cmd, cwd, stdin='', timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=ENV, input=stdin, text=True, capture_output=True, encoding='utf-8', timeout=timeout)
        return dict(command=list(map(str,cmd)), exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
    except subprocess.TimeoutExpired as e:
        return dict(command=list(map(str,cmd)), exit=None, timeout=True,
                    stdout=(e.stdout or b'').decode('utf-8','replace') if isinstance(e.stdout,bytes) else e.stdout,
                    stderr=(e.stderr or b'').decode('utf-8','replace') if isinstance(e.stderr,bytes) else e.stderr)


def save():
    (OUT/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


files = subprocess.check_output(GIT+['ls-tree','-r','--name-only',BASE,'src','main.py','tests'],text=True).splitlines()
base_dir=OUT/'base'; base_dir.mkdir(exist_ok=True)
for name in files:
    if not (name.startswith('src/') or name=='main.py' or (name.startswith('tests/') and name.count('/')==1 and name.endswith('.minipar'))): continue
    target=base_dir/name
    assert target.resolve().is_relative_to(base_dir.resolve())
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(subprocess.check_output(GIT+['show',BASE+':'+name]))

for variant, repo in [('base',base_dir),('current',ROOT)]:
    work=OUT/variant/'runs'; work.mkdir(parents=True,exist_ok=True)
    for case in [c for c in baseline.CASES if c['id'] in ('T01','T02','T04')]:
        compiled=command([sys.executable,'-B',str(repo/'main.py'),str(repo/'tests'/case['src']),case['id']],work)
        record=dict(variant=variant,case=case['id'],compile=compiled,runs=[])
        report['results'].append(record); save()
        if compiled['exit'] != 0: continue
        cpp=work/'output'/f"{case['id']}.cpp"
        # Compara o corpo legado excluindo apenas o preludio novo.
        body=cpp.read_text(encoding='utf-8').split('int main()',1)[-1]
        record['main_sha256']=hashlib.sha256(body.encode()).hexdigest()
        exe=work/'output'/f"{case['id']}.exe"
        if case['id']=='T01':
            record['scope']='PARTIAL: somente copia C++ com bind loopback; original BLOCKED por bind INADDR_ANY'
            text=cpp.read_text(encoding='utf-8').replace('address.sin_addr.s_addr = INADDR_ANY;', 'address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);')
            copy=work/'output/T01_loopback.cpp';copy.write_text(text,encoding='utf-8')
            exe=work/'output/T01_loopback.exe'
            flags=[CXX,'-std=c++20','-O3',str(copy),'-o',str(exe),'-pthread']
            if os.name=='nt': flags.append('-lws2_32')
            record['loopback_build']=command(flags,work)
            if record['loopback_build']['exit']!=0: continue
        for attempt in range(10 if case['id']=='T02' else 3 if case['id']=='T01' else 1):
            if case['id']=='T01' and not baseline.ports_free(case['ports']):
                record['runs'].append(dict(status='BLOCKED',reason='portas loopback ocupadas'));save();break
            result=command([str(exe)],work,case['stdin'],timeout=10)
            if result['exit']==0:
                result['status'],result['reason']=case['oracle'](result['stdout'],case)
            else: result['status']='FAIL' if result['exit'] is not None else 'BLOCKED'
            record['runs'].append(result);save()
        print(variant,case['id'],[r['status'] for r in record['runs']],flush=True)

save()
print(OUT/'results.json')
