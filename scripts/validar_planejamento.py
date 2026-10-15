#!/usr/bin/env python3
"""Valida coerência e dependências do backlog inicial. Somente stdlib."""
from pathlib import Path
from collections import defaultdict
from datetime import date
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "planning/cards.json").read_text(encoding="utf-8"))
items = data["items"]
ids = {c["id"] for c in items}
errors = []
if len(ids) != len(items):
    errors.append("IDs duplicados")
by_id = {c["id"]: c for c in items}
for c in items:
    required = ["id","axis","title","due","depends_on","acceptance","allowed_paths","priority","status","ready"]
    for f in required:
        if f not in c:
            errors.append(f"{c.get('id')} sem {f}")
    try:
        dt = date.fromisoformat(c["due"])
        if dt > date(2026,11,11):
            errors.append(f"{c['id']} após prazo oficial")
    except Exception:
        errors.append(f"{c['id']} prazo inválido")
    for dep in c["depends_on"]:
        if dep not in ids:
            errors.append(f"{c['id']} depende de {dep} inexistente")
        elif dep == c["id"]:
            errors.append(f"{c['id']} depende de si")
        else:
            try:
                if date.fromisoformat(by_id[dep]["due"]) > date.fromisoformat(c["due"]):
                    errors.append(f"{c['id']} vence antes da dependência {dep}")
            except Exception:
                pass
state = {}
def visit(k, stack):
    if state.get(k) == "done":
        return
    if state.get(k) == "visiting":
        errors.append("Ciclo: " + " -> ".join(stack+[k]))
        return
    state[k] = "visiting"
    for d in by_id[k]["depends_on"]:
        if d in by_id:
            visit(d, stack+[k])
    state[k] = "done"
for k in ids:
    visit(k, [])
counts = defaultdict(int)
for c in items:
    counts[c["axis"]] += 1
print(f"Cards: {len(items)}. Por eixo: {dict(sorted(counts.items()))}")
if errors:
    print("ERROS:", *errors, sep="\n - ")
    sys.exit(1)
print("OK: IDs únicos, datas válidas, dependências existentes e DAG sem ciclos.")
