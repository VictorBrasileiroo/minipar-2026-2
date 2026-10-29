"""Directed CORE-06 review: constructor regression and native par/return controls."""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from test_tac_fork_join import ROOT, frontend, generate
from tac import TACGenerator
from codegen import CppCodeGenerator


PAR_RETURN_CASES = [
    ('direct', 'var a=0;par{seq{a=1;return;a=99;}}print(a);', '1\n'),
    ('conditional', 'var a=0;var b=0;par{seq{a=1;if(true){return;}a=99;}'
     'seq{b=2;if(false){return;}b=3;}}print(a,b);', '1 3\n'),
    ('nested', 'var a=0;var b=0;par{seq{par{seq{a=1;return;a=99;}}'
     'b=2;return;b=99;}}print(a,b);', '1 2\n'),
    ('control', 'var a=0;var b=0;par{a=1;b=2;}print(a,b);', '1 2\n'),
    ('seq_function', 'func f(){seq{return 7;}return 99;}print(f());', '7\n'),
    ('par_function', 'func f(){var a=0;par{seq{a=1;return;}}return a+6;}print(f());', '7\n'),
    ('value_return', 'var a=0;par{seq{a=1;return 7;a=99;}}print(a);', '1\n'),
]


class ReviewCore06(unittest.TestCase):
    def native_probe(self, name, source, expected):
        """Execute the existing C++ backend, never TAC; retain artifacts for review."""
        compiler = os.environ.get('CXX') or r'C:\msys64\ucrt64\bin\g++.exe'
        env = dict(os.environ, CXX=compiler)
        env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')
        parent = ROOT / 'output/core06_review'
        parent.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix='native-' + name + '-', dir=parent))
        (folder / 'output').mkdir()
        (folder / 'probe.minipar').write_text(source, encoding='utf-8')
        program = frontend(source)
        tac = TACGenerator().generate_text(program)
        (folder / 'probe.tac').write_text(tac, encoding='utf-8')
        out, err = io.StringIO(), io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(folder)
            with patch.dict(os.environ, env), redirect_stdout(out), redirect_stderr(err):
                compiled = CppCodeGenerator().generate(program, 'probe')
        finally:
            os.chdir(previous)
        record = dict(name=name, source=source, tac=tac, expected_stdout=expected,
                      compile_ok=compiled, compile_stdout=out.getvalue(), compile_stderr=err.getvalue())
        if compiled:
            command = [str(folder / 'output/probe.exe')]
            run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                 cwd=folder, env=env, timeout=10)
            record['run'] = dict(command=command, returncode=run.returncode,
                                 stdout=run.stdout, stderr=run.stderr)
            record['oracle_pass'] = run.returncode == 0 and run.stdout == expected and run.stderr == ''
        (folder / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        self.assertTrue(compiled, err.getvalue())
        self.assertTrue(record['oracle_pass'], record)

    def test_constructor_without_args_preserves_existing_notation(self):
        self.assertEqual(generate('class C{var a=0;}var c=new C();'),
                         '# class C\nt0 = new C\nc = t0\n')

    def test_constructor_literal_arg_is_preserved(self):
        self.assertEqual(generate('class C{var a=0;}var c=new C(1);'),
                         '# class C\nt0 = new C(1)\nc = t0\n')

    def test_constructor_variable_values_saved_in_order(self):
        tac = generate('class Pair{var a=0;var b=0;}var x=2;var y=3;var p=new Pair(x,y);')
        self.assertRegex(tac, r'x = 2\ny = 3\n(t\d+) = x\n(t\d+) = y\n'
                         r'(t\d+) = new Pair\(\1, \2\)\np = \3')

    def test_constructor_nested_calls_do_not_mix_param_frames(self):
        tac = generate('func inc(x){return x+1;}class Pair{var a=0;var b=0;}'
                       'var p=new Pair(inc(2),inc(4));')
        self.assertRegex(tac, r'param 2\n(t\d+) = call inc, 1\nparam 4\n'
                         r'(t\d+) = call inc, 1\nt\d+ = new Pair\(\1, \2\)')
        self.assertEqual(tac.count('call inc, 1'), 2)

    def test_constructor_effect_is_evaluated_once(self):
        tac = generate('class Pair{var a=0;var b=0;}var xs=[1,2];var p=new Pair(xs.pop(),9);')
        self.assertEqual(tac.count('call xs.pop, 0'), 1)
        self.assertRegex(tac, r'(t\d+) = call xs.pop, 0\nt\d+ = new Pair\(\1, 9\)')

    def test_constructor_inside_outer_call_preserves_outer_params(self):
        tac = generate('class C{var a=0;}func inc(x){return x+1;}func use(c,x){return x;}'
                       'print(use(new C(inc(1)),inc(2)));')
        self.assertRegex(tac, r'param 1\n(t\d+) = call inc, 1\n(t\d+) = new C\(\1\)\n'
                         r'param 2\n(t\d+) = call inc, 1\nparam \2\nparam \3\nt\d+ = call use, 2')

    def test_constructor_mutation_changes_arguments_and_class(self):
        source = 'class C{var a=0;}var c=new C(17);'
        original = generate(source)
        self.assertNotEqual(original, generate(source.replace('17', '29')))
        self.assertIn('new C(29)', generate(source.replace('17', '29')))
        self.assertEqual(original.replace('C', 'Box'), generate(source.replace('C', 'Box')))

    def test_native_aggregate_initialization_and_effect(self):
        self.native_probe('constructors', '''
func inc(x){return x+1;}
class Pair{var a=0;var b=0;}
class Single{var a=0;}
var empty=new Pair();print(empty.a,empty.b);
var single=new Single(1);print(single.a);
var x=2;var y=3;var vars=new Pair(x,y);print(vars.a,vars.b);
var calls=new Pair(inc(2),inc(4));print(calls.a,calls.b);
var xs=[1,2];var effect=new Pair(xs.pop(),9);print(effect.a,effect.b,len(xs));
''', '0 0\n1\n2 3\n3 5\n2 9 1\n')

    def test_native_par_return_context_and_continuation(self):
        for name, source, expected in PAR_RETURN_CASES:
            with self.subTest(name=name):
                self.native_probe(name, source, expected)

    def test_return_is_alternative_exit_not_forced_fallthrough(self):
        tac = generate(PAR_RETURN_CASES[0][1])
        self.assertIn('return\na = 99\npar_end_branch PAR_0, 0', tac)
        # Unreachable source statements are retained; no invented jump after return.
        self.assertNotIn('return\ngoto ', tac)
        self.assertTrue(tac.endswith('par_barrier PAR_0\npar_end PAR_0\nprint a\n'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
