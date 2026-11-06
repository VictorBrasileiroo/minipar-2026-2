"""DEF-02: cada print concorrente deve chegar inteiro ao stdout."""
from collections import Counter
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CppCodeGenerator


BODY = """
par {
    seq {
        var i = 0;
        while (i < 40) { print("A", i, "fim"); i = i + 1; }
    }
    seq {
        var i = 0;
        while (i < 40) { print("B", i, "fim"); i = i + 1; }
    }
}
"""


class AtomicPrintTest(unittest.TestCase):
    def check_program(self, source, extra):
        program = Parser(Lexer(source).tokenize()).parse()
        semantic = SemanticAnalyzer()
        self.assertTrue(semantic.analyze(program))
        expected = Counter([f"{tag} {i} fim" for tag in ("A", "B") for i in range(40)] + extra)
        with tempfile.TemporaryDirectory(prefix="def02-", dir=ROOT / "output") as directory:
            cpp = Path(directory) / "program.cpp"
            exe = Path(directory) / "program.exe"
            cpp.write_text(CppCodeGenerator().generate_text(program, semantic, source), encoding="utf-8")
            env = os.environ.copy()
            default_gpp = Path(r"C:\msys64\ucrt64\bin\g++.exe")
            compiler = env.get("CXX") or (str(default_gpp) if default_gpp.is_file() else "g++")
            with patch.dict(os.environ, {"CXX": compiler}):
                result, error = CppCodeGenerator.compile_cpp(cpp, exe)
            self.assertIsNone(error, result)
            if Path(compiler).is_absolute():
                env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
            for repetition in range(20):
                run = subprocess.run([str(exe)], capture_output=True, text=True,
                                     encoding="utf-8", timeout=15, env=env)
                self.assertEqual(run.returncode, 0, (repetition, run.stderr))
                self.assertEqual(run.stderr, "", repetition)
                self.assertEqual(Counter(run.stdout.splitlines()), expected,
                                 (repetition, run.stdout))

    def test_legacy_par(self):
        self.check_program('print("SEQ", 7, true);\nprint("X\\nY", -3, false);\n' + BODY,
                           ["SEQ 7 1", "X", "Y -3 0"])

    def test_fork_join_codegen(self):
        self.check_program('func identity(x) { return x; }\nvar h = fork identity(7);\n'
                           + BODY + 'print("JOIN", join(h), "fim");\n', ["JOIN 7 fim"])


if __name__ == "__main__":
    unittest.main()
