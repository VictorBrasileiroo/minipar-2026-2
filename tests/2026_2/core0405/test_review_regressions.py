"""Regressoes independentes das revisoes F1/F2/F3/F4 (sem executar tarefas)."""
from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer


def analyze(source):
    sem = SemanticAnalyzer()
    err = io.StringIO()
    tree = Parser(Lexer(source).tokenize()).parse()
    with redirect_stderr(err):
        ok = sem.analyze(tree)
    return ok, err.getvalue(), sem, tree


IDENTITY = 'func f(x){return x;} '


class ReviewTests(unittest.TestCase):
    def valid(self, source):
        ok, err, sem, tree = analyze(source)
        self.assertTrue(ok, err)
        return sem, tree

    def invalid(self, source, diagnostic):
        ok, err, _, _ = analyze(source)
        self.assertFalse(ok, err)
        self.assertIn(diagnostic, err)

    def test_f1_for_handles(self):
        self.valid(IDENTITY + 'seq{var hs=[fork f(1),fork f(2)];for(var h in hs){print(join(h));}}')

    def test_f1_assignment_concat_helper(self):
        self.valid(IDENTITY + 'func collect(hs){var t=0;for(var h in hs){t=t+join(h);}return t;} '
                   'func make(){return [fork f(3)];} var hs=[];hs=hs+[fork f(1)];'
                   'hs=hs+make();print(collect(hs));')

    def test_f1_known_non_task(self):
        self.invalid('var ns=[1,2];for(var n in ns){join(n);}', 'FJ-SEM-03')

    def test_f1_unknown(self):
        sem, _ = self.valid('var h;join(h);')
        self.assertTrue(sem.unresolved_fj)

    def test_f1_generic_list_unknown(self):
        sem, _ = self.valid('func collect(hs){for(var h in hs){join(h);}}')
        self.assertTrue(sem.unresolved_fj)

    def test_f1_list_assigned_then_appended(self):
        sem, _ = self.valid(IDENTITY + 'var hs;hs=[];hs.append(fork f(1));for(var h in hs){join(h);}')
        self.assertFalse(sem.unresolved_fj, sem.unresolved_fj)

    def test_f1_mixed_known_invalid(self):
        self.invalid(IDENTITY + 'var hs=[fork f(1),2];for(var h in hs){join(h);}', 'FJ-SEM-03')

    def test_f1_plain_helper_preserves_handles(self):
        sem, _ = self.valid(IDENTITY + 'func wrap(x){return [x];}'
                            'var hs=wrap(fork f(1));for(var h in hs){join(h);}')
        self.assertFalse(sem.unresolved_fj, sem.unresolved_fj)

    def test_f2_inherited_initializer(self):
        self.invalid('var g=1;class A{var x=g;}class B extends A{}'
                     'func task(){var b=new B();return 1;}var h=fork task();', 'FJ-SEM-05')

    def test_f2_multilevel_and_shadowed_property(self):
        self.invalid('var g=1;class A{var x=g;}class B extends A{var x=2;}'
                     'class C extends B{}func task(){var g=2;var c=new C();return 1;}'
                     'var h=fork task();', 'FJ-SEM-05')

    def test_f2_inherited_method(self):
        self.invalid('var g=1;class A{func read(){return g;}}class B extends A{}'
                     'func task(){var b=new B();return b.read();}var h=fork task();', 'FJ-SEM-05')

    def test_f2_constructor_helper_and_shadow(self):
        self.invalid('var g=1;func value(){return g;}class A{var x=value();}'
                     'class B extends A{}func task(){var b=new B();return 1;}'
                     'var h=fork task();', 'FJ-SEM-05')
        self.valid('var g=1;class A{var g=2;var x=g;}class B extends A{}'
                   'func task(){var b=new B();return 1;}var h=fork task();')

    def test_f2_cycles(self):
        self.invalid('class A extends B{}class B extends A{}'
                     'func task(){var a=new A();return 1;}var h=fork task();', 'ciclica')

    def test_f3_unrelated_diagnostics(self):
        code = 'func bad(x){return missing;}bad(1);bad(2);'
        _, before, _, _ = analyze(code)
        _, after, _, _ = analyze(code + IDENTITY + 'var h=fork f(1);')
        self.assertEqual(after, before)
        self.assertEqual(after.count("'missing'"), 1)

    def test_f3_unrelated_typing(self):
        for code in ('var x;x=1;x="a";',
                     'func show(x){print("v="+x);}show(3);',
                     'var a=[1];for(var i in a){i=1;i="x";}'):
            with self.subTest(code=code):
                _, before, _, _ = analyze(code)
                _, after, _, _ = analyze(code + IDENTITY + 'var h=fork f(1);')
                self.assertEqual(after, before)

    def test_f3_contextual_cache(self):
        self.invalid('var g=1;func helper(x){return g;}helper(1);'
                     'func task(x){return helper(x);}var h=fork task(1);', 'FJ-SEM-05')
        self.invalid('func collect(h){return join(h);}' + IDENTITY +
                     'var h=fork f(1);collect(h);collect(1);', 'FJ-SEM-03')

    def test_f3_cache_different_types(self):
        sem, _ = self.valid(IDENTITY + 'func launch(x){return fork f(x);}'
                            'var a=launch(1);var b=launch("ok");join(a);join(b);')
        signatures = [args[0].kind for entries in sem.fork_signatures.values() for args, _ in entries]
        self.assertIn('number', signatures)
        self.assertIn('string', signatures)

    def test_f3_methods_recursive_global(self):
        self.invalid('var g=1;class C{func a(n){return this.b(n);}'
                     'func b(n){if(n==0){return g;}return this.a(n-1);}}'
                     'func task(){var c=new C();return c.a(3);}var h=fork task();', 'FJ-SEM-05')

    def test_f3_recursive_global(self):
        self.invalid('var g=1;func a(n){return b(n);}func b(n){'
                     'if(n==0){return g;}return a(n-1);}var h=fork a(3);', 'FJ-SEM-05')

    def test_f3_linear_closure(self):
        source = 'func c10(x){return x;} '
        for n in reversed(range(10)):
            source += f'func c{n}(x){{return c{n+1}(x)+c{n+1}(x)+c{n+1}(x);}} '
        source += 'var h=fork c0(1);'
        visits = 0
        original = SemanticAnalyzer.validate_node
        def count(sem, node, *args, **kwargs):
            nonlocal visits
            visits += 1
            return original(sem, node, *args, **kwargs)
        with patch.object(SemanticAnalyzer, 'validate_node', count):
            self.valid(source)
        self.assertLess(visits, 1500, f'{visits} visitas: crescimento por chamada')

    def test_f3_time_bound_unrelated_chain(self):
        source = 'func c16(x){return x;} '
        for n in reversed(range(16)):
            source += f'func c{n}(x){{return c{n+1}(x)+c{n+1}(x);}} '
        source += IDENTITY + 'print(c0(1));var h=fork f(1);'
        script = ('import sys;sys.path.insert(0,"src");from lexer import Lexer;'
                  'from parser import Parser;from semantic import SemanticAnalyzer;'
                  f'assert SemanticAnalyzer().analyze(Parser(Lexer({source!r}).tokenize()).parse())')
        result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT,
                                capture_output=True, text=True, timeout=3)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_f4_worker_io(self):
        for statement in ('var x=input();', 'var c=c_channel("local",1);',
                          'send(c_channel("local",1),"x");',
                          'var x=receive(c_channel("local",1));'):
            with self.subTest(statement=statement):
                self.invalid('func task(){' + statement + 'return 1;}var h=fork task();', 'FJ-SEM-05')

    def test_f4_none(self):
        prefix='func task(){print("ok");}var h=fork task();'
        self.valid(prefix + 'join(h);')
        for use in ('print(join(h)+1);', 'var r=join(h);print(r*2);', 'print(join(h));'):
            with self.subTest(use=use):
                self.invalid(prefix + use, 'FJ-SEM-06')

    def test_f4_discarded_handle(self):
        self.invalid(IDENTITY + 'fork f(1);', 'FJ-SEM-03')
        self.invalid(IDENTITY + 'if(true) fork f(1);', 'FJ-SEM-03')

    def test_f4_signatures(self):
        sem, _ = self.valid(IDENTITY + 'func launch(x){return fork f(x);}var h=launch(1);join(h);')
        signatures = [s for entries in sem.fork_signatures.values() for s in entries]
        self.assertTrue(signatures)
        self.assertTrue(all(a.kind == 'number' for args, _ in signatures for a in args))

    def test_f4_transitive_provisional_signatures(self):
        sem, _ = self.valid(IDENTITY + 'func launch(x){return fork f(x);}'
                            'func wrapper(x){return launch(x);}var h=wrapper(1);join(h);')
        signatures = [s for entries in sem.fork_signatures.values() for s in entries]
        self.assertTrue(all(a.kind == 'number' for args, _ in signatures for a in args), signatures)


if __name__ == '__main__':
    unittest.main(verbosity=2)
