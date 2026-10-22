"""Confere as fixtures de web_didatica/fixtures/ contra o contrato C-WEB-v1.

Uso, na raiz do repositório:
    py -B web_didatica/tools/validar_fixtures.py

Oráculos:
  - FIX-01 a FIX-04: o envelope `analyze` é igual ao bloco JSON do §1.9 de
    docs/02_CONTRATOS_TECNICOS.md, ignorando só o texto de `cpp` (abreviado no contrato).
    O contrato já usa request_id fixo e duration_ms 0, então esses campos também são comparados.
  - Todas: `source_hash` é o SHA-256 do `source` gravado; seis fases na ordem; regra das
    fases ignoradas; listas nunca nulas; ids de AST únicos e em pré-ordem.
  - EXEC-01: `compile` com ok true e ids iguais ao request_id; `execute` com stdout "5\n" (ACE-02).
Sai com código 1 se qualquer verificação falhar.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "web_didatica" / "fixtures"
CONTRACT = ROOT / "docs" / "02_CONTRATOS_TECNICOS.md"
PHASES = ["lexer", "parser", "semantic", "tac", "cpp", "gpp"]
REQUESTED = {"analyze": PHASES[:5], "compile": PHASES}

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def contract_fixtures() -> dict[str, dict]:
    text = CONTRACT.read_text(encoding="utf-8")
    found = {}
    for m in re.finditer(r"^#### (FIX-\d\d) — .*?^```json\n(.*?)^```", text, re.S | re.M):
        found[m.group(1)] = json.loads(m.group(2))
    return found


def diff(expected, actual, path="$") -> list[str]:
    if type(expected) is not type(actual):
        return [f"{path}: esperado {expected!r}, obtido {actual!r}"]
    if isinstance(expected, dict):
        out = []
        if list(expected) != list(actual):
            out.append(f"{path}: chaves {list(expected)} != {list(actual)}")
        for key in expected:
            if key in actual:
                out += diff(expected[key], actual[key], f"{path}.{key}")
        return out
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return [f"{path}: {len(expected)} itens esperados, {len(actual)} obtidos"]
        return [d for i, (e, a) in enumerate(zip(expected, actual)) for d in diff(e, a, f"{path}[{i}]")]
    return [] if expected == actual else [f"{path}: esperado {expected!r}, obtido {actual!r}"]


def check_envelope(name: str, source: str, env: dict) -> None:
    op = env["operation"]
    check(env["contract"] == "minipar.compile.v1", f"{name}: contract")
    check(re.fullmatch(r"[0-9a-f]{32}", env["request_id"]) is not None, f"{name}: request_id fora do formato")
    expected_hash = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    check(env["source_hash"] == expected_hash, f"{name}: source_hash não bate com source")
    check(list(env["phases"]) == PHASES, f"{name}: fases fora da ordem {list(env['phases'])}")
    failed = False
    for phase in PHASES:
        data = env["phases"][phase]
        if phase not in REQUESTED[op]:
            check(data == {"status": "skipped", "reason": "not_requested"}, f"{name}: {phase} deveria ser not_requested")
        elif failed:
            check(data == {"status": "skipped", "reason": "previous_phase_failed"},
                  f"{name}: {phase} deveria ser previous_phase_failed")
        else:
            check(data["status"] in ("ok", "error"), f"{name}: {phase} solicitada com status {data['status']}")
            check("reason" not in data, f"{name}: {phase} executada com reason")
            failed = data["status"] == "error"
    check(isinstance(env["diagnostics"], list), f"{name}: diagnostics não é lista")
    ast = env["phases"]["parser"].get("ast")
    if ast:
        ids, stack = [], [ast]
        while stack:
            node = stack.pop()
            ids.append(node["id"])
            check(isinstance(node["children"], list) and isinstance(node["attributes"], dict), f"{name}: nó {node['id']}")
            stack.extend(reversed(node["children"]))
        real = [i for i in ids if i.startswith("n")]
        check(real == [f"n{k}" for k in range(len(real))], f"{name}: ids da AST fora da pré-ordem")
        check(len(set(ids)) == len(ids), f"{name}: ids da AST repetidos")
        stats = env["phases"]["parser"]["ast_stats"]
        check(stats["emitted"] == len(real), f"{name}: ast_stats.emitted != nós emitidos")


def main() -> int:
    expected = contract_fixtures()
    check(sorted(expected) == ["FIX-01", "FIX-02", "FIX-03", "FIX-04"], f"contrato: fixtures encontradas {sorted(expected)}")
    index = json.loads((FIXTURES_DIR / "index.json").read_text(encoding="utf-8"))
    for entry in index["fixtures"]:
        data = json.loads((FIXTURES_DIR / entry["file"]).read_text(encoding="utf-8"))
        name = data["fixture"]
        check(data["mock"] is True, f"{name}: mock deveria ser true")
        for op in ("analyze", "compile"):
            if op in data:
                check_envelope(f"{name}/{op}", data["source"], data[op])
        if name in expected:
            actual = json.loads(json.dumps(data["analyze"]))
            reference = json.loads(json.dumps(expected[name]))
            if reference["phases"]["cpp"].get("text", "").startswith("<ABREVIADO"):
                check(actual["phases"]["cpp"]["status"] == "ok" and len(actual["phases"]["cpp"]["text"]) > 0,
                      f"{name}: cpp sem texto completo")
                actual["phases"]["cpp"]["text"] = reference["phases"]["cpp"]["text"]
            for d in diff(reference, actual):
                failures.append(f"{name}: {d}")
        if name == "EXEC-01":
            comp, run = data["compile"], data["execute"]
            rid = comp["request_id"]
            check(comp["ok"] is True, "EXEC-01: compile ok")
            check(comp["artifacts"] == {"cpp_id": rid, "tac_id": rid, "binary_id": rid}, "EXEC-01: artifacts")
            check(run["artifact_id"] == rid, "EXEC-01: artifact_id")
            check(run["ok"] is True and run["exit_code"] == 0 and run["stdout"] == "5\n",
                  f"EXEC-01: execução esperada stdout '5\\n', obtido {run['stdout']!r}")
        print(f"{name}: conferida")
    if failures:
        print("\nFAIL", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"\nPASS: {len(index['fixtures'])} fixtures conferidas; FIX-01 a FIX-04 iguais ao contrato (exceto texto C++).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
