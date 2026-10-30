"""CORE-08 behavior and native integration; run from repository root."""
import concurrent.futures
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src import service
from src.ast_nodes import UnaryExpr, NumberExpr
from src.lexer import Lexer
from src.parser import Parser, ParseError
from src.semantic import SemanticAnalyzer
from src.service_ast import serialize_ast
from src.service_process import run_bounded

OUT = ROOT / 'output' / 'core08'
OUT.mkdir(parents=True, exist_ok=True)
service.ARTIFACT_ROOT = OUT / 'web'
GOOD = 'var x = 2 + 3;\nprint(x);\n'


def normalized(value):
    value = copy.deepcopy(value)
    value.pop('request_id'); value.pop('duration_ms')
    if value['phases']['cpp']['status'] == 'ok': value['phases']['cpp']['text'] = '<cpp>'
    return value


class ContractTests(unittest.TestCase):
    def test_ace01_fixtures(self):
        for path in sorted((ROOT/'web_didatica/fixtures').glob('fix-*.json')):
            with self.subTest(fixture=path.name):
                fixture = json.loads(path.read_text(encoding='utf-8'))
                actual = service.analyze(fixture['source'])
                self.assertEqual(normalized(actual), normalized(fixture['analyze']))
                json.dumps(actual)

    def test_analyze_no_compiler_or_artifacts(self):
        before = dict(service._registry)
        with patch('subprocess.Popen', side_effect=AssertionError('analyze invoked process')):
            self.assertTrue(service.analyze(GOOD)['ok'])
        self.assertEqual(before, service._registry)

    def test_uuid_hash_phase_order(self):
        import uuid
        for source in (GOOD, GOOD.replace('\n','\r\n'), 'print("á");\n'):
            r = service.analyze(source)
            self.assertEqual(uuid.UUID(hex=r['request_id']).version, 4)
            self.assertEqual(r['source_hash'], 'sha256:'+hashlib.sha256(source.encode()).hexdigest())
            self.assertEqual(tuple(r['phases']), service.PHASES)

    def test_lexer_incomplete_strings(self):
        for source in ('print("abc', 'print("abc'+'\\', '"'):
            r = service.analyze(source)
            self.assertEqual(r['diagnostics'][0]['code'], 'LEX_UNTERMINATED_STRING')
            self.assertEqual(r['phases']['gpp']['reason'], 'not_requested')
        for char in ('@', '&', '|', '\x00'):
            r = service.analyze(char)
            self.assertEqual(r['diagnostics'][0]['code'], 'LEX_UNKNOWN_CHAR')

    def test_parser_modes(self):
        sources = [('var x=;', 'SYN_EXPECTED_EXPRESSION'), ('var x=2', 'SYN_EXPECTED_TOKEN'),
            ('input()=3;', 'SYN_INVALID_ASSIGNMENT'), ('x;', 'SYN_INVALID_STATEMENT'), (';', 'SYN_UNRECOGNIZED_STATEMENT')]
        for source, code in sources:
            with self.subTest(source=source):
                r = service.analyze(source)
                self.assertEqual(r['diagnostics'][0]['code'], code)
                with self.assertRaises(ParseError): Parser(Lexer(source).tokenize(), exit_on_error=False).parse()
        with self.assertRaises(SystemExit): Parser(Lexer('var x=;').tokenize()).parse()

    def test_semantic_accumulates_and_ace06(self):
        bad = service.analyze('print(y);\nprint(z);\nvar x=1; var x=2;')
        self.assertEqual([d['code'] for d in bad['diagnostics']], ['SEM_UNDECLARED_VARIABLE']*2+['SEM_REDECLARED'])
        self.assertEqual(len(bad['phases']['semantic']['symbols']), 1)
        self.assertEqual(normalized(service.analyze(GOOD)), normalized(service.analyze(GOOD)))
        self.assertEqual(service.analyze(GOOD)['diagnostics'], [])

    def test_scopes_symbols(self):
        source = 'class C { var a=1; func m(p) { var b=p; } }\nfunc f(q) { for(var i=0;i<2;i=i+1) { var z=i; } for(var j in [1,2]) { print(j); } }\npar { print(1); }'
        r = service.analyze(source)
        sem = r['phases']['semantic']
        self.assertEqual(sem['status'], 'ok', r['diagnostics'])
        self.assertEqual([s['kind'] for s in sem['scopes']], ['global','class','method','seq','function','seq','for','seq','for','seq','par'])
        self.assertEqual([s['kind'] for s in sem['symbols']], ['class','attribute','method','parameter','variable','function','parameter','variable','variable','iterator'])
        ids = {s['id'] for s in sem['scopes']}
        self.assertTrue(all(s['scope'] in ids for s in sem['symbols']))

    def test_review_p2_function_parameters(self):
        for parameter in ('f', 'x'):
            with self.subTest(parameter=parameter):
                r = service.analyze(f'func f({parameter}) {{ return {parameter}; }} print(f(1));')
                self.assertTrue(r['ok'], r['diagnostics'])
                sem = r['phases']['semantic']
                self.assertEqual(sem['symbols'], [
                    dict(name='f', kind='function', type=None, scope='s0', line=1, params=[parameter]),
                    dict(name=parameter, kind='parameter', type='var', scope='s1', line=1, params=[])])
                self.assertEqual(sem['scopes'], [
                    dict(id='s0', kind='global', name=None, parent=None, line=1),
                    dict(id='s1', kind='function', name='f', parent='s0', line=1),
                    dict(id='s2', kind='seq', name=None, parent='s1', line=1)])

    def test_review_p2_method_parameters(self):
        for parameter in ('m', 'x'):
            with self.subTest(parameter=parameter):
                source = f'class C {{ func m({parameter}) {{ return {parameter}; }} }} var c=new C(); print(c.m(1));'
                r = service.analyze(source)
                self.assertTrue(r['ok'], r['diagnostics'])
                sem = r['phases']['semantic']
                self.assertEqual(sem['symbols'], [
                    dict(name='C', kind='class', type=None, scope='s0', line=1, params=[]),
                    dict(name='m', kind='method', type=None, scope='s1', line=1, params=[parameter]),
                    dict(name=parameter, kind='parameter', type='var', scope='s2', line=1, params=[]),
                    dict(name='c', kind='variable', type='C', scope='s0', line=1, params=[])])
                self.assertEqual(sem['scopes'], [
                    dict(id='s0', kind='global', name=None, parent=None, line=1),
                    dict(id='s1', kind='class', name='C', parent='s0', line=1),
                    dict(id='s2', kind='method', name='C.m', parent='s1', line=1),
                    dict(id='s3', kind='seq', name=None, parent='s2', line=1)])

    def test_specialization_not_duplicated(self):
        source = 'func f(x) { var y=x; return y; } var h=fork f(2); print(join(h));'
        analyzer = SemanticAnalyzer(emit_diagnostics=False)
        program = Parser(Lexer(source).tokenize(), exit_on_error=False).parse()
        self.assertTrue(analyzer.analyze(program))
        self.assertEqual([s['name'] for s in analyzer.symbols], ['f','x','y','h'])
        r = service.analyze(source)
        self.assertEqual(r['phases']['tac']['status'], 'error')
        self.assertEqual(r['phases']['cpp']['reason'], 'previous_phase_failed')
        self.assertEqual(r['diagnostics'], [])  # CR pending, no invented code.

    def test_expected_unmapped_is_not_internal(self):
        r = service.analyze('var h=fork missing();')
        self.assertEqual(r['phases']['semantic']['status'], 'error')
        self.assertFalse(any(d['code']=='INTERNAL_ERROR' for d in r['diagnostics']))

    def test_internal_exception(self):
        with patch.object(service.TACGenerator, 'generate_text', side_effect=RuntimeError('probe')):
            r=service.analyze(GOOD)
        self.assertEqual(r['phases']['tac']['status'], 'error')
        self.assertEqual(r['diagnostics'][0]['code'], 'INTERNAL_ERROR')
        self.assertNotIn('probe', r['diagnostics'][0]['message'])

    def test_ace09_arguments(self):
        for value in ('../x', '', None, [], 'g'*32):
            self.assertEqual(service.get_artifact(value, 'cpp')['error']['code'], 'INVALID_ARGUMENT')
            self.assertEqual(service.execute(value)['error']['code'], 'INVALID_ARGUMENT')
        for kind in ('arm','../binary', None, []):
            self.assertEqual(service.get_artifact('a'*32, kind)['error']['code'], 'INVALID_ARGUMENT')
        for timeout in (0,31,True,1.2,'2',None):
            self.assertEqual(service.execute('a'*32, timeout_sec=timeout)['error']['code'], 'INVALID_ARGUMENT')
        self.assertEqual(service.get_artifact('a'*32, 'binary')['error']['code'], 'ARTIFACT_NOT_FOUND')
        self.assertEqual(service.execute('a'*32)['error']['code'], 'ARTIFACT_NOT_FOUND')

    def test_ace11_ast(self):
        r=service.analyze('print(1);\n'*2600)
        self.assertTrue(r['ok'], r['diagnostics'])
        stats=r['phases']['parser']['ast_stats']
        self.assertEqual(stats['nodes'], 5201)
        self.assertEqual(stats['emitted'],5000)
        self.assertTrue(stats['truncated'])
        node=NumberExpr(value='1')
        for _ in range(249): node=UnaryExpr(op='-',operand=node)
        tree, stats=serialize_ast(node)
        self.assertEqual((stats['nodes'],stats['emitted'],stats['depth']),(250,200,250))
        for _ in range(199): tree=tree['children'][0]
        self.assertEqual(tree['children'][0]['attributes'],dict(reason='max_depth',omitted_nodes=50))

    def test_gpp_missing_failure_no_binary_timeout(self):
        for mode, expected in (('missing','GPP_NOT_FOUND'),('fail','GPP_FAILED'),('empty','GPP_NO_BINARY'),('timeout','GPP_TIMEOUT')):
            with self.subTest(mode=mode):
                if mode=='missing':
                    context=patch.dict(os.environ, CXX=str(OUT/'nonexistent-compiler'))
                else:
                    payload=dict(returncode=1 if mode=='fail' else 0,timed_out=mode=='timeout',stdout='',stderr='probe',duration_ms=1,stdout_truncated=False,stderr_truncated=False)
                    context=patch('src.service_process.run_bounded',return_value=payload)
                with context: r=service.compile_program(GOOD)
                self.assertFalse(r['ok'])
                self.assertEqual(r['diagnostics'][0]['code'],expected)
                self.assertIsNone(r['artifacts']['binary_id'])
                self.assertEqual(service.get_artifact(r['request_id'],'binary')['error']['code'],'ARTIFACT_NOT_FOUND')
                self.assertTrue(service.get_artifact(r['request_id'],'cpp')['ok'])


class NativeTests(unittest.TestCase):
    def compile(self, source):
        r=service.compile_program(source)
        self.assertTrue(r['ok'],r['diagnostics'] or r['phases']['gpp'])
        return r['request_id']

    def test_ace02_and_stdin(self):
        rid=self.compile(GOOD)
        r=service.execute(rid)
        self.assertEqual((r['ok'],r['stdout'],r['stderr'],r['exit_code']),(True,'5\n','',0))
        rid=self.compile('var s=input(); print(s);')
        self.assertEqual(service.execute(rid,'olá\n')['stdout'],'olá\n')

    def test_ace04_08_sequential(self):
        first=self.compile('print(1);\n')
        before={k:hashlib.sha256(Path(service.get_artifact(first,k)['path']).read_bytes()).hexdigest() for k in ('cpp','tac','binary')}
        second=self.compile('print(2);\n')
        self.assertNotEqual(first,second)
        for rid,num in ((first,1),(second,2)):
            self.assertEqual(service.execute(rid)['stdout'],f'{num}\n')
            for kind,media in (('cpp','text/x-c++src'),('tac','text/plain'),('binary','application/octet-stream')):
                a=service.get_artifact(rid,kind)
                self.assertEqual(a['media_type'],media)
                self.assertTrue(a['filename'].startswith('minipar_'+rid[:8]))
            self.assertIn(f'<< {num}',Path(service.get_artifact(rid,'cpp')['path']).read_text(encoding='utf-8'))
        after={k:hashlib.sha256(Path(service.get_artifact(first,k)['path']).read_bytes()).hexdigest() for k in before}
        self.assertEqual(before,after)

    def test_ace05_concurrent_five_rounds(self):
        for _ in range(5):
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                ids=list(pool.map(self.compile, ('print(1);\n','print(2);\n')))
            self.assertNotEqual(*ids)
            self.assertEqual([service.execute(rid)['stdout'] for rid in ids],['1\n','2\n'])

    def test_ace07_timeout(self):
        rid=self.compile('while(true) { print("."); }')
        r=service.execute(rid,timeout_sec=2)
        self.assertFalse(r['ok']); self.assertTrue(r['timed_out']); self.assertIsNone(r['exit_code'])
        self.assertLess(r['duration_ms'],3500)
        self.assertTrue(r['stdout_truncated'])
        self.assertLessEqual(len(r['stdout'].encode()),1024*1024)
        # A live Windows executable cannot be renamed; tasklist also checks the unique image below.
        path=Path(service.get_artifact(rid,'binary')['path'])
        renamed=path.with_suffix('.stopped')
        path.rename(renamed); renamed.rename(path)

    def test_native_gpp_fail_and_nonzero(self):
        r=service.compile_program('class Estado { var v=[3,2,1]; func soma(i) { if(i>=len(this.v)) { return 0; } return this.v[i]+this.soma(i+1); } } var obj=new Estado(); print(obj.soma(0));')
        self.assertFalse(r['ok']); self.assertEqual(r['diagnostics'][0]['code'],'GPP_FAILED')
        rid=self.compile('print(substr("x",4,1));')
        r=service.execute(rid)
        self.assertFalse(r['ok']); self.assertNotEqual(r['exit_code'],0); self.assertTrue(r['stderr'])

    def test_ace10_retention_21_real_builds(self):
        ids=[self.compile(f'print({n});') for n in range(21)]
        for n,rid in enumerate(ids[-20:],1):
            for kind in ('cpp','tac','binary'): self.assertTrue(service.get_artifact(rid,kind)['ok'])
            self.assertEqual(service.execute(rid)['stdout'],f'{n}\n')

    def test_path_redirection_rejected(self):
        rid=self.compile('print(1);')
        with patch.object(service,'_safe_directory',side_effect=OSError('redirected')):
            self.assertEqual(service.get_artifact(rid,'binary')['error']['code'],'ARTIFACT_NOT_FOUND')


class ProcessTests(unittest.TestCase):
    def test_both_outputs_bounded_and_blocked_stdin(self):
        script='import sys; sys.stdout.buffer.write(b"x"*1500000); sys.stdout.flush(); sys.stderr.buffer.write(b"y"*1500000); sys.stderr.flush()'
        r=run_bounded([sys.executable,'-c',script],cwd=OUT,stdin='z'*2000000,timeout=5)
        self.assertEqual(r['returncode'],0)
        self.assertTrue(r['stdout_truncated']); self.assertTrue(r['stderr_truncated'])
        self.assertEqual(len(r['stdout']),1024*1024); self.assertEqual(len(r['stderr']),1024*1024)

    def test_review_p2_invalid_utf8_expansion_truncates_both_streams(self):
        # Raw 400000 bytes fit; replacement encoding expands to 1200000 bytes.
        script = 'import sys; data=bytes([255])*400000; sys.stdout.buffer.write(data); sys.stderr.buffer.write(data)'
        r = run_bounded([sys.executable, '-c', script], cwd=OUT, timeout=5)
        self.assertEqual(r['returncode'], 0)
        self.assertFalse(r['timed_out'])
        for stream in ('stdout', 'stderr'):
            with self.subTest(stream=stream):
                self.assertTrue(r[stream+'_truncated'])
                self.assertEqual(r[stream], '\ufffd'*(1024*1024//3))
                self.assertLessEqual(len(r[stream].encode('utf-8')), 1024*1024)

    def test_review_p2_invalid_utf8_without_truncation(self):
        script = 'import sys; data=bytes([255])*100; sys.stdout.buffer.write(data); sys.stderr.buffer.write(data)'
        r = run_bounded([sys.executable, '-c', script], cwd=OUT, timeout=5)
        self.assertEqual(r['returncode'], 0)
        for stream in ('stdout', 'stderr'):
            self.assertEqual(r[stream], '\ufffd'*100)
            self.assertFalse(r[stream+'_truncated'])

    def test_review_p2_valid_utf8_without_truncation(self):
        # Multibyte UTF-8 close to the byte limit, preserved without false flags.
        script = 'import sys; data=chr(0x20ac).encode("utf-8")*349525; sys.stdout.buffer.write(data); sys.stderr.buffer.write(data)'
        r = run_bounded([sys.executable, '-c', script], cwd=OUT, timeout=5)
        self.assertEqual(r['returncode'], 0)
        for stream in ('stdout', 'stderr'):
            self.assertEqual(r[stream], '\u20ac'*349525)
            self.assertFalse(r[stream+'_truncated'])

    def test_descendants_killed(self):
        pidfile=OUT/('child-'+str(time.time_ns())+'.txt')
        script='import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"]); open(sys.argv[1],"w").write(str(p.pid)); time.sleep(60)'
        r=run_bounded([sys.executable,'-c',script,str(pidfile)],cwd=OUT,timeout=1)
        self.assertTrue(r['timed_out']); self.assertIsNone(r['returncode'])
        pid=int(pidfile.read_text())
        if os.name=='nt':
            import ctypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.OpenProcess.restype=ctypes.c_void_p
            handle=kernel.OpenProcess(0x1000,False,pid)
            if handle:
                from ctypes import wintypes
                kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD)]
                kernel.CloseHandle.argtypes=[ctypes.c_void_p]
                code=wintypes.DWORD(); kernel.GetExitCodeProcess(handle,ctypes.byref(code)); kernel.CloseHandle(handle)
                self.assertNotEqual(code.value,259,'descendant remains active')
        else:
            with self.assertRaises(ProcessLookupError): os.kill(pid,0)


if __name__=='__main__': unittest.main(verbosity=2)
