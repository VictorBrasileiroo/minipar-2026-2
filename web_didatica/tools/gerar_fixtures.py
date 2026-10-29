"""Gera as fixtures mock da Web didática (card WEB-01) a partir das fases reais do compilador.

Uso, na raiz do repositório:
    py -B web_didatica/tools/gerar_fixtures.py

O script só LÊ `src/`: importa Lexer, Parser, SemanticAnalyzer, TACGenerator e
CppCodeGenerator e serializa o resultado no formato `minipar.compile.v1` /
`minipar.execute.v1` do contrato C-WEB-v1 (docs/02_CONTRATOS_TECNICOS.md, §1).

Não é o serviço de fases. Quem fornece `src/service.py` é o Eixo A (CORE-08); este
gerador existe só para produzir dados de exemplo enquanto o serviço não existe e
nunca é chamado pela Web. Onde o compilador atual ainda não faz o que o contrato
pede, o gerador reproduz o comportamento CONTRATADO e marca isso na fixture:
  - PEND-WEB-01: tokens UNKNOWN viram erro LEX_UNKNOWN_CHAR (o lexer atual não acusa);
  - PEND-WEB-02: o sys.exit do parser é capturado e vira diagnóstico;
  - PEND-WEB-03: escopos e símbolos são registrados por observação (subclasse), sem editar src/;
  - PEND-WEB-04: o texto C++ é lido do .cpp que o gerador atual grava num diretório temporário.
"""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "web_didatica" / "fixtures"
sys.path.insert(0, str(ROOT / "src"))

import ast_nodes  # noqa: E402
from ast_nodes import ClassDecl, ForStmt, FuncDecl, ParBlock, SeqBlock, VarDecl  # noqa: E402
from codegen import CppCodeGenerator  # noqa: E402
from lexer import Lexer, TokenType  # noqa: E402
from parser import Parser  # noqa: E402
from semantic import SemanticAnalyzer  # noqa: E402
from tac import TACGenerator  # noqa: E402

PHASES = ("lexer", "parser", "semantic", "tac", "cpp", "gpp")
WORKDIRS: list[Path] = []  # diretórios temporários do codegen, apagados no fim
REQUESTED = {"analyze": PHASES[:5], "compile": PHASES}
MAX_NODES = 5000
MAX_DEPTH = 200

# Nomes de todas as classes de nó: um campo cuja anotação cita um deles é campo de nó (§1.4).
NODE_CLASS_NAMES = {name for name, obj in vars(ast_nodes).items()
                    if isinstance(obj, type) and issubclass(obj, ast_nodes.ASTNode)}
LABEL_ATTRS = ("op", "name", "value", "class_name", "method_name", "property_name")


# ---------------------------------------------------------------- lexer

def run_lexer(source: str) -> tuple[dict, list, list]:
    """Devolve o payload da fase, os diagnósticos e a lista completa (com END_OF_FILE) para o parser."""
    all_tokens = Lexer(source).tokenize()
    tokens = [t for t in all_tokens if t.type is not TokenType.END_OF_FILE]
    payload = [{"type": t.type.name, "lexeme": t.lexeme, "line": t.line, "column": t.col} for t in tokens]
    # Comportamento contratado (PEND-WEB-01): o lexer atual só gera o token UNKNOWN.
    diags = [diag("lexer", "LEX_UNKNOWN_CHAR", f"Caractere desconhecido '{t.lexeme}'", t.line, t.col)
             for t in tokens if t.type is TokenType.UNKNOWN]
    status = "error" if diags else "ok"
    return {"status": status, "tokens": payload}, diags, all_tokens


# ---------------------------------------------------------------- parser

SYN_PATTERNS = (
    (re.compile(r"^\[ERRO SINTATICO\] Linha (\d+): Expressao esperada$"), "SYN_EXPECTED_EXPRESSION", True),
    (re.compile(r"^\[ERRO SINTATICO\] Linha (\d+): (Instrucao nao reconhecida: .*)$"), "SYN_UNRECOGNIZED_STATEMENT", True),
    (re.compile(r"^\[ERRO SINTATICO\] Linha (\d+): (.* \(Encontrado: .*\))$"), "SYN_EXPECTED_TOKEN", True),
    (re.compile(r"^\[ERRO\] Linha (\d+): Atribuicao invalida$"), "SYN_INVALID_ASSIGNMENT", False),
    (re.compile(r"^\[ERRO\] Linha (\d+): Instrucao ou expressao isolada invalida$"), "SYN_INVALID_STATEMENT", False),
)
SYN_FIXED_MESSAGE = {
    "SYN_EXPECTED_EXPRESSION": "Expressao esperada",
    "SYN_INVALID_ASSIGNMENT": "Atribuicao invalida",
    "SYN_INVALID_STATEMENT": "Instrucao ou expressao isolada invalida",
}


def run_parser(tokens_with_eof) -> tuple[dict, list, object]:
    parser = Parser(tokens_with_eof)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            program = parser.parse()
    except SystemExit:
        line_text = err.getvalue().strip().splitlines()[-1] if err.getvalue().strip() else ""
        for pattern, code, knows_column in SYN_PATTERNS:
            m = pattern.match(line_text)
            if m:
                message = SYN_FIXED_MESSAGE.get(code) or m.group(2)
                # Nesses três pontos o parser acusa o token em _peek(), que não foi consumido.
                column = parser._peek().col if knows_column else None
                return {"status": "error"}, [diag("parser", code, message, int(m.group(1)), column)], None
        return {"status": "error"}, [diag("internal", "INTERNAL_ERROR", "Erro sintatico nao classificado", None, None,
                                          detail=line_text)], None
    ast, stats = serialize_ast(program)
    return {"status": "ok", "ast": ast, "ast_stats": stats}, [], program


def node_fields(node):
    """Separa campos de nó e de atributo pelo tipo DECLARADO no dataclass (§1.4)."""
    child_fields, attrs = [], {}
    for f in dataclasses.fields(node):
        if f.name == "line":
            continue
        annotation = f.type if isinstance(f.type, str) else getattr(f.type, "__name__", str(f.type))
        is_node = any(name in NODE_CLASS_NAMES for name in re.findall(r"[A-Za-z_]\w*", annotation))
        value = getattr(node, f.name)
        if is_node:
            if isinstance(value, list):
                child_fields.extend((f.name, i, v) for i, v in enumerate(value) if v is not None)
            elif value is not None:
                child_fields.append((f.name, None, value))
        else:
            attrs[f.name] = list(value) if isinstance(value, list) else value
    return child_fields, attrs


def make_label(kind: str, attrs: dict) -> str:
    for key in LABEL_ATTRS:
        value = attrs.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif kind == "StringExpr" and key == "value":
            text = json.dumps(value, ensure_ascii=False)
        else:
            text = str(value)
        if len(text) > 40:
            text = text[:39] + "…"
        return f"{kind}({text})"
    return kind


def subtree_size(node) -> int:
    total, stack = 0, [node]
    while stack:
        current = stack.pop()
        total += 1
        stack.extend(child for _, _, child in node_fields(current)[0])
    return total


def subtree_depth(node) -> int:
    best, stack = 0, [(node, 1)]
    while stack:
        current, depth = stack.pop()
        best = max(best, depth)
        stack.extend((child, depth + 1) for _, _, child in node_fields(current)[0])
    return best


def serialize_ast(program):
    """Pré-ordem iterativa (sem recursão) com os limites e marcadores de truncamento do §1.4."""
    counters = {"n": 0, "x": 0}

    def make(node, role, index):
        children, attrs = node_fields(node)
        kind = type(node).__name__
        out = {"id": f"n{counters['n']}", "kind": kind, "label": make_label(kind, attrs), "role": role,
               "index": index, "line": node.line, "attributes": attrs, "children": []}
        counters["n"] += 1
        return out, children

    def marker(reason, omitted, first):
        role, index, node = first
        out = {"id": f"x{counters['x']}", "kind": "Truncated", "label": f"Truncated({omitted} nós)", "role": role,
               "index": index, "line": node.line, "attributes": {"reason": reason, "omitted_nodes": omitted},
               "children": []}
        counters["x"] += 1
        return out

    root, root_children = make(program, None, None)
    # Cada quadro: (saída, filhos pendentes, próximo índice, profundidade, filhos omitidos por max_nodes)
    stack = [[root, root_children, 0, 1, []]]
    while stack:
        frame = stack[-1]
        out, pending, i, depth, omitted = frame
        if i >= len(pending):
            if omitted:
                out["children"].append(marker("max_nodes", sum(subtree_size(c[2]) for c in omitted), omitted[0]))
            stack.pop()
            continue
        frame[2] += 1
        child = pending[i]
        if depth + 1 > MAX_DEPTH:
            out["children"].append(marker("max_depth", subtree_size(child[2]), child))
            continue
        if counters["n"] >= MAX_NODES:
            omitted.append(child)
            continue
        child_out, grandchildren = make(child[2], child[0], child[1])
        out["children"].append(child_out)
        stack.append([child_out, grandchildren, 0, depth + 1, []])

    nodes = subtree_size(program)
    stats = {"nodes": nodes, "emitted": counters["n"], "depth": subtree_depth(program),
             "truncated": counters["n"] < nodes, "max_nodes": MAX_NODES, "max_depth": MAX_DEPTH}
    return root, stats


# ---------------------------------------------------------------- semantic

SEM_CODES = (
    (re.compile(r"^Variavel '.*' ja declarada\.$"), "SEM_REDECLARED"),
    (re.compile(r"^Variavel '.*' nao declarada\.$"), "SEM_UNDECLARED_VARIABLE"),
    (re.compile(r"^Tipo incompativel"), "SEM_TYPE_MISMATCH"),
    (re.compile(r"^Operador '.*' exige operandos numericos\.$"), "SEM_NUMERIC_OPERANDS"),
    (re.compile(r"usado fora de laco\.$"), "SEM_OUTSIDE_LOOP"),
    (re.compile(r"espera \d+ argumento\(s\), recebeu \d+\.$"), "SEM_ARITY"),
    (re.compile(r"^Funcao '.*' nao declarada\.$"), "SEM_UNDECLARED_FUNCTION"),
    (re.compile(r"^Superclasse '.*' nao declarada\.$"), "SEM_UNDECLARED_SUPERCLASS"),
    (re.compile(r"^Classe '.*' nao declarada\.$"), "SEM_UNDECLARED_CLASS"),
    (re.compile(r"^Metodo '.*' nao declarado em '.*'\.$"), "SEM_UNDECLARED_METHOD"),
    (re.compile(r"^Atributo '.*' nao declarado em '.*'\.$"), "SEM_UNDECLARED_ATTRIBUTE"),
)
SEM_LINE = re.compile(r"^\[ERRO SEMANTICO\] Linha (\d+)(?: \(Funcao: [^)]*\))?: (.*)$")


class ObservedSemantic(SemanticAnalyzer):
    """Registra escopos e símbolos no momento em que o semântico real os cria (PEND-WEB-03)."""

    def __init__(self) -> None:
        self.obs_scopes: list[dict] = []
        self.obs_symbols: list[dict] = []
        self._scope_ids: list[str] = []
        self._node_stack: list = []
        super().__init__()

    def validate_node(self, node) -> None:
        self._node_stack.append(node)
        try:
            super().validate_node(node)
        finally:
            self._node_stack.pop()

    def _enter_scope(self) -> None:
        node = self._node_stack[-1] if self._node_stack else None
        if node is None:
            kind, name, line = "global", None, 1
        elif isinstance(node, ClassDecl):
            kind, name, line = "class", node.name, node.line
        elif isinstance(node, FuncDecl):
            if self._current_class:
                kind, name = "method", f"{self._current_class}.{node.name}"
            else:
                kind, name = "function", node.name
            line = node.line
        elif isinstance(node, SeqBlock):
            kind, name, line = "seq", None, node.line
        elif isinstance(node, ParBlock):
            kind, name, line = "par", None, node.line
        elif isinstance(node, ForStmt):
            kind, name, line = "for", None, node.line
        else:
            raise RuntimeError(f"escopo aberto por nó inesperado: {type(node).__name__}")
        scope_id = f"s{len(self.obs_scopes)}"
        self.obs_scopes.append({"id": scope_id, "kind": kind, "name": name,
                                "parent": self._scope_ids[-1] if self._scope_ids else None, "line": line})
        self._scope_ids.append(scope_id)
        super()._enter_scope()

    def _exit_scope(self) -> None:
        if len(self._scopes) > 1:
            self._scope_ids.pop()
        super()._exit_scope()

    def _define_symbol(self, name, type_, line, params=None) -> None:
        if name not in self._scopes[-1]:
            node = self._node_stack[-1]
            scope_kind = self.obs_scopes[int(self._scope_ids[-1][1:])]["kind"]
            if isinstance(node, VarDecl):
                kind = "attribute" if scope_kind == "class" else "variable"
            elif isinstance(node, FuncDecl):
                kind = ("method" if scope_kind == "class" else "function") if name == node.name else "parameter"
            elif isinstance(node, ClassDecl):
                kind = "class"
            elif isinstance(node, ForStmt):
                kind = "iterator"
            else:
                raise RuntimeError(f"símbolo definido por nó inesperado: {type(node).__name__}")
            if kind in ("function", "method", "class"):
                published_type = None
            elif type_ in ("FUNC", "CLASS", "unknown"):
                published_type = "var"
            else:
                published_type = type_
            self.obs_symbols.append({"name": name, "kind": kind, "type": published_type,
                                     "scope": self._scope_ids[-1], "line": line,
                                     "params": list(params or []) if kind in ("function", "method") else []})
        super()._define_symbol(name, type_, line, params)


def run_semantic(program) -> tuple[dict, list]:
    analyzer = ObservedSemantic()
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        ok = analyzer.analyze(program)
    diags = []
    for raw in err.getvalue().splitlines():
        m = SEM_LINE.match(raw)
        if not m:
            diags.append(diag("internal", "INTERNAL_ERROR", "Mensagem semantica nao classificada", None, None, detail=raw))
            continue
        message = m.group(2)
        code = next((c for pattern, c in SEM_CODES if pattern.search(message)), None)
        if code is None:
            diags.append(diag("internal", "INTERNAL_ERROR", "Mensagem semantica nao classificada", None, None, detail=raw))
            continue
        diags.append(diag("semantic", code, message, int(m.group(1)), None))
    diags.sort(key=lambda d: d["line"] or 0)
    return {"status": "ok" if ok else "error", "scopes": analyzer.obs_scopes, "symbols": analyzer.obs_symbols}, diags


# ---------------------------------------------------------------- tac, cpp, gpp

def run_tac(program) -> dict:
    text = TACGenerator().generate_text(program)
    return {"status": "ok", "text": text, "lines": len(text.splitlines())}


@contextlib.contextmanager
def inside(path: Path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def run_codegen(program, workdir: Path, output_name: str, compiler: str | None):
    """Chama o CppCodeGenerator real. Com compiler=None o g++ não existe e só o .cpp é gravado."""
    env_before = os.environ.get("CXX")
    os.environ["CXX"] = compiler or str(workdir / "sem-compilador-de-proposito.exe")
    out, err = io.StringIO(), io.StringIO()
    start = time.perf_counter()
    try:
        with inside(workdir), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            ok = CppCodeGenerator().generate(program, output_name)
    finally:
        if env_before is None:
            os.environ.pop("CXX", None)
        else:
            os.environ["CXX"] = env_before
    duration = int((time.perf_counter() - start) * 1000)
    cpp_text = (workdir / "output" / f"{output_name}.cpp").read_text(encoding="utf-8")
    return ok, cpp_text, out.getvalue(), err.getvalue(), duration


# ---------------------------------------------------------------- envelope

def diag(phase, code, message, line, column, severity="error", detail=None):
    out = {"phase": phase, "severity": severity, "code": code, "message": message, "line": line, "column": column}
    if detail is not None:
        out["detail"] = detail
    return out


def skipped(reason):
    return {"status": "skipped", "reason": reason}


def envelope(source: str, operation: str, request_id: str, compiler: str | None = None) -> tuple[dict, Path | None]:
    phases, diagnostics = {}, []
    artifacts = {"cpp_id": None, "tac_id": None, "binary_id": None}
    binary = None

    lexer_payload, lexer_diags, tokens = run_lexer(source)
    phases["lexer"] = lexer_payload
    diagnostics += lexer_diags
    program = None
    if lexer_payload["status"] == "ok":
        phases["parser"], parser_diags, program = run_parser(tokens)
        diagnostics += parser_diags
    if program is not None:
        phases["semantic"], semantic_diags = run_semantic(program)
        diagnostics += semantic_diags
    if phases.get("semantic", {}).get("status") == "ok":
        phases["tac"] = run_tac(program)
        workdir = Path(tempfile.mkdtemp(prefix="minipar_fix_"))
        WORKDIRS.append(workdir)
        output_name = f"minipar_{request_id[:8]}"
        gpp_ok, cpp_text, gpp_out, gpp_err, gpp_ms = run_codegen(program, workdir, output_name,
                                                                compiler if operation == "compile" else None)
        phases["cpp"] = {"status": "ok", "text": cpp_text}
        if operation == "compile":
            command = [compiler, "-std=c++20", "-O3", os.path.join("output", f"{output_name}.cpp"),
                       "-o", os.path.join("output", f"{output_name}.exe"), "-pthread"]
            if sys.platform == "win32":
                command.append("-lws2_32")
            # O codegen atual imprime o comando e as mensagens do g++ misturadas; aqui só interessa o resultado.
            exe = workdir / "output" / f"{output_name}.exe"
            phases["gpp"] = {"status": "ok" if gpp_ok else "error", "command": command,
                             "returncode": 0 if gpp_ok else 1, "stdout": "", "stderr": "" if gpp_ok else gpp_err,
                             "duration_ms": gpp_ms}
            if gpp_ok and exe.is_file() and exe.stat().st_size > 0:
                artifacts = {"cpp_id": request_id, "tac_id": request_id, "binary_id": request_id}
                binary = exe
            else:
                diagnostics.append(diag("gpp", "GPP_FAILED", "Falha na compilacao C++", None, None))

    # Regra única das fases ignoradas (§1.3).
    failed = False
    ordered = {}
    for phase in PHASES:
        if phase not in REQUESTED[operation]:
            ordered[phase] = skipped("not_requested")
        elif failed or phase not in phases:
            ordered[phase] = skipped("previous_phase_failed")
        else:
            ordered[phase] = phases[phase]
            failed = phases[phase]["status"] == "error"

    ok = all(ordered[p]["status"] == "ok" for p in REQUESTED[operation])
    if operation == "compile":
        ok = ok and binary is not None
    return {
        "contract": "minipar.compile.v1",
        "operation": operation,
        "request_id": request_id,
        "ok": ok,
        "source_hash": "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "duration_ms": 0,
        "phases": ordered,
        "diagnostics": diagnostics,
        "artifacts": artifacts,
    }, binary


def execute(binary: Path, artifact_id: str, stdin: str = "", timeout_sec: int = 10) -> dict:
    start = time.perf_counter()
    result = subprocess.run([str(binary)], input=stdin.encode("utf-8"), capture_output=True, timeout=timeout_sec)
    stdout = result.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    stderr = result.stderr.decode("utf-8", errors="replace").replace("\r\n", "\n")
    return {"contract": "minipar.execute.v1", "artifact_id": artifact_id, "ok": result.returncode == 0,
            "exit_code": result.returncode, "timed_out": False,
            "duration_ms": int((time.perf_counter() - start) * 1000),
            "stdout": stdout, "stderr": stderr, "stdout_truncated": False, "stderr_truncated": False, "error": None}


# ---------------------------------------------------------------- fixtures

FIXTURES = (
    # arquivo, id, título, código, notas
    ("fix-01-sucesso", "FIX-01", "Sucesso: soma e impressão", "var x = 2 + 3;\nprint(x);\n", []),
    ("fix-02-erro-lexico", "FIX-02", "Erro léxico: caractere desconhecido", "var x = 2 @ 3;\n",
     ["Comportamento contratado (PEND-WEB-01): o lexer atual ainda não acusa LEX_UNKNOWN_CHAR."]),
    ("fix-03-erro-sintatico", "FIX-03", "Erro sintático: expressão faltando", "var x = 2 + ;\n", []),
    ("fix-04-erro-semantico", "FIX-04", "Erro semântico: variável não declarada", "print(y);\n", []),
)
LARGE_PROGRAM = ("prog-01-quicksort-classes", "PROG-01", "Programa maior: Quicksort com classes (Teste 6)",
                 "tests/teste6_quicksort_classes.minipar")
HUGE_PROGRAM = ("prog-02-grande-truncado", "PROG-02", "Programa grande: mais de 5000 nós (AST truncada)")
HUGE_DECLARATIONS = 1000  # 6 nós por declaração: passa de MAX_NODES e força o marcador max_nodes


def huge_program_source() -> str:
    """Programa determinístico para o teste de desempenho do WEB-02: uma função com laço e mil declarações."""
    lines = [
        "# PROG-02: gerado por web_didatica/tools/gerar_fixtures.py para testar a Web com mais de 5000 nos.",
        "func soma_quadrados(n) {",
        "    var total = 0;",
        "    var i = 1;",
        "    while (i <= n) {",
        "        total = total + i * i;",
        "        i = i + 1;",
        "    }",
        "    return total;",
        "}",
        "",
    ]
    lines += [f"var v{i} = {i} + {i} * 2;" for i in range(HUGE_DECLARATIONS)]
    lines += ["", "print(soma_quadrados(10));", f"print(v{HUGE_DECLARATIONS - 1});"]
    return "\n".join(lines) + "\n"


def write(name: str, data: dict, compact: bool = False) -> None:
    path = FIXTURES_DIR / f"{name}.json"
    # Fixtures grandes saem compactas para não pesar no repositório; as demais ficam legíveis.
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) if compact \
        else json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(f"gravado {path.relative_to(ROOT)}")


def main() -> int:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    common_notes = ["MOCK: gerado por web_didatica/tools/gerar_fixtures.py a partir das fases reais de src/; "
                    "não é resposta do serviço CORE-08."]
    index = []
    for i, (name, fid, title, source, notes) in enumerate(FIXTURES, start=1):
        response, _ = envelope(source, "analyze", f"{i:032x}")
        write(name, {"fixture": fid, "title": title, "mock": True, "source": source,
                     "notes": common_notes + notes, "analyze": response})
        index.append({"fixture": fid, "title": title, "file": f"{name}.json"})

    name, fid, title, path = LARGE_PROGRAM
    source = (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")
    response, _ = envelope(source, "analyze", f"{len(FIXTURES) + 1:032x}")
    write(name, {"fixture": fid, "title": title, "mock": True, "source": source,
                 "notes": common_notes + [f"Código de {path} com fim de linha normalizado para \\n, "
                                          "como o editor do navegador envia."], "analyze": response})
    index.append({"fixture": fid, "title": title, "file": f"{name}.json"})

    # request_id 7: os ids de 1 a 6 já pertencem às fixtures do WEB-01 e não mudam.
    name, fid, title = HUGE_PROGRAM
    source = huge_program_source()
    response, _ = envelope(source, "analyze", f"{len(FIXTURES) + 3:032x}")
    write(name, {"fixture": fid, "title": title, "mock": True, "source": source,
                 "notes": common_notes + [
                     f"Programa gerado com {HUGE_DECLARATIONS} declarações para passar de {MAX_NODES} nós "
                     "e exercitar o truncamento do §1.4 e o desempenho da Web (WEB-02).",
                     "JSON compacto (sem indentação) para reduzir o tamanho no repositório."],
                 "analyze": response}, compact=True)
    index.append({"fixture": fid, "title": title, "file": f"{name}.json"})

    compiler = os.environ.get("CXX") or "g++"
    source = FIXTURES[0][3]
    request_id = f"{len(FIXTURES) + 2:032x}"
    response, binary = envelope(source, "compile", request_id, compiler)
    if binary is None:
        print("[ERRO] g++ não gerou binário; fixture de execução não gravada.", file=sys.stderr)
        return 1
    run = execute(binary, request_id)
    write("exec-01-fix01", {"fixture": "EXEC-01", "title": "Compilar e executar o código de FIX-01", "mock": True,
                            "source": source, "stdin": "",
                            "notes": common_notes + [
                                "compile: o comando do g++ é o do CppCodeGenerator atual, gravando em output/ de um "
                                "diretório temporário; o serviço real usará um diretório por requisição.",
                                "execute: o binário foi realmente executado; duration_ms é a medida desta geração."],
                            "compile": response, "execute": run})
    index.append({"fixture": "EXEC-01", "title": "Compilar e executar o código de FIX-01", "file": "exec-01-fix01.json"})

    write("index", {"contract": "minipar.compile.v1", "mock": True, "fixtures": index})
    return 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        for workdir in WORKDIRS:
            shutil.rmtree(workdir, ignore_errors=True)
    sys.exit(code)
