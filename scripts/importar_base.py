#!/usr/bin/env python3
"""Importa com segurança a base MiniPar 2026.1 para snapshot + raiz ativa.

Uso:
  python scripts/importar_base.py --source ../minipar-base-2026-1        # dry-run
  python scripts/importar_base.py --source ../minipar-base-2026-1 --apply

Nunca copia .git, ambientes virtuais, caches, artefatos nem credenciais usuais.
A importação preserva a documentação do novo repositório, README e .gitignore.
Em caso de conflito, aborta antes de modificar qualquer arquivo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "legacy" / "minipar-2026.1"
IGNORE_DIRS = {
    ".git", ".github", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", "node_modules", "output", "outputs",
    "build", "dist", ".idea", ".vscode", ".cache", "temp_code", "site-packages",
}
IGNORE_FILES = {".DS_Store", "Thumbs.db", ".env", ".env.local", ".env.production"}
IGNORE_SUFFIXES = {".pyc", ".pyo", ".exe", ".dll", ".so", ".o", ".obj", ".class", ".log"}
ROOT_RESERVED = {"README.md", ".gitignore", "AGENTS.md", "planning", "docs", ".github", "legacy", "runtime", "web_didatica", "scripts"}


def sha256(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            dig.update(chunk)
    return dig.hexdigest()


def git_head(directory: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(directory), "rev-parse", "HEAD"],
                           check=True, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def main() -> None:
    p = argparse.ArgumentParser(description="Importação segura do MiniPar 2026.1")
    p.add_argument("--source", required=True, help="Diretório extraído/clonado da versão anterior")
    p.add_argument("--apply", action="store_true", help="Efetivamente copiar (sem esta flag é só dry-run)")
    args = p.parse_args()
    src = Path(args.source).expanduser().resolve(strict=True)
    if not src.is_dir():
        p.error("--source precisa apontar para um diretório")
    if src == ROOT or ROOT in src.parents or src in ROOT.parents:
        p.error("A fonte não pode ser igual, filha ou ancestral da pasta do novo projeto")
    if not (src / "src" / "lexer.py").is_file() or not (src / "main.py").is_file():
        p.error("Pasta fonte não parece MiniPar 2026.1: esperado src/lexer.py e main.py")
    if not LEGACY.is_dir():
        p.error("Snapshot legacy/minipar-2026.1 não encontrado")

    source_files: list[tuple[Path, Path]] = []
    for file in sorted(src.rglob("*")):
        if file.is_symlink():
            raise SystemExit(f"ERRO: link simbólico na fonte (revisar manualmente): {file}")
        if not file.is_file():
            continue
        rel = file.relative_to(src)
        if any(x in IGNORE_DIRS for x in rel.parts[:-1]):
            continue
        if file.name in IGNORE_FILES or file.suffix.lower() in IGNORE_SUFFIXES:
            continue
        source_files.append((file, rel))

    if not source_files:
        raise SystemExit("ERRO: nenhuma fonte elegível para importar")
    conflicts: list[str] = []
    targets: list[tuple[Path, Path]] = []
    archived_only: list[Path] = []
    for file, rel in source_files:
        archived = LEGACY / rel
        if archived.exists():
            conflicts.append(str(archived))
        targets.append((file, archived))
        # Documentação e arquivos reservados na raiz pertencem à nova estrutura.
        if rel.parts[0] in ROOT_RESERVED:
            archived_only.append(rel)
            continue
        active = ROOT / rel
        if active.exists():
            conflicts.append(str(active))
        targets.append((file, active))

    manifest_path = LEGACY / "ORIGEM_SNAPSHOT.json"
    if manifest_path.exists():
        conflicts.append(str(manifest_path))
    if conflicts:
        print("ABORTADO: destinos já existentes, não sobrescrever:")
        for x in conflicts[:30]:
            print("  -", x)
        if len(conflicts) > 30:
            print(f"  ... e mais {len(conflicts)-30} conflitos")
        raise SystemExit(2)

    print(f"Fonte:      {src}")
    print(f"Novo repo:  {ROOT}")
    print(f"Arquivos fonte elegíveis: {len(source_files)}")
    print(f"Cópias previstas (snapshot + raiz): {len(targets)}")
    print("Mantidos SOMENTE no snapshot (por segurança):", ", ".join(map(str, archived_only)) or "nenhum")
    print("Estado:", "APLICANDO" if args.apply else "DRY-RUN (nenhum arquivo será copiado)")
    if not args.apply:
        print("Confirme os caminhos e execute novamente com --apply.")
        return

    for file, dest in targets:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, dest)

    commit = git_head(src)
    manifest = {
        "origem": "https://github.com/luizwhirl/minipar-improvement",
        "commit": commit,
        "snapshot_em_utc": datetime.now(timezone.utc).isoformat(),
        "arquivos": {str(rel).replace('\\', '/'): sha256(file) for file, rel in source_files},
        "arquivos_apenas_snapshot": [str(x).replace('\\', '/') for x in archived_only],
        "nota": "Snapshot imutável. Desenvolvimento ocorre na raiz ativa; sem cópia da pasta .git original.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: importados {len(source_files)} arquivos da base; snapshot e cópia ativa criados.")
    print("Próximo passo: conferir git status; testar baseline com toolchain compatível.")


if __name__ == "__main__":
    main()
