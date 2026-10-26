"""Provas C-T11-v1 sem editar referencias: MiniPar -> main.py -> g++ -> binario.

Somente stdlib. CXX deve selecionar o g++ C++20; suas DLLs devem estar no PATH
do processo. Fontes do contrato sao copiadas literalmente para a rodada em output/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
EXPRESSION = "((2+4)*7)-(5*4)"


def cases():
    # Review regressions: numeric assignments must never become C++ char writes.
    review_negatives = {
        "REVIEW-ATRIBUTO": 'class C { var t = ""; } var c = new C(); c.t = 65; print(c.t);',
        "REVIEW-METODO": 'class C { var t = ""; func set(n) { this.t = n; } } var c = new C(); c.set(72); print(c.t);',
        "REVIEW-RETORNO-FUNCAO": 'func n() { return 67; } var s = "z"; s = n(); print(s);',
        "REVIEW-RETORNO-METODO": 'class C { func n() { return 67; } } var c = new C(); var s = "z"; s = c.n(); print(s);',
        "REVIEW-PARAMETRO": 'func set(n) { var s = ""; s = n; return s; } print(set(72));',
        "REVIEW-FOR": 'func n() { return 65; } var s = ""; for (var i = 0; i < 1; s = n()) { i = i + 1; } print(s);',
    }
    for name, source in review_negatives.items():
        yield dict(id=name, source=source, compile_error=True,
                   diagnostic="Tipo incompativel" if name == "REVIEW-ATRIBUTO" else "atribuicao")
    for native in ("to_string", "substr", "len", "range", "exp", "random", "to_number", "parse_ints"):
        yield dict(id="REVIEW-NOME-" + native, source=f'func {native}(a) {{ return a * 2; }} print({native}(21));',
                   compile_error=True, diagnostic="reservado")
    yield dict(id="REVIEW-STRINGS-VALIDAS", source='''
class C { var t = ""; func set(s) { this.t = s; } func get() { return this.t; } }
func texto(s) { var r = ""; r = s; return r; }
var c = new C(); c.t = "a"; c.set("b"); var s = ""; s = c.get();
s = texto(s); for (var i = 0; i < 1; s = "c") { i = i + 1; }
print(c.t, s, texto("ok"));
''', stdout="b c ok\n")
    contract = (ROOT / "docs/02_CONTRATOS_TECNICOS.md").read_text(encoding="utf-8")
    section = contract.split("### 3.5 ", 1)[1].split("### 3.6 ", 1)[0]
    sources = dict(re.findall(r"#### (PROVA-(?:\d+|INT))[^\n]*\n.*?```minipar\n(.*?)```", section, re.S))
    oracles = {
        "PROVA-01": ("", "3 3\n"),
        "PROVA-02": (EXPRESSION, "(\n2\n2+4\n2\n"),
        "PROVA-03": ("", "42\n-84\n22\n-46\n"),
        "PROVA-04": ("10 -8*7", "10-8*7\nMOV R0, #22\nt1 = 10-8*7\nR3, R3\n"),
        "PROVA-05": (EXPRESSION, "5 4 6\n"),
        "PROVA-06": (EXPRESSION, "[]\n[]\n[]\n0\ninteira\n[)]\n+4\n2\n-1\ncurto-circuito\n" + EXPRESSION + "\n"),
        "PROVA-07": (EXPRESSION, "VVVVVVVVVVVVVFFF\n"),
        "PROVA-08": (EXPRESSION, "ab\n[]\nR3, #-84\n7*2\n" + EXPRESSION + "\nfim\nt1 = t2\nMOV R0, #22\n0;1;2;\n4\n"),
        "PROVA-09": (EXPRESSION, "    SUB    r2\nMUL!\n[?|((]\n⚙️ Assembly ARMv7 (CPUlator):\n🔹 2 → CONST\n"),
        "PROVA-INT": ("((10 -8*7)+4)*2", "SIM(() SIM(() NUM(10) SIM(-) NUM(8) SIM(*) NUM(7) SIM()) SIM(+) NUM(4) SIM()) SIM(*) NUM(2)\ntotal=13\n"),
    }
    assert sources.keys() == oracles.keys(), "Provas do contrato ausentes ou duplicadas"
    for name, (stdin, stdout) in oracles.items():
        yield dict(id=name, source=sources[name], stdin=stdin + "\n", stdout=stdout)

    error_indices = [("0 - 1", "1", "abc"), ("0", "0 - 1", "abc"),
                     ("4", "0", "abc"), ("2", "2", "abc"),
                     ("3", "1", "abc"), ("1.5", "1", "abc"), ("0", "1", "")]
    for i, (start, size, stdin) in enumerate(error_indices, 1):
        yield dict(id=f"ERR-{i:02}", source='var e = input();\nprint("antes");\n'
                   f'print(substr(e, {start}, {size}));\nprint("depois");\n',
                   stdin=stdin + "\n", stdout="antes\n", exit_code=1,
                   stderr_contains=["substr", "inicio", "tamanho", "len"])

    negatives = ['print("R" + 3);', 'var s = "abc"; if (s == 3) { print("x"); }',
                 'print(substr("abc", 0));']
    for i, source in enumerate(negatives, 1):
        yield dict(id=f"NEG-{i:02}", source=source, compile_error=True,
                   diagnostic="espera 3 argumento(s)" if i == 3 else "conversao explicita")

    # Regressao dos recursos ja disponiveis, sem rede nem alteracoes aos testes herdados.
    yield dict(id="REG-LISTA", source='''func montar(n) {
    var v = []; for (var i in range(n)) { v.append(i); } return v;
}
var v = montar(3); v[0] = 7; print(v.pop(), v[0], len(v));
var vazio = []; print(len(vazio) - 1);
''', stdout="2 7 2\n-1\n")
    yield dict(id="REG-RECURSAO", source='''func fat(n) {
    if (n <= 1) { return 1; } return n * fat(n - 1);
}
print(fat(6));
''', stdout="720\n")
    yield dict(id="REG-CLASSE", source='''class Estado {
    var v = []; var total = 0;
    func add(n) { this.v.append(n); }
    func soma(i) {
        if (i >= len(this.v)) { return 0.0; }
        this.total = this.total + this.v[i]; return this.v[i] + this.soma(i + 1);
    }
    func texto(i) {
        if (i >= len(this.v)) { return "fim"; }
        return to_string(this.v[i]) + ":" + this.texto(i + 1);
    }
}
func preencher(obj, n) {
    if (n <= 0) { return; } obj.add(n); preencher(obj, n - 1);
}
var obj = new Estado(); preencher(obj, 3);
print(obj.soma(0), obj.total, obj.texto(0));
''', stdout="6 6 3:2:1:fim\n")
    yield dict(id="HERDADO-RETORNO-NUMERICO", source='''class Estado {
    var v = [3, 2, 1];
    func soma(i) {
        if (i >= len(this.v)) { return 0; }
        return this.v[i] + this.soma(i + 1);
    }
}
var obj = new Estado(); print(obj.soma(0));
''', compile_error=True, diagnostic="inconsistent deduction", known_defect=True)
    yield dict(id="EXTRA-STRINGS", source='''class Texto {
    var valor = "é";
    func ler(n) { if (n == 0) { return "vazio"; } return this.valor + "!"; }
}
func eco(s) { return s; }
string s; s = "ação";
var t = new Texto(); t.valor = t.valor + "🙂";
print(s, t.valor, t.ler(1), "[" + t.ler(0) + "]", eco("ok"));
print("a\\t\\\"\\\\b");
print(len("é"), len("🙂"));
if ("z" > "b" && "a" <= "a" && "c" >= "b" && "d" != "e") { print("ordem"); }
if (true || substr("", 0, 1) == "x") { print("or"); }
print("[" + substr("abc", 1, 0) + "]");
''', stdout='ação é🙂 é🙂! [vazio] ok\na\t"\\b\n2 4\nordem\nor\n[]\n')
    yield dict(id="EXTRA-NUMEROS", source='''var v = [42, 0 - 84, 0];
print(to_string(v[0]), to_string(v[1]), to_string(v[2]));
print(to_string(to_number("100000000000000000000")));
print(to_string(to_number("-0")));
print(to_string(1.25));
print(substr("abc", 1.0, 2.0));
''', stdout="42 -84 0\n100000000000000000000\n0\n1.25\nbc\n")
    # Mesmo programa com variacoes de entrada: nao reconhecer nome, fonte ou constantes.
    yield dict(id="EXTRA-ENTRADA", source='''var e = input(); var i = 0; var s = "";
while (i < len(e)) { s = substr(e, i, 1) + s; i = i + 1; }
print(s); print(to_string(len(e)));
''', stdin="(7+8)*3\n", stdout="3*)8+7(\n7\n")
    for label, start, size in [("FRAC-TAMANHO", "0", "0.5"),
                               ("NAN", 'to_number("nan")', "0"),
                               ("INF", "0", 'to_number("inf")'),
                               ("ENORME", 'to_number("1e300")', "0")]:
        yield dict(id="EXTRA-ERR-" + label,
                   source=f'print("antes"); print(substr("abc", {start}, {size}));',
                   stdout="antes\n", exit_code=1,
                   stderr_contains=["substr", "inicio", "tamanho", "len"])
    for label, source in {
        "SUBSTR-TIPO": 'print(substr(3, 0, 1));',
        "SUBSTR-INDICE-TIPO": 'print(substr("abc", "0", 1));',
        "SUBSTR-ARIDADE": 'print(substr("abc", 0, 1, 2));',
        "TOSTRING-TIPO": 'print(to_string("3"));',
        "TOSTRING-ARIDADE": 'print(to_string());',
        "LEN-TIPO": 'print(len(3));',
        "LEN-ARIDADE": 'print(len());',
        "LISTA-STRING": 'var l = ["a", "b"]; print(l[1]);',
        "APPEND-STRING": 'var l = []; l.append("x");',
        "ATRIBUTO-NUMERO": 'class T { var s = "a"; } var t = new T(); print(t.s + 3);',
        "FUNCAO-NUMERO": 'func f() { return "x"; } print(f() + 3);',
        "PARAMETRO-NUMERO": 'func f(s) { return s == 3; } print(f("x"));',
        "SUBSTR-PARAMETRO-BOOL": 'func f(i) { return substr("abc", i, 1); } print(f(true));',
    }.items():
        yield dict(id="EXTRA-NEG-" + label, source=source, compile_error=True)


def run(command, cwd, env, stdin="", timeout=150):
    result = subprocess.run(command, cwd=cwd, env=env, input=stdin.encode("utf-8"),
                            capture_output=True, timeout=timeout)
    return dict(command=[str(a) for a in command], exit_code=result.returncode,
                stdout=result.stdout.decode("utf-8").replace("\r\n", "\n"),
                stderr=result.stderr.decode("utf-8").replace("\r\n", "\n"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", help="Executar somente o ID informado (repetivel)")
    args = parser.parse_args()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    parent = ROOT / "output/core03"
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="run-", dir=parent))
    results = []
    selected = list(cases())
    if args.case:
        unknown = set(args.case) - {c["id"] for c in selected}
        if unknown:
            parser.error(f"IDs desconhecidos: {sorted(unknown)}")
        selected = [c for c in selected if c["id"] in args.case]
    for case in selected:
        folder = work / case["id"]
        folder.mkdir()
        source = folder / "program.minipar"
        source.write_text(case["source"], encoding="utf-8", newline="\n")
        result = dict(case=case, status="FAIL")
        try:
            compilation = run([sys.executable, str(ROOT / "main.py"), str(source), "program"], folder, env)
            result["compile"] = compilation
            binary = folder / "output/program.exe"
            if case.get("compile_error"):
                assert compilation["exit_code"] == 1 and not binary.exists(), "Rejeicao esperada sem binario"
                assert compilation["stderr"], "Diagnostico ausente"
                assert case.get("diagnostic", "") in compilation["stderr"], "Diagnostico incorreto"
            else:
                assert compilation["exit_code"] == 0 and binary.is_file(), "Compilacao falhou"
                assert not compilation["stderr"], "Diagnostico inesperado na compilacao"
                execution = run([str(binary)], folder, env, case.get("stdin", ""), timeout=10)
                result["run"] = execution
                assert execution["exit_code"] == case.get("exit_code", 0), "Exit code divergente"
                assert execution["stdout"] == case["stdout"], "Stdout divergente"
                if case.get("stderr_contains"):
                    assert all(s in execution["stderr"] for s in case["stderr_contains"]), "Diagnostico incompleto"
                else:
                    assert execution["stderr"] == "", "Stderr inesperado"
            result["status"] = "KNOWN_FAIL" if case.get("known_defect") else "PASS"
        except (AssertionError, OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
            result["error"] = str(exc)
        (folder / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        results.append(result)
        print(f'{case["id"]}: {result["status"]} {result.get("error", "")}', flush=True)
    files = ["main.py", "src/semantic.py", "src/codegen.py", "src/cpp_template.py",
             "docs/02_CONTRATOS_TECNICOS.md", "tests/2026_2/core03/verify_core03.py"]
    summary = dict(python=sys.version, platform=platform.platform(),
                   compiler=run([env.get("CXX", "g++"), "--version"], ROOT, env),
                   hashes={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
                   results=results)
    (work / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(r["status"] == "PASS" for r in results)
    known = sum(r["status"] == "KNOWN_FAIL" for r in results)
    print(f"{passed} PASS, {known} KNOWN_FAIL, {len(results) - passed - known} FAIL; evidencias: {work / 'summary.json'}")
    return int(passed + known != len(results))


if __name__ == "__main__":
    raise SystemExit(main())
