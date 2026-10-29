"""CORE-06: structural TAC oracles through the real frontend, stdlib only.

This suite inspects IR; it does not execute tasks or interpret TAC.
"""
from contextlib import redirect_stderr
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from ast_nodes import ASTNode, Program, VarDecl, ForkExpr, JoinExpr
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator
from codegen import CppCodeGenerator

IDENTITY = 'func f(x){return x;} '


def frontend(source):
    program = Parser(Lexer(source).tokenize()).parse()
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        ok = SemanticAnalyzer().analyze(program)
    if not ok:
        raise AssertionError(stderr.getvalue())
    return program


def generate(source):
    return TACGenerator().generate_text(frontend(source))


class Core06TAC(unittest.TestCase):
    def assert_flow(self, tac):
        labels = re.findall(r'^(\w+):$', tac, re.M)
        self.assertEqual(len(labels), len(set(labels)), tac)
        targets = re.findall(r'goto (\w+)', tac)
        targets += re.findall(r'^par_spawn \w+, \d+, (\w+)$', tac, re.M)
        self.assertTrue(set(targets).issubset(labels), tac)
        self.assertNotIn('?', tac)
        # Temps are globally allocated, even across branch/function bodies.
        definitions = re.findall(r'^(t\d+) = ', tac, re.M)
        # Boolean merge temps and loop iterator state are deliberate updates.
        generated = [t for t in definitions if not re.search(rf'^{t} = (?:true|false)$', tac, re.M)]
        self.assertEqual(len(generated), len(set(generated)), tac)

    def test_tac01_sequential_exact_oracle(self):
        self.assertEqual(generate('seq{var x=2+3;print(x);}'),
                         't0 = 2 + 3\nx = t0\nprint x\n')

    def test_tac02_local_fork_captures_before_mutation(self):
        tac = generate(IDENTITY + 'var x=10;var h=fork f(x);x=99;print(join(h));')
        self.assertIn('x = 10\nt0 = capture x\nt1 = fork f(t0) on "local"\nh = t1\nx = 99', tac)
        self.assertIn('t2 = join h\nprint t2', tac)

    def test_tac03_literal_and_dynamic_destination_once(self):
        tac = generate(IDENTITY + 'func host(){return "node:9000";}'
                       'var h=fork f(4) on "node:8000";'
                       'var k=fork f(5) on host();join(h);join(k);')
        self.assertEqual(tac.count('call host, 0'), 1)
        self.assertRegex(tac, r'(t\d+) = "node:8000"\nt\d+ = fork f\(t\d+\) on \1')
        self.assertRegex(tac, r'(t\d+) = call host, 0\n(t\d+) = \1\nt\d+ = fork f\(t\d+\) on \2')

    def test_tac03_variable_destination_not_folded(self):
        tac = generate(IDENTITY + 'var dest="local";var h=fork f(2) on dest;dest="n:1";join(h);')
        self.assertRegex(tac, r'(t\d+) = dest\nt\d+ = fork f\(t\d+\) on \1\nh = t\d+\ndest = "n:1"')

    def test_tac04_distinct_handles_same_function(self):
        tac = generate(IDENTITY + 'var a=fork f(1);var b=fork f(2);print(join(b),join(a));')
        handles = re.findall(r'^(t\d+) = fork f', tac, re.M)
        self.assertEqual(len(set(handles)), 2)
        self.assertLess(tac.index('join b'), tac.index('join a'))
        self.assert_flow(tac)

    def test_tac05_join_statement_does_not_invent_value(self):
        tac = generate('func work(){print(7);}var h=fork work();join(h);')
        self.assertTrue(tac.endswith('join h\n'))
        self.assertNotRegex(tac, r'= join')
        self.assertNotIn('return 0', tac)

    def test_tac06_timeout_once_and_handle_saved_first(self):
        tac = generate(IDENTITY + 'func wait(){return 30000;}var h=fork f(7);var r=join(h,wait());')
        self.assertEqual(tac.count('call wait, 0'), 1)
        self.assertRegex(tac, r'(t\d+) = h\n(t\d+) = call wait, 0\nt\d+ = join \1, timeout \2')
        self.assertIn('timeout 30000', generate(IDENTITY + 'var h=fork f(1);join(h,30000);'))

    def test_tac07_join_expression_order(self):
        tac = generate(IDENTITY + 'var a=fork f(3);var b=fork f(4);print(join(a)+join(b));')
        self.assertRegex(tac, r'(t\d+) = join a\n(t\d+) = join b\n(t\d+) = \1 \+ \2\nprint \3')

    def test_tac08_nested_call_param_frames_and_capture_order(self):
        tac = generate('func pair(a,b){return a+b;}func twice(x){return x*2;}'
                       'var x=10;var h=fork pair(x,twice(3));join(h);')
        self.assertRegex(tac, r'(t\d+) = capture x\nparam 3\n(t\d+) = call twice, 1\n'
                         r'(t\d+) = capture \2\nt\d+ = fork pair\(\1, \3\)')
        ordinary = generate('func pair(a,b){return a+b;}func inc(x){return x+1;}'
                            'var x=2;print(pair(x,inc(3)));')
        self.assertRegex(ordinary, r'(t\d+) = x\nparam 3\n(t\d+) = call inc, 1\n'
                         r'param \1\nparam \2\nt\d+ = call pair, 2')

    def test_tac08_effects_in_arguments_and_destination_not_duplicated(self):
        tac = generate('func f(a,b){return a+b;}func arg(x){return x;}'
                       'func dest(){return "local";}'
                       'var h=fork f(arg(1),arg(2)) on dest();join(h);')
        self.assertEqual(tac.count('call arg, 1'), 2)
        self.assertEqual(tac.count('call dest, 0'), 1)
        self.assertLess(tac.index('param 1'), tac.index('param 2'))
        self.assertLess(tac.index('param 2'), tac.index('call dest'))
        self.assertLess(tac.index('call dest'), tac.index(' = fork f'))

    def test_tac08_collection_snapshot_before_next_argument(self):
        tac = generate('func first(a,b){return a;}var values=[1,2];'
                       'var h=fork first(values,values.pop());values[0]=99;join(h);')
        self.assertRegex(tac, r'(t\d+) = capture values\n(t\d+) = call values.pop, 0\n'
                         r'(t\d+) = capture \2\nt\d+ = fork first\(\1, \3\)')
        self.assertLess(tac.index(' = fork first'), tac.index('values[0] = 99'))

    def test_tac08_matrix_operands_saved_before_effectful_call(self):
        tac = generate('func size(){return 2;}func f(a){return a;}'
                       'var n=2;var h=fork f(matrix(n,size(),0));join(h);')
        self.assertRegex(tac, r'(t\d+) = n\n(t\d+) = call size, 0\n'
                         r't\d+ = matrix\(\1, \2, 0\)')

    def test_join_handle_expression_and_timeout_both_once(self):
        tac = generate(IDENTITY + 'var a=fork f(2);var b=fork f(4);var hs=[a];'
                       'print(join(hs.pop(),join(b)));')
        self.assertEqual(tac.count('call hs.pop, 0'), 1)
        self.assertEqual(tac.count('join b'), 1)
        self.assertRegex(tac, r'(t\d+) = call hs.pop, 0\n(t\d+) = \1\n'
                         r'(t\d+) = join b\nt\d+ = join \2, timeout \3')

    def test_binary_left_value_saved_before_effectful_right(self):
        tac = generate(IDENTITY + 'var h=fork f(2);var x=3;print(x+join(h));')
        self.assertRegex(tac, r'(t\d+) = x\n(t\d+) = join h\nt\d+ = \1 \+ \2')

    def test_tac09_list_handles_and_handle_copy(self):
        tac = generate(IDENTITY + 'var a=fork f(1);var b=a;var hs=[a,fork f(2)];join(b);')
        self.assertEqual(tac.count(' = fork f'), 2)
        self.assertIn('b = a\n', tac)
        self.assertRegex(tac, r't\d+ = \[t\d+, t\d+\]')
        self.assertTrue(tac.endswith('join b\n'))

    def test_tac10_for_in_full_cycle_with_join(self):
        tac = generate(IDENTITY + 'var hs=[fork f(2),fork f(3)];for(var h in hs){print(join(h));}')
        self.assertRegex(tac, r'(t\d+) = iter_begin hs\n(FOR_IN_\d+):\n'
                         r'(t\d+) = iter_has_next \1\nifFalse \3 goto (ENDFOR_\d+)\n'
                         r'(t\d+) = iter_value \1\nh = \5\nt\d+ = join h\nprint t\d+\n'
                         r'FOR_STEP_\d+:\niter_next \1\ngoto \2\n\4:')
        self.assert_flow(tac)

    def test_tac10_iterable_evaluated_once_empty_and_nested_collections(self):
        for source in ['func values(){return [1,2];}for(var v in values()){print(v);}',
                       'for(var v in []){print(v);}',
                       'for(var row in matrix(2,3,0)){for(var v in row){print(v);}}',
                       'for(var v in range(2)){print(v);}']:
            with self.subTest(source=source):
                tac = generate(source)
                self.assertEqual(tac.count('call values, 0'), int('values()' in source))
                self.assertEqual(tac.count('iter_begin'), source.count('for('))
                self.assert_flow(tac)

    def test_tac11_par_two_bodies_and_terminal_branch_ends(self):
        tac = generate('var x=0;par{x=1;print(x);}print(9);')
        self.assertIn('par_begin PAR_0, 2\npar_spawn PAR_0, 0, PAR_BRANCH_2\n'
                      'par_spawn PAR_0, 1, PAR_BRANCH_3\ngoto PAR_WAIT_1', tac)
        self.assertIn('x = 1\npar_end_branch PAR_0, 0\nPAR_BRANCH_3:', tac)
        self.assertTrue(tac.endswith('par_barrier PAR_0\npar_end PAR_0\nprint 9\n'))
        self.assertNotIn('capture', tac)
        self.assert_flow(tac)

    def test_tac12_nested_par_regions_barriers_and_seq(self):
        tac = generate('seq{par{seq{print(1);par{print(2);print(3);}}print(4);}}')
        regions = re.findall(r'^par_begin (\w+), (\d+)$', tac, re.M)
        self.assertEqual(len(regions), 2)
        self.assertEqual(len({r for r, _ in regions}), 2)
        for region, count in regions:
            self.assertEqual(tac.count('par_barrier ' + region + '\n'), 1)
            self.assertEqual(len(re.findall(rf'^par_spawn {region}, ', tac, re.M)), int(count))
            self.assertEqual(len(re.findall(rf'^par_end_branch {region}, ', tac, re.M)), int(count))
        self.assert_flow(tac)

    def test_tac12_empty_par_has_barrier(self):
        tac = generate('par{}print(1);')
        self.assertIn('par_begin PAR_0, 0', tac)
        self.assertNotIn('par_spawn', tac)
        self.assertTrue(tac.endswith('par_barrier PAR_0\npar_end PAR_0\nprint 1\n'))

    def test_par_inside_if_loop_with_fork_join_and_return(self):
        tac = generate(IDENTITY + 'func run(){if(true){for(var i in [1,2]){'
                       'par{seq{var h=fork f(i);join(h);}seq{par{print(i);}return;}}}}}run();')
        self.assertEqual(tac.count('par_begin'), 2)
        self.assertIn(' = fork f(', tac)
        self.assertIn('join h\n', tac)
        self.assertRegex(tac, r'par_end PAR_\d+\nreturn\npar_end_branch PAR_\d+, 1')
        self.assert_flow(tac)

    def test_tac13_fork_join_if_while_and_classic_for(self):
        tac = generate(IDENTITY + 'var n=0;while(n<2){if(n==0){var h=fork f(n);print(join(h));}'
                       'n=n+1;}for(var i=0;i<2;i=i+1){var h=fork f(i);join(h);}')
        for token in ['WHILE_', 'ENDIF_', 'FOR_STEP_', 'ENDFOR_', 'join h']:
            self.assertIn(token, tac)
        self.assertEqual(tac.count(' = fork f'), 2)
        self.assert_flow(tac)

    def test_tac13_short_circuit_join_is_conditional(self):
        for op, instruction, initial in [('&&', 'ifFalse', 'false'), ('||', 'if', 'true')]:
            with self.subTest(op=op):
                tac = generate(IDENTITY + f'var h=fork f(1);print(false {op} join(h));')
                self.assertRegex(tac, rf't\d+ = {initial}\n{instruction} false goto (BOOL_END_\d+)\n'
                                 r'(t\d+) = join h\nt\d+ = !!\2\n\1:')

    def test_tac14_for_in_break_continue_targets(self):
        tac = generate('for(var n in [1,2]){if(n==1){continue;}break;}')
        step = re.search(r'^(FOR_STEP_\d+):', tac, re.M)[1]
        end = re.search(r'^(ENDFOR_\d+):', tac, re.M)[1]
        self.assertIn(f'goto {step}\n', tac)
        self.assertIn(f'goto {end}\n', tac)
        self.assert_flow(tac)

    def test_tac14_loops_inside_par_do_not_cross_branches(self):
        tac = generate('while(true){par{seq{for(var n in [1]){continue;}}'
                       'seq{while(true){break;}}}break;}')
        branches = re.split(r'^PAR_BRANCH_\d+:$', tac, flags=re.M)[1:]
        first = branches[0].split('par_end_branch')[0]
        second = branches[1].split('par_end_branch')[0]
        self.assertRegex(first, r'goto FOR_STEP_\d+')
        self.assertNotRegex(first, r'goto ENDWHILE_\d+')
        self.assertRegex(second, r'goto ENDWHILE_\d+')
        self.assertNotRegex(second, r'goto FOR_STEP_\d+')
        self.assert_flow(tac)

    def test_tac14_cross_branch_break_continue_explicitly_unsupported(self):
        for statement in ['break;', 'continue;']:
            with self.subTest(statement=statement):
                program = frontend('while(true){par{' + statement + '}}')
                with self.assertRaisesRegex(NotImplementedError, 'sem laco na branch atual'):
                    TACGenerator().generate_text(program)

    def test_tac14_do_continue_tests_condition_before_back_edge(self):
        tac = generate('do{continue;}while(false);')
        self.assertRegex(tac, r'DO_\d+:\ngoto (DO_TEST_\d+)\n\1:\nif false goto DO_\d+')
        self.assert_flow(tac)

    def test_tac15_mutations_change_structure_and_values(self):
        source = 'func calc(x){return x*2;}var h=fork calc(3) on "local";print(join(h));'
        original = generate(source)
        for changed, expected in [(source.replace('calc', 'compute'), 'fork compute'),
                                  (source.replace('calc(3)', 'calc(8)'), 'capture 8'),
                                  (source.replace('x*2', 'x+2'), 'x + 2'),
                                  (source.replace('"local"', '"node:90"'), '"node:90"'),
                                  (source + 'var k=fork calc(4);join(k);', 'join k')]:
            with self.subTest(expected=expected):
                tac = generate(changed)
                self.assertNotEqual(original, tac)
                self.assertIn(expected, tac)

    def test_tac16_arbitrary_names_no_filename_selection(self):
        a = generate(IDENTITY + 'var h=fork f(19);join(h);')
        b = generate(IDENTITY.replace('f(', 'synthesize(') + 'var h=fork synthesize(19);join(h);')
        self.assertEqual(a.replace('func f:', 'func synthesize:').replace('endfunc f', 'endfunc synthesize')
                         .replace('fork f(', 'fork synthesize('), b)

    def test_generator_reuse_is_deterministic_and_names_do_not_collide(self):
        program = frontend('func f(t0){return t0;}var t1=3;var h=fork f(t1);join(h);')
        generator = TACGenerator()
        first = generator.generate_text(program)
        self.assertEqual(first, generator.generate_text(program))
        self.assertNotIn('t0 = capture', first)
        self.assertNotIn('t1 = capture', first)
        self.assertRegex(first, r't2 = capture t1')

    def test_unknown_ast_rejected_in_expression_and_statement(self):
        @dataclass
        class Unknown(ASTNode):
            pass
        for program in [Program([Unknown()]), Program([VarDecl('x', Unknown())])]:
            with self.subTest(program=program), self.assertRaisesRegex(NotImplementedError, 'nao suportad'):
                TACGenerator().generate_text(program)
        with self.assertRaisesRegex(NotImplementedError, 'nao suportado'):
            TACGenerator().generate_text(Program([ASTNode()]))

    def test_class_attribute_fork_join_not_silently_omitted(self):
        for source in ['func f(){return 1;}class C{var h=fork f();}var c=new C();',
                       'func f(){return 1;}class C{var r=join(fork f());}var c=new C();',
                       'func f(){return 1;}func launch(){return fork f();}'
                       'class C{var h=launch();}var c=new C();']:
            with self.subTest(source=source), self.assertRaisesRegex(NotImplementedError, 'atributo'):
                generate(source)

    def test_invalid_fork_join_ast_rejected_without_placeholder(self):
        for program in [Program([VarDecl('h', ForkExpr('', []))]),
                        Program([VarDecl('h', ForkExpr('f', [None]))]),
                        Program([JoinExpr(None)]), Program([ForkExpr('f', [])])]:
            with self.subTest(program=program), self.assertRaises(NotImplementedError):
                TACGenerator().generate_text(program)

    def test_unrepresented_constructor_arguments_fail_explicitly(self):
        with self.assertRaisesRegex(NotImplementedError, 'construtor'):
            generate('class C{}var c=new C(1);')

    def test_string_escapes_keep_one_instruction_per_line(self):
        self.assertEqual(generate(r'print("a\nb\t\"c");'), 'print "a\\nb\\t\\\"c"\n')

    def test_generate_writes_actual_tac_file(self):
        program = frontend(IDENTITY + 'var h=fork f(2);join(h);')
        parent = ROOT / 'output/core06'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                path = TACGenerator().generate(program, 'probe')
                self.assertEqual(Path(path).read_text(encoding='utf-8'), TACGenerator().generate_text(program))
                self.assertFalse(Path('output/probe.exe').exists())
            finally:
                os.chdir(previous)

    def test_cpp_guard_does_not_compile_or_reuse_old_executable(self):
        program = frontend(IDENTITY + 'var h=fork f(2);join(h);')
        parent = ROOT / 'output/core06'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            previous = Path.cwd()
            try:
                os.chdir(folder)
                Path('output').mkdir()
                Path('output/probe.exe').write_bytes(b'old artifact')
                with redirect_stderr(io.StringIO()) as stderr, patch('codegen.subprocess.run') as compiler:
                    self.assertFalse(CppCodeGenerator().generate(program, 'probe'))
                compiler.assert_not_called()
                self.assertIn('CORE-07', stderr.getvalue())
                self.assertFalse(Path('output/probe.exe').exists())
            finally:
                os.chdir(previous)

    def test_cli_guard_rejects_before_tac_cpp_and_invalidates_old_exe(self):
        parent = ROOT / 'output/core06'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            folder = Path(folder)
            source = folder / 'probe.minipar'
            source.write_text(IDENTITY + 'var h=fork f(2);join(h);', encoding='utf-8')
            (folder / 'output').mkdir()
            (folder / 'output/probe.exe').write_bytes(b'old artifact')
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'main.py'), str(source), 'probe'],
                                    cwd=folder, capture_output=True, text=True, encoding='utf-8', timeout=20)
            self.assertEqual(result.returncode, 1)
            self.assertIn('CORE-07', result.stderr)
            self.assertNotIn('[TAC] Arquivo gerado', result.stdout)
            for extension in ['exe', 'cpp', 'tac']:
                self.assertFalse((folder / f'output/probe.{extension}').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
