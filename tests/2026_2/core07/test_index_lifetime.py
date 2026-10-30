"""P1: valores temporarios nao escapam por referencia; matrizes locais preservam storage.

CORE07_INDEX_CODEGEN seleciona um snapshot anterior somente para o controle
negativo test_index_reference_contract (static_assert, sem executar UB).
"""
from pathlib import Path
from contextlib import redirect_stderr
import io
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from ast_nodes import IndexExpr, IdentifierExpr, iter_child_nodes
from codegen import CppCodeGenerator

if os.environ.get('CORE07_INDEX_CODEGEN'):
    spec = importlib.util.spec_from_file_location('index_baseline', os.environ['CORE07_INDEX_CODEGEN'])
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    CppCodeGenerator = baseline.CppCodeGenerator

PARENT = ROOT/'output/core07/p1-index-lifetime'
PARENT.mkdir(parents=True, exist_ok=True)
WORK = Path(tempfile.mkdtemp(prefix='run-', dir=PARENT))
RESULTS = []
TEXT = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SOURCE = '''
func idn(m) { return m; }
func ids(m) { return m; }
func idb(m) { return m; }
func make() { print(101); return matrix(2,2,7); }
func emit(x) { print(x); return x; }
var n=matrix(2,2,7);
var s=matrix(2,2,"TEXT");
var b=matrix(2,2,true);
print(idn(matrix(2,2,7))[0][0]);
print(join(fork idn(matrix(2,2,7)))[0][0]);
print(ids(matrix(2,2,"TEXT"))[0][0]);
print(join(fork ids(matrix(2,2,"TEXT")))[0][0]);
print(matrix(2,2,7)[0][1]);
print(make()[emit(0)][emit(1)]);
n[1][0]=9; s[0][1]="changed";
print(n[0][0],n[1][0],s[0][0],s[0][1]);
var before=b[0][0]; b[0][0]=false; print(before,b[0][0]);
print(idb(matrix(2,2,true))[0][0],join(fork idb(matrix(2,2,true)))[0][0]);
'''.replace('TEXT', TEXT)
EXPECTED = f'7\n7\n{TEXT}\n{TEXT}\n7\n101\n0\n1\n7\n7 9 {TEXT} changed\n1 0\n1 1\n'
REPRO = 'func f(m) { return m; } print(join(fork f(matrix(2, 2, 7)))[0][0]);'


def record(**data):
    RESULTS.append(data)
    (WORK/'results.json').write_text(json.dumps(RESULTS,indent=2),encoding='utf-8')


def translate(source):
    p = Parser(Lexer(source).tokenize()).parse()
    s = SemanticAnalyzer()
    if not s.analyze(p): raise AssertionError('semantic failure')
    g = CppCodeGenerator()
    return p,g,g.generate_text(p,s,source)


def compile_cpp(text, name, syntax=False):
    cpp=WORK/(name+'.cpp'); cpp.write_text(text,encoding='utf-8')
    exe=WORK/(name+'.exe')
    cmd=[os.environ.get('CXX','g++'),'-std=c++20','-O2','-pthread','-I',str(ROOT/'runtime/include'),str(cpp)]
    if syntax: cmd.append('-fsyntax-only')
    else:
        cmd.extend(['-o',str(exe)])
        if os.name=='nt': cmd.append('-lws2_32')
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    record(kind='compile',name=name,command=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
    return r,exe


class IndexLifetimeTests(unittest.TestCase):
    def test_text_cell_still_rejects_string_indexing(self):
        source='func f(m){return m;} var h=fork f(matrix(2,2,"abc")); print(join(h)[0][0][0]);'
        p=Parser(Lexer(source).tokenize()).parse()
        errors=io.StringIO()
        with redirect_stderr(errors): ok=SemanticAnalyzer().analyze(p)
        self.assertFalse(ok)
        self.assertIn('Indexacao de string nao suportada',errors.getvalue())
        record(kind='negative',source=source,stderr=errors.getvalue(),status='PASS')

    def test_index_reference_contract(self):
        p,g,text=translate(SOURCE)
        pending=list(p.statements); assertions=[]
        while pending:
            node=pending.pop()
            if isinstance(node,IndexExpr):
                root=node.object
                while isinstance(root,IndexExpr): root=root.object
                ref=isinstance(root,IdentifierExpr) and g.context['types'][id(node)].kind!='bool'
                expr=g._translate_expression(node)
                assertions.append(f'static_assert(std::is_lvalue_reference_v<decltype({expr})> == {str(ref).lower()}, "CORE07_INDEX_LIFETIME");')
            pending.extend(iter_child_nodes(node))
        # Unevaluated lambdas do not fork/join/print: deterministic type oracle.
        marker='    std::cout.flush(); std::cerr.flush(); std::_Exit(0);'
        text=text.replace(marker,'\n'.join(assertions)+'\n'+marker)
        r,_=compile_cpp(text,'reference-contract',syntax=True)
        record(kind='reference_contract',assertions=len(assertions),source=SOURCE,
               expected_exit=0,exit=r.returncode,status='PASS' if r.returncode==0 else 'FAIL')
        self.assertEqual(r.returncode,0,r.stderr)

    def native(self, source, expected, name):
        _,_,text=translate(source)
        (WORK/(name+'.minipar')).write_text(source,encoding='utf-8')
        r,exe=compile_cpp(text,name)
        self.assertEqual(r.returncode,0,r.stderr)
        for attempt in range(3):
            r=subprocess.run([str(exe)],capture_output=True,text=True,encoding='utf-8',timeout=15)
            passed=(r.returncode,r.stdout,r.stderr)==(0,expected,'')
            record(kind='native',name=name,attempt=attempt,source=source,expected=expected,
                   exit=r.returncode,stdout=r.stdout,stderr=r.stderr,status='PASS' if passed else 'FAIL')
            self.assertEqual((r.returncode,r.stdout,r.stderr),(0,expected,''))

    def test_native_temporaries_storage_effects_and_bool(self):
        self.native(SOURCE,EXPECTED,'matrix-cases')

    def test_original_reproducer(self):
        self.native(REPRO,'7\n','original-reproducer')


if __name__=='__main__': unittest.main(verbosity=2)
