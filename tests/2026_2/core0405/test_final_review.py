"""Regressoes da rodada final: codigos e tipos abstratos sem multiplicidade."""
from pathlib import Path
import subprocess
import sys
import unittest

from test_review_regressions import analyze, IDENTITY, ROOT
from semantic import ValueType


class FinalReviewTests(unittest.TestCase):
    def invalid(self, source, code):
        ok, diagnostics, _, _ = analyze(source)
        self.assertFalse(ok, diagnostics)
        self.assertIn(code + ':', diagnostics)
        return diagnostics

    def test_diagnostic_extension_preserves_03_and_06(self):
        self.invalid('join(1);', 'FJ-SEM-03')
        self.invalid('class A{}' + IDENTITY + 'var h=fork f(new A());', 'FJ-SEM-06')
        err = self.invalid(IDENTITY + 'fork f(1);', 'FJ-SEM-07')
        self.assertNotIn('FJ-SEM-03:', err)
        err = self.invalid('func f(){}print(join(fork f()));', 'FJ-SEM-08')
        self.assertNotIn('FJ-SEM-06:', err)

    def test_repeated_types_keep_every_distinct_alternative(self):
        number, text, obj = ValueType('number'), ValueType('string'), ValueType('A')
        self.assertEqual(ValueType('list', (number, number)), ValueType('list', (number,)))
        mixed = ValueType('list', (number, obj, number, text, obj))
        self.assertEqual(mixed.elements, (number, obj, text))
        self.assertNotEqual(mixed, ValueType('list', (number, text)))

    def test_nested_objects_not_hidden(self):
        self.invalid('class A{}' + IDENTITY +
                     'var h=fork f([[1,1],[1,new A(),1],[1,1]]);', 'FJ-SEM-06')

    def test_nested_handles_not_hidden(self):
        self.invalid(IDENTITY + 'var h=fork f(1);var k=fork f([[1,1],[h,h],[1,1]]);', 'FJ-SEM-06')

    def test_mixed_join_not_hidden(self):
        self.invalid(IDENTITY + 'var h=fork f(1);var hs=[h,h,1,h];'
                     'for(var k in hs){join(k);}', 'FJ-SEM-03')

    def test_distinct_task_results_preserved(self):
        ok, err, sem, _ = analyze(IDENTITY + 'func wrap(x){return fork f(x);}'
                                 'var h=wrap(1);var k=wrap("ok");join(h);join(k);')
        self.assertTrue(ok, err)
        kinds = {args[0].kind for signatures in sem.fork_signatures.values() for args, _ in signatures}
        self.assertEqual(kinds, {'number', 'string'})

    def test_transitive_global_after_normal_call(self):
        self.invalid('var g=1;func read(x){return g;}read([1,1]);'
                     'func task(x){return read([x,x]);}var h=fork task(1);', 'FJ-SEM-05')

    def test_recursive_global_with_nested_arguments(self):
        self.invalid('var g=1;func a(n,x){if(n==0){return g;}return b(n-1,[x,x]);}'
                     'func b(n,x){return a(n,x);}var h=fork a(2,[1,1]);', 'FJ-SEM-05')

    def test_none_as_statement_still_allowed(self):
        ok, err, _, _ = analyze('func f(){}var h=fork f();join(h);')
        self.assertTrue(ok, err)

    def test_nested_chain_finishes_in_bounded_subprocess(self):
        # A timeout catches exponential reanalysis; no hardware-specific speedup assertion.
        command = [sys.executable, '-B', str(Path(__file__).with_name('measure_final_review.py')),
                   '--worker', '16']
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        measured = json.loads(result.stdout)
        self.assertTrue(measured['accepted'], measured['diagnostics'])
        self.assertLess(measured['contexts'], 1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
