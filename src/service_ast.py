"""Contract C-WEB-v1 AST presentation, independent from compiler traversal."""
from dataclasses import fields
from typing import get_args, get_type_hints
from functools import lru_cache

_hints = lru_cache(maxsize=None)(get_type_hints)
import json
if __package__:
    from .ast_nodes import ASTNode
else:
    from ast_nodes import ASTNode

MAX_NODES, MAX_DEPTH = 5000, 200


def _node_type(annotation):
    return (isinstance(annotation, type) and issubclass(annotation, ASTNode)) or any(
        _node_type(arg) for arg in get_args(annotation))


def _parts(node):
    children, attrs = [], {}
    hints = _hints(type(node))
    for field in fields(node):
        if field.name == "line": continue
        value = getattr(node, field.name)
        if _node_type(hints[field.name]):
            if isinstance(value, list): children.extend((field.name, i, n) for i, n in enumerate(value) if n is not None)
            elif value is not None: children.append((field.name, None, value))
        else: attrs[field.name] = value.copy() if isinstance(value, list) else value
    return children, attrs


def serialize_ast(program):
    sizes, depth, pending = {}, 0, [(program, 1, False)]
    parts = {}
    while pending:
        node, level, visited = pending.pop()
        if visited:
            sizes[id(node)] = 1 + sum(sizes[id(n)] for _, _, n in parts[id(node)][0])
            continue
        depth = max(depth, level)
        parts[id(node)] = _parts(node)
        pending.append((node, level, True))
        pending.extend((n, level+1, False) for _, _, n in reversed(parts[id(node)][0]))
    emitted, markers = 0, 0
    def make(node, role, index):
        nonlocal emitted
        children, attrs = parts[id(node)]
        kind = type(node).__name__
        label = kind
        for key in ("op", "name", "value", "class_name", "method_name", "property_name"):
            value = attrs.get(key)
            if value is None: continue
            text = (str(value).lower() if isinstance(value, bool) else
                json.dumps(value, ensure_ascii=False) if kind == "StringExpr" and key == "value" else str(value))
            label += "(" + (text[:39] + "…" if len(text)>40 else text) + ")"
            break
        out = dict(id=f"n{emitted}", kind=kind, label=label, role=role, index=index,
            line=node.line, attributes=attrs, children=[])
        emitted += 1
        return out, children
    def marker(reason, omitted):
        nonlocal markers
        role, index, node = omitted[0]
        count = sum(sizes[id(n)] for _, _, n in omitted)
        out = dict(id=f"x{markers}", kind="Truncated", label=f"Truncated({count} nós)",
            role=role, index=index, line=node.line, attributes=dict(reason=reason, omitted_nodes=count), children=[])
        markers += 1
        return out
    root, children = make(program, None, None)
    stack = [[root, children, 0, 1]]
    while stack:
        out, children, i, level = stack[-1]
        if i == len(children): stack.pop(); continue
        child = children[i]
        stack[-1][2] += 1
        if level >= MAX_DEPTH:
            out["children"].append(marker("max_depth", [child])); continue
        if emitted >= MAX_NODES:
            out["children"].append(marker("max_nodes", children[i:])); stack.pop(); continue
        child_out, grandchildren = make(child[2], child[0], child[1])
        out["children"].append(child_out)
        stack.append([child_out, grandchildren, 0, level+1])
    return root, dict(nodes=sizes[id(program)], emitted=emitted, depth=depth,
        truncated=emitted < sizes[id(program)], max_nodes=MAX_NODES, max_depth=MAX_DEPTH)
