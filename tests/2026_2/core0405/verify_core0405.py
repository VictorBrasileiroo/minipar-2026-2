"""CORE-04/05: oraculos de AST, diagnosticos, isolamento e recusa do backend.

Executar da raiz com Python da venv. Somente stdlib; o smoke legado usa CXX.
Fontes, logs e resultado JSON ficam em output/core0405/run-*/ (nao em legacy).
"""
from __future__ import annotations

from contextlib import redirect_stderr
from dataclasses import asdict
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from lexer import Lexer, TokenType
from parser import Parser
from ast_nodes import (ForkExpr, JoinExpr, BinaryExpr, FuncCallExpr, IdentifierExpr,
                       IndexExpr, MethodCall, PropertyAccess, StringExpr)
from semantic import SemanticAnalyzer
from tac import TACGenerator
from codegen import CppCodeGenerator

IDENTITY = 'func f(x) { return x; } '
WORK = None
EVIDENCE = []


def portable(value):
    if isinstance(value, str):
        return value.replace(str(ROOT).replace('\\', '\\\\'), '.').replace(str(ROOT), '.').replace(ROOT.as_posix(), '.')
    if isinstance(value, list): return [portable(item) for item in value]
    if isinstance(value, dict): return {key: portable(item) for key, item in value.items()}
    return value


def parse(source):
    return Parser(Lexer(source).tokenize()).parse()


def analyze(source):
    program = parse(source)
    semantic = SemanticAnalyzer()
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        ok = semantic.analyze(program)
    EVIDENCE.append(dict(source=source, semantic_ok=ok, stderr=stderr.getvalue(),
                         unresolved=semantic.unresolved_fj))
    return ok, stderr.getvalue(), semantic, program


class FrontendTests(unittest.TestCase):
    def test_keywords(self):
        self.assertEqual([t.type for t in Lexer('fork join on forked joined only').tokenize()],
                         [TokenType.FORK, TokenType.JOIN, TokenType.ON,
                          TokenType.IDENTIFIER, TokenType.IDENTIFIER,
                          TokenType.IDENTIFIER, TokenType.END_OF_FILE])

    def test_ast_fields_and_location(self):
        program = parse('\n  var h = fork f(2, "x") on "host:9000";\n  join(h, 20);')
        fork = program.statements[0].init_value
        self.assertIsInstance(fork, ForkExpr)
        self.assertEqual((fork.function_name, fork.line, fork.column), ('f', 2, 11))
        self.assertEqual([a.value for a in fork.arguments], ['2', 'x'])
        self.assertEqual(fork.destination.value, 'host:9000')
        join = program.statements[1]
        self.assertEqual((join.line, join.column, join.handle.name, join.timeout.value), (3, 3, 'h', '20'))
        EVIDENCE.append(dict(ast=asdict(program)))

    def test_ast_optional_fields(self):
        fork = parse('var h = fork f();').statements[0].init_value
        join = parse('join(h);').statements[0]
        self.assertEqual(fork.arguments, [])
        self.assertIsNone(fork.destination)
        self.assertIsNone(join.timeout)

    def test_precedence_calls_properties_and_blocks(self):
        program = parse('seq { par { var h = fork f(obj.valor, g(2)); print(1 + join(h) * 3); } }')
        block = program.statements[0].statements[0]
        fork = block.statements[0].init_value
        self.assertIsInstance(fork.arguments[0], PropertyAccess)
        self.assertIsInstance(fork.arguments[1], FuncCallExpr)
        result = block.statements[1].arguments[0]
        self.assertEqual((result.op, result.right.op), ('+', '*'))
        self.assertIsInstance(result.right.left, JoinExpr)
        self.assertIsInstance(parse('var x = join(h).valor;').statements[0].init_value, PropertyAccess)
        self.assertIsInstance(parse('var x = join(h)[0];').statements[0].init_value, IndexExpr)
        self.assertIsInstance(parse('join(h).metodo();').statements[0], MethodCall)

    def test_destination_consumes_expression(self):
        fork = parse('var h = fork f() on "host:" + to_string(9000);').statements[0].init_value
        self.assertIsInstance(fork.destination, BinaryExpr)
        self.assertIsInstance(parse('var x = (fork f() on "local") == h;').statements[0].init_value, BinaryExpr)

    def test_task_and_join_result_metadata(self):
        ok, err, semantic, program = analyze(IDENTITY + 'var h = fork f("ok"); var r = join(h);')
        self.assertTrue(ok, err)
        self.assertEqual(semantic._lookup('h').type, 'task')
        self.assertEqual(semantic._lookup('r').type, 'string')
        fork = program.statements[1].init_value
        arguments, result = semantic.fork_signatures[id(fork)][0]
        self.assertEqual(([a.kind for a in arguments], result.kind), (['string'], 'string'))
        self.assertEqual(semantic.expression_types[id(fork)].result.kind, 'string')

    def test_recursive_unknown_is_recorded(self):
        source = 'func f(n) { if (n == 0) {return n;} return f(n-1); } var h=fork f(3);'
        ok, err, semantic, _ = analyze(source)
        self.assertTrue(ok, err)
        self.assertTrue(semantic.unresolved_fj, 'Recursao nao pode ser declarada tipada por completo')

    def test_unknown_join_is_unresolved(self):
        ok, err, semantic, _ = analyze('var h; join(h);')
        self.assertTrue(ok, err)
        self.assertEqual(err, '')
        self.assertTrue(semantic.unresolved_fj)


POSITIVES = {
    'local_remote': IDENTITY + 'var a=fork f(2); var b=fork f(3) on "host:9000"; print(join(a)+join(b,3000)*2);',
    'destination_expression': IDENTITY + 'var d="local"; var h=fork f(1) on d + ""; join(h, len(d));',
    'destination_invalid_value_runtime': IDENTITY + 'var h=fork f(1) on "host:abc"; join(h,-1);',
    'local_variables': 'func f(x) {var sum=0; for(var i=0;i<x;i=i+1) {sum=sum+i;} return sum;} var h=fork f(5); join(h);',
    'parameter_shadow': 'var g=10; func f(g) {var x=g; seq {var g=4; x=x+g;} return x;} var h=fork f(2); join(h);',
    'for_shadow': 'var i=10; func f(n) {var s=0; for(var i in range(n)){s=s+i;} return s;} var h=fork f(4);',
    'transitive_parameter_shadow': 'var g=10; func helper(g){return g;} func f(x){return helper(x);} var h=fork f(2);',
    'caller_local_not_capture': 'var g=3; func helper(g){return g;} func f(x){var g=x; return helper(g);} var h=fork f(2);',
    'forward_function': 'var h=fork f(3); func f(x){return x;} join(h);',
    'mutual_recursion_isolation': 'func f(n){if(n==0){return 0;} return g(n-1);} func g(n){if(n==0){return 0;} return f(n-1);} var h=fork f(4);',
    'nested_lists': IDENTITY + 'var h=fork f([[1,2],[3,4]]); var r=join(h);',
    'handle_alias_assignment': IDENTITY + 'var h; h=fork f(1); var a=h; print(join(a));',
    'list_handles': IDENTITY + 'var hs=[fork f(1),fork f(2)]; print(join(hs[0])+join(hs[1]));',
    'list_append_handles': IDENTITY + 'var hs=[]; hs.append(fork f(1)); hs.append(fork f(2)); join(hs[0]);',
    'copied_list_value': IDENTITY + 'var v=[1];var a=v;a.append(fork f(2));var h=fork f(v);',
    'generic_collect_helper': IDENTITY + 'func collect(h){return join(h);} var h=fork f(2); print(collect(h));',
    'local_object_method': 'class A{var n=1; func get(){return this.n;}} func f(){var a=new A();return a.get();} var h=fork f();',
    'local_object_helper': 'class A{var n=1;} func make(){return new A();} func f(){var a=make();return a.n;} var h=fork f();',
    'local_object_call_expression': 'class A{var n=1;func get(){return this.n;}}func make(){return new A();}func f(){return make().get();}var h=fork f();',
    'legacy_in_fj_program': 'class A{var s="x";func get(){return this.s+"!";}} func f(s){var v=[1,2];v.append(3);return s+to_string(len(v));} seq{par{var h=fork f("a");print(join(h));}}',
}

NEGATIVES = {
    '01_missing': ('var h=fork missing();', 'FJ-SEM-01'),
    '01_variable': ('var f=3; var h=fork f();', 'FJ-SEM-01'),
    '01_class': ('class A{} var h=fork A();', 'FJ-SEM-01'),
    '01_builtin': ('var h=fork len([1]);', 'FJ-SEM-01'),
    '01_method': ('class A{func method(){return 1;}} var h=fork method();', 'FJ-SEM-01'),
    '01_nested': ('seq{func f(){return 1;} var h=fork f();}', 'FJ-SEM-01'),
    '01_shadow': (IDENTITY + 'seq{var f=3;var h=fork f(1);}', 'FJ-SEM-01'),
    '02_missing_arg': (IDENTITY + 'var h=fork f();', 'FJ-SEM-02'),
    '02_extra_arg': (IDENTITY + 'var h=fork f(1,2);', 'FJ-SEM-02'),
    '03_number': ('join(1);', 'FJ-SEM-03'),
    '03_string': ('join("task-1");', 'FJ-SEM-03'),
    '03_object': ('class A{} join(new A());', 'FJ-SEM-03'),
    '03_generic_bad_call': ('func collect(h){return join(h);} print(collect(2));', 'FJ-SEM-03'),
    '04_destination': (IDENTITY + 'var h=fork f(1) on 3;', 'FJ-SEM-04'),
    '04_timeout': (IDENTITY + 'var h=fork f(1);join(h,"3");', 'FJ-SEM-04'),
    '04_boolean_timeout': (IDENTITY + 'var h=fork f(1);join(h,true);', 'FJ-SEM-04'),
    '04_destination_function': ('func dest(){return 3;} func f(){return 1;} var h=fork f() on dest();', 'FJ-SEM-04'),
    '05_read': ('var g=1;func f(){return g;}var h=fork f();', 'FJ-SEM-05'),
    '05_this_capture': ('func f(){return this.n;}var h=fork f();', 'FJ-SEM-05'),
    '05_write': ('var g=1;func f(){g=2;return 1;}var h=fork f();', 'FJ-SEM-05'),
    '05_transitive': ('var g=1;func helper(){return g;}func f(){return helper();}var h=fork f();', 'FJ-SEM-05'),
    '05_caller_shadow': ('var g=1;func helper(){return g;}func f(){var g=2;return helper();}var h=fork f();', 'FJ-SEM-05'),
    '05_before_local': ('var g=1;func f(){var x=g;var g=2;return x;}var h=fork f();', 'FJ-SEM-05'),
    '05_after_block': ('var g=1;func f(){seq{var g=2;}return g;}var h=fork f();', 'FJ-SEM-05'),
    '05_index_write': ('var g=[1];func f(){g[0]=2;return 1;}var h=fork f();', 'FJ-SEM-05'),
    '05_property_read': ('class A{var n=1;}var g=new A();func f(){return g.n;}var h=fork f();', 'FJ-SEM-05'),
    '05_method_transitive': ('var g=1;class A{func get(){return g;}}func f(){var a=new A();return a.get();}var h=fork f();', 'FJ-SEM-05'),
    '05_initializer_global': ('var g=1;class A{var n=g;}func f(){var a=new A();return a.n;}var h=fork f();', 'FJ-SEM-05'),
    '05_recursive': ('var g=1;func f(n){if(n==0){return g;}return f(n-1);}var h=fork f(3);', 'FJ-SEM-05'),
    '05_mutual_recursive': ('var g=1;func a(n){return b(n);}func b(n){if(n==0){return g;}return a(n-1);}var h=fork a(2);', 'FJ-SEM-05'),
    '06_object_arg': ('class A{} ' + IDENTITY + 'var h=fork f(new A());', 'FJ-SEM-06'),
    '06_channel_arg': (IDENTITY + 'var c=c_channel("local",9000);var h=fork f(c);', 'FJ-SEM-06'),
    '06_task_arg': (IDENTITY + 'var h=fork f(1);var k=fork f(h);', 'FJ-SEM-06'),
    '06_object_return': ('class A{} func f(){return new A();}var h=fork f();', 'FJ-SEM-06'),
    '06_channel_return': ('func f(){return c_channel("local",9000);}var h=fork f();', 'FJ-SEM-06'),
    '06_task_return': ('func f(){return 1;}func bad(){return fork f();}var h=fork bad();', 'FJ-SEM-06'),
    '06_list_object': ('class A{} ' + IDENTITY + 'var h=fork f([[new A()]]);', 'FJ-SEM-06'),
    '06_list_task': (IDENTITY + 'var h=fork f(1);var k=fork f([h]);', 'FJ-SEM-06'),
    '06_shadow_list_initializer': (IDENTITY + 'var v=[fork f(1)];seq{var v=v;var h=fork f(v);}', 'FJ-SEM-06'),
    '06_list_append': ('class A{} ' + IDENTITY + 'var v=[];v.append(new A());var h=fork f(v);', 'FJ-SEM-06'),
    '06_list_index_assign': ('class A{} ' + IDENTITY + 'var v=[1];v[0]=new A();var h=fork f(v);', 'FJ-SEM-06'),
    '06_helper_return': ('class A{} func helper(){return new A();}func f(){return helper();}var h=fork f();', 'FJ-SEM-06'),
    '06_arg_from_helper': ('class A{} func helper(){return new A();}' + IDENTITY + 'var h=fork f(helper());', 'FJ-SEM-06'),
    '06_mixed_returns': ('class A{} func f(n){if(n==0){return 1;}return new A();}var h=fork f(2);', 'FJ-SEM-06'),
    '06_task_arithmetic': (IDENTITY + 'var h=fork f(1);var k=fork f(h+1);', 'FJ-SEM-06'),
    'core03_string_mix': (IDENTITY + 'var h=fork f(1);print("x"+3);', 'conversao explicita'),
    'core03_string_list': (IDENTITY + 'var h=fork f(1);var v=["x"];', 'Listas de strings'),
}

MALFORMED = [
    'fork ;', 'fork ();', 'fork f;', 'fork f(;', 'fork f(1;',
    'fork f() on ;', 'fork f(,1);', 'fork f(1,);',
    'join();', 'join(h;', 'join(h,);', 'join(h,1,2);',
]


def positive_test(source):
    def check(self):
        ok, stderr, _, _ = analyze(source)
        self.assertTrue(ok, stderr)
        self.assertEqual(stderr, '')
    return check


def negative_test(source, diagnostic):
    def check(self):
        ok, stderr, _, _ = analyze(source)
        self.assertFalse(ok)
        self.assertIn(diagnostic, stderr)
    return check


def malformed_test(source):
    def check(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            parse(source)
        self.assertEqual(raised.exception.code, 1)
        self.assertIn('Linha 1', stderr.getvalue())
        self.assertIn('SINTATICO', stderr.getvalue())
        EVIDENCE.append(dict(source=source, syntax_error=stderr.getvalue()))
    return check


for name, source in POSITIVES.items():
    setattr(FrontendTests, 'test_positive_' + name, positive_test(source))
for name, (source, diagnostic) in NEGATIVES.items():
    setattr(FrontendTests, 'test_negative_' + name, negative_test(source, diagnostic))
for i, source in enumerate(MALFORMED):
    setattr(FrontendTests, f'test_malformed_{i:02}', malformed_test(source))


class BackendBoundaryTests(unittest.TestCase):
    def test_direct_generators_refuse_nested_fork(self):
        program = parse('func f(){return 1;}func unused(){var h=fork f();return 2;}')
        with self.assertRaisesRegex(NotImplementedError, 'CORE-06'):
            TACGenerator().generate_text(program)
        destination = Path(tempfile.mkdtemp(dir=WORK))
        previous = Path.cwd()
        try:
            os.chdir(destination)
            output = destination / 'output'
            output.mkdir()
            binary = output / 'probe.exe'
            binary.write_bytes(b'previous artifact')
            stderr = io.StringIO()
            with redirect_stderr(stderr), patch('codegen.subprocess.run') as compiler:
                self.assertFalse(CppCodeGenerator().generate(program, 'probe'))
                compiler.assert_not_called()
            self.assertIn('CORE-07', stderr.getvalue())
            self.assertFalse(binary.exists())
            self.assertFalse((output / 'probe.cpp').exists())
        finally:
            os.chdir(previous)

    def test_cli_refuses_before_artifacts(self):
        folder = Path(tempfile.mkdtemp(dir=WORK))
        source = folder / 'program.minipar'
        source.write_text(IDENTITY + 'var h=fork f(2);print(join(h));', encoding='utf-8')
        (folder / 'output').mkdir()
        binary = folder / 'output/program.exe'
        binary.write_bytes(b'previous artifact')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'main.py'), str(source), 'program'],
                                cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=20)
        EVIDENCE.append(dict(command=result.args, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
        self.assertEqual(result.returncode, 1)
        self.assertIn('CORE-06/CORE-07', result.stderr)
        self.assertNotIn('ERRO SEMANTICO', result.stderr)
        self.assertFalse(binary.exists())
        self.assertFalse((folder / 'output/program.cpp').exists())
        self.assertFalse((folder / 'output/program.tac').exists())

    def test_legacy_native_smoke(self):
        folder = Path(tempfile.mkdtemp(dir=WORK))
        source = folder / 'legacy_smoke.minipar'
        source.write_text('''class Texto {var s="ok";func get(){return this.s+"!";}}
func fat(n){if(n<=1){return 1;}return n*fat(n-1);}
var obj=new Texto();seq{print(fat(5),obj.get(),substr("abc",1,1));}
par{print("par");}
''', encoding='utf-8')
        compiled = subprocess.run([sys.executable, '-B', str(ROOT / 'main.py'), str(source), 'smoke'],
                                  cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=120)
        EVIDENCE.append(dict(command=compiled.args, exit=compiled.returncode, stdout=compiled.stdout, stderr=compiled.stderr))
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        self.assertEqual(compiled.stderr, '')
        binary = folder / 'output/smoke.exe'
        self.assertTrue(binary.is_file())
        executed = subprocess.run([str(binary)], cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=10)
        EVIDENCE.append(dict(command=executed.args, exit=executed.returncode, stdout=executed.stdout, stderr=executed.stderr))
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(executed.stdout, '120 ok! b\npar\n')
        self.assertEqual(executed.stderr, '')


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append(dict(test=test.id(), status='PASS'))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append(dict(test=test.id(), status='FAIL', detail=self._exc_info_to_string(err, test)))

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append(dict(test=test.id(), status='FAIL', detail=self._exc_info_to_string(err, test)))


if __name__ == '__main__':
    parent = ROOT / 'output/core0405'
    parent.mkdir(parents=True, exist_ok=True)
    WORK = Path(tempfile.mkdtemp(prefix='run-', dir=parent))
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    spec = importlib.util.spec_from_file_location('core0405_review', Path(__file__).with_name('test_review_regressions.py'))
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(review))
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    files = ['src/lexer.py', 'src/parser.py', 'src/ast_nodes.py', 'src/semantic.py',
             'src/tac.py', 'src/codegen.py', 'main.py', 'tests/2026_2/core0405/verify_core0405.py',
             'tests/2026_2/core0405/test_review_regressions.py']
    summary = dict(python=sys.version, tests=result.testsRun, results=result.records, evidence=EVIDENCE,
                   hash_normalization='UTF-8 text with LF',
                   hashes={p: hashlib.sha256((ROOT / p).read_text(encoding='utf-8').encode('utf-8')).hexdigest() for p in files})
    (WORK / 'summary.json').write_text(json.dumps(portable(summary), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Evidencias: {(WORK / "summary.json").relative_to(ROOT)}')
    raise SystemExit(not result.wasSuccessful())
