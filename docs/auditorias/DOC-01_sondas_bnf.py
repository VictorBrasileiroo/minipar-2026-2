"""DOC-01 — sondas que confrontam a BNF e os pseudocódigos com o código real.

Uso (na raiz do repositório):

    python docs/auditorias/DOC-01_sondas_bnf.py            # imprime o resumo
    python docs/auditorias/DOC-01_sondas_bnf.py --json F   # grava também o JSON

Somente leitura: importa `src/` e não altera arquivos fora do JSON pedido.
Cada caso declara o resultado esperado pela documentação (BNF/pseudocódigo)
e é comparado com o comportamento observado do Lexer, Parser e Semântico.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from lexer import Lexer, TokenType  # noqa: E402
from parser import Parser, ParseError  # noqa: E402
from semantic import SemanticAnalyzer  # noqa: E402


def lex(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    return [(t.type.name, t.lexeme) for t in tokens[:-1]], [d["code"] for d in lexer.diagnostics]


def parse(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    if lexer.diagnostics:
        return "lexer", lexer.diagnostics[0]["code"], None
    try:
        program = Parser(tokens, exit_on_error=False).parse()
    except ParseError as exc:
        return "reject", exc.diagnostic["code"], None
    return "accept", None, program


def analyze(source):
    status, code, program = parse(source)
    if status != "accept":
        return status, [code], None
    semantic = SemanticAnalyzer(emit_diagnostics=False)
    with redirect_stderr(io.StringIO()):
        ok = semantic.analyze(program)
    codes = [d["message"].split(":")[0] if d["message"].startswith("FJ-") else d["code"]
             for d in semantic.diagnostics]
    return ("ok" if ok else "error"), codes, semantic


# --------------------------------------------------------------------------
# 1. Léxico: (id, fonte, tokens esperados [(tipo, lexema)], códigos esperados)
LEX_CASES = [
    ("LEX-01 palavras reservadas FJ", "fork join on", [("FORK", "fork"), ("JOIN", "join"), ("ON", "on")], []),
    ("LEX-02 tipos são TYPE", "number int string bool void list dict",
     [("TYPE", w) for w in "number int string bool void list dict".split()], []),
    ("LEX-03 true/false são BOOL_LITERAL", "true false", [("BOOL_LITERAL", "true"), ("BOOL_LITERAL", "false")], []),
    ("LEX-04 número inteiro, real e '1.'", "12 3.25 1.",
     [("NUMBER", "12"), ("NUMBER", "3.25"), ("NUMBER", "1.")], []),
    ("LEX-05 '.5' não é número", ".5", [("DOT", "."), ("NUMBER", "5")], []),
    ("LEX-06 escapes conhecidos", r'"a\nb\t\"\\"', [("STRING_LITERAL", 'a\nb\t"\\')], []),
    ("LEX-07 escape desconhecido descarta a barra", r'"\q"', [("STRING_LITERAL", "q")], []),
    ("LEX-08 string sem fechamento", '"abc', [("STRING_LITERAL", "abc")], ["LEX_UNTERMINATED_STRING"]),
    ("LEX-09 operadores de dois caracteres", "== != <= >= && ||",
     [("EQ", "=="), ("NEQ", "!="), ("LTE", "<="), ("GTE", ">="), ("AND", "&&"), ("OR", "||")], []),
    ("LEX-10 '&' e '|' isolados", "& |", [("UNKNOWN", "&"), ("UNKNOWN", "|")], ["LEX_UNKNOWN_CHAR", "LEX_UNKNOWN_CHAR"]),
    ("LEX-11 caractere desconhecido", "@", [("UNKNOWN", "@")], ["LEX_UNKNOWN_CHAR"]),
    ("LEX-12 comentário até o fim da linha", "var x; # comentario\nx",
     [("VAR", "var"), ("IDENTIFIER", "x"), ("SEMICOLON", ";"), ("IDENTIFIER", "x")], []),
    ("LEX-13 identificador com letra Unicode (str.isalpha)", "ação_1", [("IDENTIFIER", "ação_1")], []),
    ("LEX-14 '!' isolado é NOT", "!x", [("NOT", "!"), ("IDENTIFIER", "x")], []),
]

# --------------------------------------------------------------------------
# 2. Sintaxe: (id, produção, fonte, "accept"|"reject", código esperado)
SYN_CASES = [
    ("SYN-01", "<declaracao_variavel> var", "var x = 1;", "accept", None),
    ("SYN-02", "<declaracao_variavel> tipo", "int x = 1; string s; list l = [1];", "accept", None),
    ("SYN-03", "<declaracao_variavel> exige ';'", "var x = 1", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-04", "<declaracao_funcao> com parâmetro tipado", "func f(number a, b) { return a + b; }", "accept", None),
    ("SYN-05", "<declaracao_funcao> exige bloco '{'", "func f() return 1;", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-06", "<declaracao_classe> extends + membros",
     "class A { var x = 1; func get() { return this.x; } } class B extends A { }", "accept", None),
    ("SYN-07", "<membro_classe> não aceita declaração tipada", "class A { int x; }", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-08", "<comando_return> com ';' opcional", "func f() { return 1 }", "accept", None),
    ("SYN-09", "<comando_break>/<comando_continue> com ';' opcional",
     "while (true) { break } while (true) { continue }", "accept", None),
    ("SYN-10", "<bloco_seq> com e sem 'seq'", "seq { var a = 1; } { var b = 2; }", "accept", None),
    ("SYN-11", "<bloco_par>", "par { print(1); print(2); }", "accept", None),
    ("SYN-12", "<comando_if> else-if encadeado", "if (1 < 2) print(1); else if (2 < 3) print(2); else print(3);", "accept", None),
    ("SYN-13", "<comando_do_while> com ';' opcional", "do { print(1); } while (false) do print(2); while (false);", "accept", None),
    ("SYN-14", "<for_classico> todas as partes", "for (var i = 0; i < 3; i = i + 1) print(i);", "accept", None),
    ("SYN-15", "<for_classico> partes vazias", "for (;;) { break; }", "accept", None),
    ("SYN-16", "<for_classico> inicializador tipado", "for (int i = 0; i < 3; i = i + 1) print(i);", "accept", None),
    ("SYN-17", "<for_iterador> exige 'var'", "for (var x in [1, 2]) print(x);", "accept", None),
    ("SYN-18", "<for_iterador> sem 'var' não é aceito", "var x; for (x in [1, 2]) print(x);", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-19", "<comando_print> sem argumentos", "print();", "accept", None),
    ("SYN-20", "<comando_send>", 'var c = c_channel("127.0.0.1", 9000); send(c, "oi");', "accept", None),
    ("SYN-21", "<comando_expressao> chamada de função", "f(1, 2);", "accept", None),
    ("SYN-22", "<comando_expressao> chamada de método encadeada", "a.b.c(1);", "accept", None),
    ("SYN-23", "<comando_expressao> rejeita expressão sem efeito", "x + 1;", "reject", "SYN_INVALID_STATEMENT"),
    ("SYN-24", "<comando_expressao> rejeita 'input()' isolado", "input();", "reject", "SYN_INVALID_STATEMENT"),
    ("SYN-25", "<comando> não começa com literal", "1;", "reject", "SYN_UNRECOGNIZED_STATEMENT"),
    ("SYN-26", "<comando> não começa com '('", "(f());", "reject", "SYN_UNRECOGNIZED_STATEMENT"),
    ("SYN-27", "<atribuicao> a propriedade e índice", "this.x = 1; a[0][1] = 2; m.v[0] = 3;", "accept", None),
    ("SYN-28", "<atribuicao> alvo inválido", "f() = 1;", "reject", "SYN_INVALID_ASSIGNMENT"),
    ("SYN-29", "<expressao_fork> com e sem 'on'", 'var h = fork f(1); var g = fork f(2) on "local";', "accept", None),
    ("SYN-30", "<expressao_fork> exige identificador", "var h = fork (f)(1);", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-31", "<expressao_join> com timeout", "var r = join(h, 1000);", "accept", None),
    ("SYN-32", "<comando_expressao> fork/join como comando (sintaxe)", "fork f(1); join(h);", "accept", None),
    ("SYN-33", "<expressao_matrix> exige 3 argumentos", "var m = matrix(2, 2);", "reject", "SYN_EXPECTED_TOKEN"),
    ("SYN-34", "<expressao_input> com e sem prompt", 'var a = input(); var b = input("p: ");', "accept", None),
    ("SYN-35", "<expressao_new> com argumentos", "var o = new A(1, 2);", "accept", None),
    ("SYN-36", "<expressao_lista> vazia e aninhada", "var l = []; var m = [[1], [2, 3]];", "accept", None),
    ("SYN-37", "<expressao_unaria> repetida", "var x = - - !true;", "accept", None),
    ("SYN-38", "<expressao_posfixo> após primária parentizada", "var n = (l)[0];", "accept", None),
    ("SYN-39", "<declaracao_funcao> aninhada em bloco (comando)", "seq { func g() { return 1; } }", "accept", None),
    ("SYN-40", "<expressao_primaria> ausente", "var x = ;", "reject", "SYN_EXPECTED_EXPRESSION"),
]

# Precedência e associatividade: (id, fonte da expressão, forma parentizada esperada)
PREC_CASES = [
    ("PREC-01 * antes de +", "1 + 2 * 3", "(1 + (2 * 3))"),
    ("PREC-02 + esquerda", "1 - 2 - 3", "((1 - 2) - 3)"),
    ("PREC-03 comparações no mesmo nível, esquerda", "1 < 2 == true", "((1 < 2) == true)"),
    ("PREC-04 && antes de ||", "a || b && c", "(a || (b && c))"),
    ("PREC-05 unário antes de *", "-a * b", "((-a) * b)"),
    ("PREC-06 posfixo antes de unário", "-l[0]", "(-l[0])"),
    ("PREC-07 'on' consome expressão completa", "fork f() on d + 1", "fork f() on (d + 1)"),
]

# --------------------------------------------------------------------------
# 3. Semântico: (id, fonte, "ok"|"error", códigos esperados (subconjunto))
SEM_CASES = [
    ("SEM-01 não declarada", "print(x);", "error", ["SEM_UNDECLARED_VARIABLE"]),
    ("SEM-02 redeclaração no mesmo escopo", "var x = 1; var x = 2;", "error", ["SEM_REDECLARED"]),
    ("SEM-03 sombreamento em escopo interno", "var x = 1; seq { var x = 2; }", "ok", []),
    ("SEM-04 tipo incompatível", 'int x = "a";', "error", ["SEM_TYPE_MISMATCH"]),
    ("SEM-05 int e number compatíveis", "int x = 1.5;", "ok", []),
    ("SEM-06 break fora de laço", "break;", "error", ["SEM_OUTSIDE_LOOP"]),
    ("SEM-07 aridade de função", "func f(a) { return a; } print(f(1, 2));", "error", ["SEM_ARITY"]),
    ("SEM-08 função não declarada", "g();", "error", ["SEM_UNDECLARED_FUNCTION"]),
    ("SEM-09 nome nativo reservado", "func len(x) { return 1; }", "error", ["SEM_RESERVED_NAME"]),
    ("SEM-10 string + número sem conversão", 'print("a" + 1);', "error", ["SEM_TYPE_MISMATCH"]),
    ("SEM-11 operador aritmético exige números", 'print("a" * 2);', "error", ["SEM_NUMERIC_OPERANDS"]),
    ("SEM-12 indexação de string", 'var s = "ab"; print(s[0]);', "error", ["SEM_UNSUPPORTED_FEATURE"]),
    ("SEM-13 lista de strings", 'var l = ["a"];', "error", ["SEM_UNSUPPORTED_FEATURE"]),
    ("SEM-14 superclasse não declarada", "class B extends A { }", "error", ["SEM_UNDECLARED_SUPERCLASS"]),
    ("SEM-15 atributo herdado", "class A { var x = 1; } class B extends A { } var b = new B(); print(b.x);", "ok", []),
    ("SEM-16 atributo inexistente", "class A { var x = 1; } var a = new A(); print(a.y);", "error", ["SEM_UNDECLARED_ATTRIBUTE"]),
    ("SEM-17 método inexistente", "class A { } var a = new A(); a.m();", "error", ["SEM_UNDECLARED_METHOD"]),
    ("SEM-18 classe não declarada", "var a = new Z();", "error", ["SEM_UNDECLARED_CLASS"]),
    ("SEM-19 substr com tipo errado", 'print(substr(1, 0, 1));', "error", ["SEM_TYPE_MISMATCH"]),
    ("SEM-20 função declarada depois do uso", "print(f()); func f() { return 1; }", "ok", []),
    # Fork/Join
    ("FJ-01 fork de função global válida", "func f(a) { return a * 2; } var h = fork f(3); print(join(h));", "ok", []),
    ("FJ-02 fork de nome não global (FJ-SEM-01)", "var f = 1; var h = fork f();", "error", ["FJ-SEM-01"]),
    ("FJ-03 fork de método (FJ-SEM-01)", "class A { func m() { return 1; } } var h = fork m();", "error", ["FJ-SEM-01"]),
    ("FJ-04 aridade (FJ-SEM-02 / SEM_ARITY)", "func f(a) { return a; } var h = fork f();", "error", ["FJ-SEM-02"]),
    ("FJ-05 join de não-task (FJ-SEM-03)", "var x = 1; print(join(x));", "error", ["FJ-SEM-03"]),
    ("FJ-06 destino não string (FJ-SEM-04)", "func f() { return 1; } var h = fork f() on 5; print(join(h));", "error", ["FJ-SEM-04"]),
    ("FJ-07 timeout não numérico (FJ-SEM-04)", 'func f() { return 1; } var h = fork f(); print(join(h, "x"));', "error", ["FJ-SEM-04"]),
    ("FJ-08 global mutável na tarefa (FJ-SEM-05)", "var g = 1; func f() { return g; } var h = fork f(); print(join(h));", "error", ["FJ-SEM-05"]),
    ("FJ-09 global mutável transitivo (FJ-SEM-05)",
     "var g = 1; func k() { return g; } func f() { return k(); } var h = fork f(); print(join(h));", "error", ["FJ-SEM-05"]),
    ("FJ-10 input na tarefa (FJ-SEM-05)", "func f() { var s = input(); return 1; } var h = fork f(); print(join(h));", "error", ["FJ-SEM-05"]),
    ("FJ-11 objeto como argumento (FJ-SEM-06)",
     "class A { var x = 1; } func f(o) { return 1; } var a = new A(); var h = fork f(a); print(join(h));", "error", ["FJ-SEM-06"]),
    ("FJ-12 aritmética com handle (FJ-SEM-06)", "func f() { return 1; } var h = fork f(); print(h + 1);", "error", ["FJ-SEM-06"]),
    ("FJ-13 handle descartado (FJ-SEM-07)", "func f() { return 1; } fork f();", "error", ["FJ-SEM-07"]),
    ("FJ-14 none usado como valor (FJ-SEM-08)", "func f() { print(1); } var h = fork f(); print(join(h));", "error", ["FJ-SEM-08"]),
    ("FJ-15 join de none como comando", "func f() { print(1); } var h = fork f(); join(h);", "ok", []),
    ("FJ-16 lista de handles + for-in",
     "func f(i) { return i; } var hs = []; for (var i in range(3)) { hs.append(fork f(i)); } "
     "for (var h in hs) { print(join(h)); }", "ok", []),
]

# 4. Tabela de símbolos: (id, fonte, [(nome, kind, type, kind_do_escopo)])
SYMTAB_CASES = [
    ("SYM-01 kinds publicados",
     "class A { var x = 1; func m(p) { return p; } } func f(a) { var l = 2; return a + l; } "
     "for (var i in [1]) print(i);",
     [("A", "class", None, "global"), ("x", "attribute", "number", "class"), ("m", "method", None, "class"),
      ("p", "parameter", "var", "method"), ("f", "function", None, "global"), ("a", "parameter", "var", "function"),
      ("l", "variable", "number", "seq"), ("i", "iterator", "var", "for")]),
]


def render(node):
    """Parentização mínima da AST de expressões, para checar precedência."""
    name = type(node).__name__
    if name == "BinaryExpr":
        return f"({render(node.left)} {node.op} {render(node.right)})"
    if name == "UnaryExpr":
        return f"({node.op}{render(node.operand)})"
    if name == "NumberExpr":
        return node.value
    if name == "BoolExpr":
        return "true" if node.value else "false"
    if name == "IdentifierExpr":
        return node.name
    if name == "IndexExpr":
        return f"{render(node.object)}[{render(node.index)}]"
    if name == "ForkExpr":
        dest = f" on {render(node.destination)}" if node.destination else ""
        return f"fork {node.function_name}({', '.join(render(a) for a in node.arguments)}){dest}"
    return name


def main(argv):
    results = []

    for cid, src, tokens, codes in LEX_CASES:
        got_tokens, got_codes = lex(src)
        ok = got_tokens == tokens and got_codes == codes
        results.append(dict(id=cid, kind="lexer", status="PASS" if ok else "FAIL",
                            expected=dict(tokens=tokens, codes=codes), observed=dict(tokens=got_tokens, codes=got_codes)))

    for cid, prod, src, expect, code in SYN_CASES:
        status, got_code, _ = parse(src)
        ok = status == expect and (code is None or got_code == code)
        results.append(dict(id=cid, kind="parser", production=prod, status="PASS" if ok else "FAIL",
                            expected=dict(result=expect, code=code), observed=dict(result=status, code=got_code)))

    for cid, expr, shape in PREC_CASES:
        status, code, program = parse(f"var r = {expr};")
        got = render(program.statements[0].init_value) if status == "accept" else f"{status}:{code}"
        results.append(dict(id=cid, kind="precedence", status="PASS" if got == shape else "FAIL",
                            expected=shape, observed=got))

    for cid, src, expect, codes in SEM_CASES:
        status, got_codes, _ = analyze(src)
        ok = status == expect and all(c in got_codes for c in codes) and (expect == "error" or not got_codes)
        results.append(dict(id=cid, kind="semantic", status="PASS" if ok else "FAIL",
                            expected=dict(result=expect, codes=codes), observed=dict(result=status, codes=got_codes)))

    for cid, src, expected in SYMTAB_CASES:
        status, codes, semantic = analyze(src)
        kinds = {s["id"]: s["kind"] for s in semantic.scopes} if semantic else {}
        got = [(s["name"], s["kind"], s["type"], kinds[s["scope"]]) for s in semantic.symbols] if semantic else []
        ok = status == "ok" and all(tuple(e) in [tuple(g) for g in got] for e in expected)
        results.append(dict(id=cid, kind="symbols", status="PASS" if ok else "FAIL",
                            expected=expected, observed=dict(result=status, codes=codes, symbols=got)))

    # 5. Programas reais do repositório: devem ser aceitos pelo Lexer/Parser.
    for path in sorted(ROOT.glob("tests/**/*.minipar")):
        status, code, _ = parse(path.read_text(encoding="utf-8"))
        results.append(dict(id=f"REAL {path.relative_to(ROOT).as_posix()}", kind="corpus",
                            status="PASS" if status == "accept" else "FAIL",
                            expected="accept", observed=f"{status}:{code}" if code else status))

    passed = sum(r["status"] == "PASS" for r in results)
    for r in results:
        if r["status"] != "PASS":
            print(f"FAIL {r['id']}: esperado={r['expected']} observado={r['observed']}")
    print(f"DOC-01 sondas: {passed}/{len(results)} PASS")
    if "--json" in argv:
        out = Path(argv[argv.index("--json") + 1])
        out.write_text(json.dumps(dict(card="DOC-01", python=sys.version.split()[0], passed=passed,
                                       total=len(results), results=results), ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
