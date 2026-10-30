"""CORE-07: provas nativas e negativas; artefatos em output/core07/.

Executar da raiz: python -B -m unittest discover -s tests/2026_2/core07 -v
CXX e PATH (DLLs do compilador) devem estar configurados somente no processo.
"""
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer, CppProofError
from codegen import CppCodeGenerator

PARENT = ROOT / 'output/core07'
PARENT.mkdir(parents=True, exist_ok=True)
WORK = Path(tempfile.mkdtemp(prefix='run-', dir=PARENT))
EVIDENCE = []


def record(**data):
    EVIDENCE.append(data)
    (WORK / 'results.json').write_text(json.dumps(EVIDENCE, indent=2, ensure_ascii=False), encoding='utf-8')


def analyze(source):
    program = Parser(Lexer(source).tokenize()).parse()
    sem = SemanticAnalyzer()
    errors = io.StringIO()
    with redirect_stderr(errors): ok = sem.analyze(program)
    return program, sem, ok, errors.getvalue()


def build(source, name):
    folder = WORK / name
    folder.mkdir(exist_ok=True)
    (folder / 'program.minipar').write_text(source, encoding='utf-8')
    program, sem, ok, errors = analyze(source)
    if not ok: raise AssertionError(errors)
    previous = Path.cwd()
    out, err = io.StringIO(), io.StringIO()
    try:
        os.chdir(folder)
        with redirect_stdout(out), redirect_stderr(err):
            success = CppCodeGenerator().generate(program, 'program', sem, source)
    finally: os.chdir(previous)
    record(kind='build', name=name, source=source, ok=success, stdout=out.getvalue(), stderr=err.getvalue())
    if not success: raise AssertionError(err.getvalue())
    return folder / 'output/program.exe'


def run(exe, stdin='', expected='', code=0, error=None):
    proc = subprocess.run([str(exe)], input=stdin, text=True, capture_output=True, encoding='utf-8', timeout=15)
    passed = proc.returncode == code and proc.stdout == expected and (error in proc.stderr if error else proc.stderr == '')
    record(kind='run', executable=str(exe.relative_to(ROOT)), stdin=stdin, expected=expected,
           expected_exit=code, expected_error=error, exit=proc.returncode, stdout=proc.stdout,
           stderr=proc.stderr, status='PASS' if passed else 'FAIL')
    if not passed: raise AssertionError(f'exit={proc.returncode}, stdout={proc.stdout!r}, stderr={proc.stderr!r}')
    return proc


EQUIVALENCE = '''
func integer(x) { return helper(x) / 2; }
func decimal(x) { return helper(x) / 2; }
func helper(x) { return x * 3; }
func bits(x) { return (x % 3) + 7; }
func text(s) { return substr(s, 1, 2) + "!"; }
func flag(b) { return !b; }
func numbers(xs) { xs.append(4); return xs; }
func booleans(bs) { return bs; }
func grid(m) { return m; }
func noresult(x) { var y=x+1; }
func branchresult(x) { par { return x; } }
func complete(x) { if (x>0) { return 8; } else { return 9; } }
var dest=input();
print(integer(5),join(fork integer(5) on dest));
print(decimal(5.0),join(fork decimal(5.0) on dest));
print(bits(5),join(fork bits(5) on dest));
print(text("abcd"),join(fork text("abcd") on dest));
print(flag(true),join(fork flag(true) on dest));
var xs=[1,2];
print(numbers(xs),join(fork numbers(xs) on dest),xs);
print(booleans([true,false]),join(fork booleans([true,false]) on dest));
var m=matrix(2,2,3);
print(grid(m),join(fork grid(m) on dest));
print(complete(1),join(fork complete(1) on dest),complete(0));
var h=fork noresult(1) on dest; join(h);
var branch=fork branchresult(1) on dest; join(branch);
'''
EXPECTED_EQ = '7 7\n7.5 7.5\n9 9\nbc! bc!\n0 0\n[1, 2, 4] [1, 2, 4] [1, 2]\n[1, 0] [1, 0]\n[[3, 3], [3, 3]] [[3, 3], [3, 3]]\n8 8 9\n'

FAILURES = '''
func good(x) { return x+1; }
func bad(s) { return substr(s,99,1); }
func nested(s) { var h=fork bad(s); return join(h); }
func branched(s) { par { print(substr(s,99,1)); } return s; }
func slow(n) { var x=0.0; for(var i=0;i<n;i=i+1){ x=x+exp(0.001); } return x; }
var mode=input(); var dest=input();
if(mode=="bad") { var h=fork bad("a") on dest; print(join(h)); }
if(mode=="nested") { var h=fork nested("a") on dest; print(join(h)); }
if(mode=="par") { var h=fork branched("a") on dest; print(join(h)); }
if(mode=="second") { var h=fork good(1) on dest; var copy=h; print(join(copy)); print(join(h)); }
if(mode=="timeout") { var h=fork slow(2000000000) on dest; print(join(h,0)); }
if(mode=="good") { var h=fork good(41) on dest; print(join(h)); }
'''


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eq = build(EQUIVALENCE, 'equivalence')
        cls.failure_exe = build(FAILURES, 'failures')

    def test_local_equivalence(self):
        run(self.eq, 'local\n', EXPECTED_EQ)

    def test_effects_handles_collections(self):
        exe = build('''
func pair(xs,n) { return xs[0]*10+n; }
func id(x) { return x; }
func word(x) { return x; }
func boolcopy(xs) { return xs; }
func collect(h) { return join(h); }
func emit(x) { print(x); return x; }
func launch(x) { var h=fork id(x); return join(h); }
var xs=[1,2];
var h=fork pair(xs,xs.pop()); xs[0]=9; var copy=h;
print(join(copy),xs);
var hs=[]; hs.append(fork id(11)); hs.append(fork id(22));
var copied=hs; var total=0; for(var item in copied) { total=total+join(item); }
print(total);
var replacement=fork id(2); replacement=fork id(3); print(join(replacement));
var more=[fork id(4),fork id(5)]; print(join(more[1]),join(more[0]));
var a=false && join(fork id(emit(999)))>0; var b=true || join(fork id(emit(888)))>0;
print(a,b);
print(launch(7),join(fork launch(8)));
var bs=[true,false]; var before=bs[0]; bs[0]=false; print(before,bs.pop(),bs);
var bools=[true]; for(var item in bools){bools[0]=false; print(item);}
for(var i=0;i<1;bools[0]=true){i=i+1;} print(bools[0]);
print(join(fork boolcopy([true]))[0]);
print(collect(fork id(6)),collect(fork word("ok")));
var __fj_1_0=13; print(join(fork id(__fj_1_0)));
''', 'effects')
        run(exe, expected='12 [9]\n33\n3\n5 4\n0 1\n7 8\n1 0 [0]\n1\n1\n1\n6 ok\n13\n')

    def test_effects_once_and_argument_order(self):
        exe = build('''
func pair(a,b) { return a*10+b; }
func emit(x) { print(x); return x; }
func identity(x) { return x; }
var h=fork pair(emit(1),emit(2)) on input();
print(join(h,emit(3000)));
var tasks=[fork identity(4)];
print(join(tasks[emit(0)]));
''', 'order')
        run(exe, 'local\n', '1\n2\n3000\n12\n0\n4\n')

    def test_runtime_failures_local(self):
        for mode in ('bad', 'nested', 'par'):
            with self.subTest(mode=mode): run(self.failure_exe, f'{mode}\nlocal\n', code=1, error='TASK_FAILED')
        run(self.failure_exe, 'second\nlocal\n', expected='2\n', code=1, error='INVALID_HANDLE')
        run(self.failure_exe, 'timeout\nlocal\n', code=1, error='TIMEOUT')
        run(self.failure_exe, 'good\nbad-destination\n', code=1, error='BAD_DESTINATION')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port=sock.getsockname()[1]
        run(self.failure_exe, f'good\n127.0.0.1:{port}\n', code=1, error='WORKER_UNAVAILABLE')

    def start_worker(self, exe, name):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port=sock.getsockname()[1]
        log = open(WORK / f'{name}.log', 'w', encoding='utf-8')
        proc = subprocess.Popen([str(exe), '--minipar-worker', str(port), '--bind', '127.0.0.1'],
                                stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        self.addCleanup(log.close)
        def stop():
            if proc.poll() is None: proc.terminate()
            proc.wait(timeout=10)
        self.addCleanup(stop)
        for _ in range(100):
            if proc.poll() is not None: self.fail(f'worker exit={proc.returncode}')
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1', port)) == 0: break
            time.sleep(.05)
        else: self.fail('worker indisponivel')
        return proc, f'127.0.0.1:{port}'

    def test_loopback_equivalence_and_worker_mode(self):
        proc, dest = self.start_worker(self.eq, 'worker-equivalence')
        run(self.eq, dest+'\n', EXPECTED_EQ)
        self.assertIsNone(proc.poll())
        log = (WORK / 'worker-equivalence.log').read_text(encoding='utf-8')
        self.assertIn('fn=', log)
        self.assertNotIn('7 7\n', log)  # fluxo principal nunca executado no worker

    def test_worker_survives_recoverable_and_nested_errors(self):
        proc, dest = self.start_worker(self.failure_exe, 'worker-failures')
        for mode in ('bad', 'nested', 'par'):
            with self.subTest(mode=mode):
                run(self.failure_exe, f'{mode}\n{dest}\n', code=1, error='TASK_FAILED')
                self.assertIsNone(proc.poll())
                run(self.failure_exe, f'good\n{dest}\n', '42\n')
        run(self.failure_exe, f'second\n{dest}\n', expected='2\n', code=1, error='INVALID_HANDLE')
        run(self.failure_exe, f'timeout\n{dest}\n', code=1, error='TIMEOUT')

    def test_build_mismatch(self):
        other = build(FAILURES+'\n\n', 'other-build')
        proc, dest = self.start_worker(other, 'worker-mismatch')
        run(self.failure_exe, f'good\n{dest}\n', code=1, error='VERSION_MISMATCH')
        self.assertIsNone(proc.poll())

    def test_task_ids_out_of_order(self):
        exe = build('''
func work(n) { var x=0.0; for(var i=0;i<n;i=i+1){x=x+exp(0.001);} return x/exp(0.001); }
var dest=input();
var a=fork work(1000000000) on dest; var b=fork work(2) on dest;
print(join(b),join(a));
''', 'ids')
        proc, dest = self.start_worker(exe, 'worker-ids')
        run(exe, dest+'\n', '2 1e+09\n')
        log = (WORK / 'worker-ids.log').read_text(encoding='utf-8')
        self.assertLess(log.index('RESULT task-2'), log.index('RESULT task-1'))
        self.assertIsNone(proc.poll())


class ProofTests(unittest.TestCase):
    def reject(self, source, diagnostic=None):
        program, sem, ok, error = analyze(source)
        if ok:
            with self.assertRaises(CppProofError) as caught:
                CppCodeGenerator().generate_text(program, sem, source)
            error = str(caught.exception)
        if diagnostic: self.assertIn(diagnostic, error)
        record(kind='negative', source=source, diagnostic=error, status='PASS')

    def test_unproved_returns_helpers_and_recursion(self):
        bodies = ['if(x>0){return 1;}', 'while(x>0){return 1;}',
                  'if(x>0){return 1;}else{return;}',
                  'return f(x);', 'return f([x]);', 'return helper(x);']
        for body in bodies:
            with self.subTest(body=body):
                self.reject('func helper(x){if(x>0){return 2;}} func f(x){'+body+'} var h=fork f(0); print(join(h));')
        self.reject('func f(x){par{return x;}} var h=fork f(1); print(join(h));', 'none')

    def test_unknown_incompatible_forbidden(self):
        cases = [
            'func f(x){return x;} var x; var h=fork f(x);',
            'func f(x){return x;} var a=fork f(1); var b=fork f(1.0);',
            'func f(x){return x;} var a=fork f(1); var b=fork f("a");',
            'func f(x){return x;} var a=fork f(1); var b=fork f(a);',
            'class C{var x=1;} func f(x){return x;} var h=fork f(new C());',
            'func f(x){return x;} var c=c_channel("127.0.0.1",1); var h=fork f(c);',
            'func f(x){return x;} var a=[]; var h=fork f(a);',
            'func f(x){return x;} var h=fork f(1); var a=[h,2];',
            'func f(x){return x;} func unused(x){var h=fork f(x);} var h=fork f(1);',
        ]
        for source in cases:
            with self.subTest(source=source): self.reject(source)

    def test_contexts_are_specialized_and_forward_declared(self):
        source='func f(x){return helper(x);} func helper(x){return x;} print(helper(1.5)); var h=fork f(1); print(join(h));'
        p,s,ok,error=analyze(source); self.assertTrue(ok,error)
        gen=CppCodeGenerator(); text=gen.generate_text(p,s,source)
        self.assertEqual(len([k for k in gen.fj.contexts if k[0]=='helper']),2)
        self.assertTrue(s.function_contexts)
        self.assertIn(hashlib.sha256(source.encode()).hexdigest(),text)
        other=Parser(Lexer(source).tokenize()).parse()
        with self.assertRaisesRegex(CppProofError,'mesma AST'): gen.generate_text(other,s,source)

    def test_compile_failure_removes_stale_executable(self):
        source='func f(x){return x;} var h=fork f(1); print(join(h));'
        p,s,ok,error=analyze(source); self.assertTrue(ok,error)
        folder=WORK/'compile-fail'; (folder/'output').mkdir(parents=True)
        stale=folder/'output/probe.exe'; stale.write_bytes(b'stale')
        previous=Path.cwd(); log=io.StringIO()
        try:
            os.chdir(folder)
            with patch.dict(os.environ, CXX=sys.executable), redirect_stdout(log), redirect_stderr(log):
                self.assertFalse(CppCodeGenerator().generate(p,'probe',s,source))
            self.assertFalse(stale.exists())
        finally: os.chdir(previous)
        record(kind='compile_failure', log=log.getvalue(), status='PASS')

    def test_cli_waits_for_tac_without_stale_binary(self):
        folder=WORK/'cli'; (folder/'output').mkdir(parents=True)
        source=folder/'p.minipar'; source.write_text('func f(x){return x;} var h=fork f(1); print(join(h));',encoding='utf-8')
        exe=folder/'output/p.exe'; exe.write_bytes(b'stale')
        p=subprocess.run([sys.executable,'-B',str(ROOT/'main.py'),str(source),'p'],cwd=folder,capture_output=True,text=True,timeout=15)
        self.assertEqual(p.returncode,1); self.assertIn('CORE-06',p.stderr)
        self.assertFalse(exe.exists()); self.assertFalse((folder/'output/p.cpp').exists())
        record(kind='CLI', status='BLOCKED', reason='CORE-06 PR #17 fora de dev', stdout=p.stdout,stderr=p.stderr)


if __name__ == '__main__': unittest.main(verbosity=2)
