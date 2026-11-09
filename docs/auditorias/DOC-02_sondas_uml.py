"""DOC-02 — sondas que confrontam os diagramas de classes UML com o código.

Lê os blocos ```mermaid classDiagram``` de docs/15_UML_MINIPAR_2026_2.md e confere:

  * classe: cada classe com ``%% @fonte Nome caminho [caminho ...]`` existe no(s) arquivo(s);
  * membro: cada atributo, método e valor de enumeração listado existe na classe/módulo;
  * heranca: cada ``Pai <|-- Filho`` existe no código (Python e JS);
  * aresta: as duas pontas de cada relação foram declaradas no bloco (o Mermaid cria
    classes fantasmas para nomes digitados errado);
  * cobertura: toda classe de nível de módulo em src/*.py, todo tipo de nível de namespace
    em runtime/include/minipar_rt/*.hpp, toda classe JS e todo arquivo de código das
    camadas modeladas aparecem em algum diagrama.

Python é conferido por AST; C++, JS e MiniPar por busca de declaração no arquivo.
Uso: python docs/auditorias/DOC-02_sondas_uml.py [--json SAIDA] [--doc DOC]
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "15_UML_MINIPAR_2026_2.md"
EXTERNAL = {"Exception", "ValueError", "Error"}  # tipos da linguagem/biblioteca padrão

# Arquivos que precisam ser citados por algum @fonte (cobertura de módulos).
COVERED_FILES = (
    sorted(p for p in (ROOT / "src").glob("*.py") if p.name != "__init__.py")
    + [ROOT / n for n in ("main.py", "menu.py", "app.py", "test_orchestrator.py", "program_analyzer.py")]
    + [ROOT / "web_didatica" / "server.py"]
    + sorted((ROOT / "web_didatica" / "static" / "js").glob("*.js"))
    + sorted(p for p in (ROOT / "runtime" / "include" / "minipar_rt").glob("*.hpp") if p.name != "minipar_rt.hpp")
    + [ROOT / "tests" / "2026_2" / "test11" / "minicompilador.minipar"]
)

REL = re.compile(r'^(\w+)(?:~\w+~)?(?:\s+"[^"]*")?\s+(<\|--|\*--|o--|-->|\.\.>|--|\.\.\|>)\s+(?:"[^"]*"\s+)?(\w+)')


# ---------------------------------------------------------------- leitura do documento
def parse_doc(text: str) -> list[dict]:
    blocks = re.findall(r"```mermaid\n(.*?)```", text, flags=re.S)
    diagrams = []
    for index, block in enumerate(blocks, 1):
        lines = block.splitlines()
        if not lines or lines[0].strip() != "classDiagram":
            continue
        d = dict(index=index, fonte={}, classes={}, stereo={}, relations=[])
        current = None
        for raw in lines[1:]:
            line = raw.strip()
            if not line:
                continue
            m = re.match(r"%%\s*@fonte\s+(\w+)\s+(.+)$", line)
            if m:
                d["fonte"][m[1]] = m[2].split()
                continue
            if line.startswith("%%") or line.startswith("direction"):
                continue
            if current is not None:
                if line == "}":
                    current = None
                else:
                    add_member(d, current, line)
                continue
            m = re.match(r"^class\s+(\w+)(?:~\w+~)?\s*(\{)?\s*(.*?)\s*(\})?$", line)
            if m:
                name = m[1]
                d["classes"].setdefault(name, [])
                if m[2] and m[4]:          # class X { +a: b }
                    if m[3]:
                        add_member(d, name, m[3])
                elif m[2]:
                    current = name
                continue
            m = REL.match(line)
            if m:
                d["relations"].append((m[1], m[2], m[3], line))
        diagrams.append(d)
    return diagrams


def add_member(d: dict, cls: str, line: str) -> None:
    if line.startswith("<<"):
        d["stereo"][cls] = line.strip("<>").strip()
        return
    body = line.lstrip("+-#~").strip()
    if "(" in body:
        name, kind = body.split("(", 1)[0].strip(), "method"
    else:
        name, kind = re.split(r"[:\s]", body, maxsplit=1)[0], "attribute"
    if d["stereo"].get(cls) == "enumeration":
        kind = "enum"
    d["classes"][cls].append((kind, name))


# ---------------------------------------------------------------- consulta ao código
_py_cache: dict[Path, ast.Module] = {}


def py_tree(path: Path) -> ast.Module:
    if path not in _py_cache:
        _py_cache[path] = ast.parse(path.read_text(encoding="utf-8"))
    return _py_cache[path]


def targets(node) -> list[str]:
    out = []
    items = node.targets if isinstance(node, ast.Assign) else [node.target]
    for t in items:
        for e in (t.elts if isinstance(t, ast.Tuple) else [t]):
            if isinstance(e, ast.Name):
                out.append(e.id)
    return out


def py_class(path: Path, name: str):
    return next((n for n in py_tree(path).body if isinstance(n, ast.ClassDef) and n.name == name), None)


def py_class_members(cls: ast.ClassDef) -> set[str]:
    names = set()
    for n in cls.body:
        if isinstance(n, ast.FunctionDef):
            names.add(n.name)
            for sub in ast.walk(n):
                if isinstance(sub, (ast.Assign, ast.AnnAssign)):
                    items = sub.targets if isinstance(sub, ast.Assign) else [sub.target]
                    for t in items:
                        for e in (t.elts if isinstance(t, ast.Tuple) else [t]):
                            if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name) and e.value.id == "self":
                                names.add(e.attr)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            names.update(targets(n))
    return names


def py_module_members(path: Path) -> set[str]:
    names = set()
    for n in py_tree(path).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            names.update(targets(n))
    return names


def text_of(paths: list[Path]) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)


def class_exists(name: str, paths: list[Path], module: bool) -> bool:
    if not all(p.is_file() for p in paths):
        return False
    if module:
        return True
    ext = paths[0].suffix
    if ext == ".py":
        return any(py_class(p, name) for p in paths)
    src = text_of(paths)
    if ext == ".hpp":
        return re.search(rf"^\s*(?:class|struct|enum class)\s+{name}\b(?!\s*;)", src, re.M) is not None
    if ext in (".js", ".minipar"):
        return re.search(rf"\bclass\s+{name}\b", src) is not None
    return False


def member_exists(cls: str, kind: str, member: str, paths: list[Path], module: bool) -> bool:
    ext = paths[0].suffix
    if ext == ".py":
        for p in paths:
            found = py_module_members(p) if module else py_class_members(py_class(p, cls) or ast.ClassDef(body=[]))
            if member in found:
                return True
        return False
    src = text_of(paths)
    m = re.escape(member)
    if ext == ".hpp":
        pattern = rf"\b{m}\s*\(" if kind == "method" else rf"\b{m}\b"
        return re.search(pattern, src) is not None
    if ext == ".js":
        return re.search(rf"(?:\bfunction\s+|\b(?:const|let|var|class)\s+){m}\b", src) is not None
    if ext == ".minipar":
        pattern = rf"\bfunc\s+{m}\s*\(" if kind == "method" else rf"\bvar\s+{m}\b"
        return re.search(pattern, src) is not None
    return False


def inherits(parent: str, child: str, paths: list[Path]) -> bool:
    ext = paths[0].suffix
    if ext == ".py":
        node = next((py_class(p, child) for p in paths if py_class(p, child)), None)
        return node is not None and parent in [ast.unparse(b) for b in node.bases]
    src = text_of(paths)
    if ext == ".js":
        return re.search(rf"\bclass\s+{child}\s+extends\s+{parent}\b", src) is not None
    if ext == ".hpp":
        return re.search(rf"\b(?:class|struct)\s+{child}\s*:\s*(?:public\s+)?(?:\w+::)*{parent}\b", src) is not None
    return False


# ---------------------------------------------------------------- execução das sondas
def run(text: str) -> list[dict]:
    results = []

    def record(group, case, ok, detail=""):
        results.append(dict(group=group, case=case, status="PASS" if ok else "FAIL", detail=detail))

    diagrams = parse_doc(text)
    record("documento", "blocos classDiagram", len(diagrams) >= 10, f"{len(diagrams)} blocos")
    cited_files: set[Path] = set()
    modeled: dict[Path, set[str]] = {}

    for d in diagrams:
        tag = f"bloco {d['index']}"
        for cls, members in d["classes"].items():
            if cls in EXTERNAL:
                continue
            files = d["fonte"].get(cls)
            if not files:
                record("classe", f"{tag}: {cls}", False, "sem %% @fonte")
                continue
            paths = [ROOT / f for f in files]
            cited_files.update(p.resolve() for p in paths)
            module = "module" in d["stereo"].get(cls, "")
            ok = class_exists(cls, paths, module)
            record("classe", f"{tag}: {cls}", ok, " ".join(files))
            if not ok:
                continue
            if not module:
                for p in paths:
                    modeled.setdefault(p.resolve(), set()).add(cls)
            for kind, member in members:
                if kind == "method" and member == cls and paths[0].suffix == ".py" and not module:
                    member = "__init__"  # construtor na notação UML: +Classe(...)
                record("membro", f"{tag}: {cls}.{member}", member_exists(cls, kind, member, paths, module), kind)
        for left, arrow, right, line in d["relations"]:
            declared = left in d["classes"] and right in d["classes"]
            record("aresta", f"{tag}: {line}", declared, "pontas declaradas" if declared else "classe não declarada")
            if arrow == "<|--" and right not in EXTERNAL:
                files = d["fonte"].get(right)
                ok = bool(files) and inherits(left, right, [ROOT / f for f in files])
                record("heranca", f"{tag}: {left} <|-- {right}", ok)

    for path in COVERED_FILES:
        rel = path.relative_to(ROOT).as_posix()
        record("cobertura-arquivo", rel, path.resolve() in cited_files)
    for path in sorted((ROOT / "src").glob("*.py")):
        for n in py_tree(path).body:
            if isinstance(n, ast.ClassDef):
                rel = path.relative_to(ROOT).as_posix()
                record("cobertura-classe", f"{rel}: {n.name}", n.name in modeled.get(path.resolve(), set()))
    for path in sorted((ROOT / "runtime" / "include" / "minipar_rt").glob("*.hpp")):
        src = path.read_text(encoding="utf-8")
        names = sorted(set(re.findall(r"^(?:class|struct|enum class)\s+(\w+)\b(?!\s*;)", src, re.M)))
        for name in names:
            rel = path.relative_to(ROOT).as_posix()
            record("cobertura-classe", f"{rel}: {name}", name in modeled.get(path.resolve(), set()))
    for path in sorted((ROOT / "web_didatica" / "static" / "js").glob("*.js")):
        for name in re.findall(r"^\s*(?:export\s+)?class\s+(\w+)", path.read_text(encoding="utf-8"), re.M):
            rel = path.relative_to(ROOT).as_posix()
            record("cobertura-classe", f"{rel}: {name}", name in modeled.get(path.resolve(), set()))
    return results


def main(argv: list[str], text: str | None = None) -> int:
    out = None
    doc = DOC
    args = list(argv[1:])
    while args:
        flag = args.pop(0)
        if flag == "--json" and args:
            out = Path(args.pop(0))
        elif flag == "--doc" and args:
            doc = Path(args.pop(0))
    if text is None:
        text = doc.read_text(encoding="utf-8")
    results = run(text)
    failed = [r for r in results if r["status"] != "PASS"]
    for r in failed:
        print(f"FAIL [{r['group']}] {r['case']} {r['detail']}".rstrip())
    groups: dict[str, list[int]] = {}
    for r in results:
        g = groups.setdefault(r["group"], [0, 0])
        g[0] += r["status"] == "PASS"
        g[1] += 1
    for name, (ok, total) in groups.items():
        print(f"  {name:<18} {ok}/{total}")
    passed = len(results) - len(failed)
    print(f"DOC-02 sondas: {passed}/{len(results)} PASS")
    if out:
        out.write_text(json.dumps(dict(card="DOC-02", passed=passed, total=len(results), results=results),
                                  ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
