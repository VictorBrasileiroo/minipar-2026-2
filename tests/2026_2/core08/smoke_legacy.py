"""Smoke CLI and old Flask test client, isolated cwd, no listening server."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/core08/legacy'
OUT.mkdir(parents=True,exist_ok=True)


def main():
    env=os.environ.copy()
    env['PATH']=str(Path(sys.executable).parent)+os.pathsep+str(Path(env['CXX']).parent)+os.pathsep+env.get('PATH','')
    env['PYTHONIOENCODING']='utf-8'
    (OUT/'main.py').write_text('import runpy\nrunpy.run_path('+repr(str(ROOT/'main.py'))+',run_name="__main__")\n',encoding='utf-8')
    (OUT/'smoke.minipar').write_text('print(5);\n',encoding='utf-8')
    command=[sys.executable,'-B',str(ROOT/'main.py'),str(OUT/'smoke.minipar'),'terminal_smoke']
    build=subprocess.run(command,cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
    assert build.returncode==0,build.stderr
    run=subprocess.run([str(OUT/'output/terminal_smoke.exe')],cwd=OUT,env=env,capture_output=True,text=True,timeout=5)
    assert (run.returncode,run.stdout,run.stderr)==(0,'5\n',''),run
    invalid=OUT/'invalid.minipar'; invalid.write_text('print("bad'+'\\',encoding='utf-8')
    bad=subprocess.run([sys.executable,'-B',str(ROOT/'main.py'),str(invalid),'invalid_smoke'],cwd=OUT,env=env,capture_output=True,text=True,timeout=5)
    assert bad.returncode==1 and '[ERRO LEXICO]' in bad.stderr and 'Traceback' not in bad.stderr,bad
    script='''import sys,json
sys.path.insert(0,sys.argv[1])
from app import app
with app.test_client() as client:
 assert client.get('/').status_code==200
 response=client.post('/api/compile',json=dict(code='print(5);\\n',filename='web_smoke.minipar'))
 data=response.get_json()
 assert response.status_code==200 and data['success'],data
 assert '\\n5\\n' in data['stdout'] and data['cpp'] and data['tac'],data
 print(json.dumps(data,ensure_ascii=False))
'''
    web=subprocess.run([sys.executable,'-B','-c',script,str(ROOT)],cwd=OUT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=35)
    (OUT/'web.json').write_text(web.stdout,encoding='utf-8')
    assert web.returncode==0,web.stderr
    report=dict(status='PASS',terminal=dict(command=command,stdout=run.stdout,stderr=run.stderr,exit_code=run.returncode,compile_stdout=build.stdout),
        invalid_cli=dict(exit_code=bad.returncode,stderr=bad.stderr),web=dict(exit_code=web.returncode,method='Flask test_client; subprocess compilation and execution real; no network server'))
    (OUT/'smoke.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CLI + old Web smoke: PASS')


if __name__=='__main__': main()
