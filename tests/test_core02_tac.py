"""CORE-02: regressões de TAC pela API real, sem comparar com o snapshot histórico.

Uso: python -B -m unittest discover -s tests -p test_core02_tac.py -v
"""
from pathlib import Path
import re
import sys
import unittest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator

T07 = REPO / "tests" / "teste7_quicksort_iterativo_tac.minipar"


def generate(source):
    program = Parser(Lexer(source).tokenize()).parse()
    if not SemanticAnalyzer().analyze(program):
        raise AssertionError("fonte de teste semanticamente inválida")
    return TACGenerator().generate_text(program)


class Core02TAC(unittest.TestCase):
    def test_same_name_different_body(self):
        source = T07.read_text(encoding="utf-8")
        _, tail = source.split("\nseq {", 1)
        mutated = "func quicksort_iterativo(arr) { var x = 1; return arr; }\nseq {" + tail
        original, changed = generate(source), generate(mutated)
        self.assertNotEqual(original, changed)
        self.assertTrue(changed.startswith(
            "func quicksort_iterativo:\nx = 1\nreturn arr\nendfunc quicksort_iterativo\n"))
        self.assertNotIn("WHILE_", changed)
        self.assertNotIn("pivot", changed)
        self.assertIn("call quicksort_iterativo, 1", changed)

    def test_name_does_not_select_algorithm(self):
        source = T07.read_text(encoding="utf-8")
        renamed = generate(source.replace("quicksort_iterativo", "ordenar"))
        self.assertEqual(generate(source).replace("quicksort_iterativo", "ordenar"), renamed)

    def test_partition_operator_changes_with_ast(self):
        source = T07.read_text(encoding="utf-8")
        original = generate(source)
        changed = generate(source.replace("arr[j] <= pivot", "arr[j] > pivot"))
        self.assertIn(" <= pivot\n", original)
        self.assertNotIn(" <= pivot\n", changed)
        self.assertEqual(original.replace(" <= pivot\n", " > pivot\n"), changed)

    def test_t07_structure_and_vocabulary(self):
        tac = generate(T07.read_text(encoding="utf-8"))
        self.assertNotIn("?", tac)
        self.assertNotIn("#", tac)
        self.assertEqual(tac.count("call stack.pop, 0"), 2)
        self.assertEqual(tac.count("call stack.append, 1"), 6)
        self.assertIn(" = arr[fim]\n", tac)
        self.assertIn(" = arr[j]\n", tac)
        self.assertIn(" = j < fim\n", tac)
        for line in ("arr[j] = tmp", "arr[fim] = tmp2", "return arr",
                     'print "Array ordenado:"', "print ordenado"):
            self.assertIn(line, tac.splitlines())
        self.assertEqual(len(re.findall(r"^WHILE_\d+:$", tac, re.M)), 2)
        # Todo salto tem destino emitido, inclusive continue e os dois laços.
        labels = re.findall(r"^(\w+):$", tac, re.M)
        self.assertEqual(len(labels), len(set(labels)))
        self.assertTrue(set(re.findall(r"goto (\w+)", tac)).issubset(labels))
        # Vocabulário do gerador existente; nenhum pseudo-op específico de Quicksort.
        instruction = re.compile(
            r"(?:func \w+:|endfunc \w+|\w+:|goto \w+|ifFalse \w+ goto \w+|"
            r"param .+|print .+|return .+|(?:\w+|arr\[\w+\]) = .+)")
        for line in tac.splitlines():
            self.assertIsNotNone(instruction.fullmatch(line), line)

    def test_other_statements_are_not_hidden_by_function_name(self):
        source = '''
func quicksort_iterativo(arr) { return arr; }
func dobro(x) { return x * 2; }
seq {
    var a = [3, 1];
    a[0] = dobro(a[1] + 4);
    var r = quicksort_iterativo(a);
    for (var i = 0; i < 2; i = i + 1) {
        if (i == 1) { break; } else { print(-i); }
    }
    print(r);
}
'''
        tac = generate(source)
        for fragment in ("func dobro:", " = x * 2\n", " = a[1]\n", " + 4\n",
                         "call dobro, 1", "a[0] = ", "FOR_STEP_", "ENDFOR_",
                         "ELSE_", " = -i\n", "print r\n"):
            self.assertIn(fragment, tac)
        self.assertNotIn("?", tac)


if __name__ == "__main__":
    unittest.main()
