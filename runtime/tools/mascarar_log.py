"""Mascara logs do runtime antes de anexá-los como evidência (card RUN-06, Eixo C).

- IPv4 que não é loopback: o 3º octeto vira `x` (192.168.0.31 -> 192.168.x.31). Basta para
  mostrar que A e B têm IPs diferentes sem publicar a rede.
- Hostnames: cada `--host NOME=APELIDO` troca NOME por APELIDO (ex.: `--host DESKTOP-7Q2=pc-B`),
  inclusive dentro de `worker_id` (`host:pid`).
- Caminhos com a pasta do usuário (`C:\\Users\\<nome>`, `/home/<nome>`) viram `<home>`.

Uso:
    python runtime/tools/mascarar_log.py ENTRADA SAIDA [--host NOME=APELIDO ...]
    python runtime/tools/mascarar_log.py worker_B.log docs/evidencias/RUN-06/worker_B.log --host DESKTOP-7Q2=pc-B

Não sobrescreve a entrada. Termina com exit 1 se ainda sobrar um IPv4 sem máscara na saída.
Somente biblioteca padrão.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

IPV4 = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?![\d.])")
HOME = re.compile(r"(?i)([A-Z]:\\Users\\|/home/|/Users/)[^\\/\s\"']+")


def mascarar_ip(m: re.Match) -> str:
    a, b, c, d = m.groups()
    if a == "127" or not all(0 <= int(o) <= 255 for o in (a, b, c, d)):
        return m.group(0)
    return f"{a}.{b}.x.{d}"


def mascarar(texto: str, hosts: dict[str, str]) -> str:
    for nome, apelido in sorted(hosts.items(), key=lambda kv: -len(kv[0])):
        texto = re.sub(rf"\b{re.escape(nome)}\b", apelido, texto, flags=re.IGNORECASE)
    texto = HOME.sub(lambda m: m.group(1) + "<home>", texto)
    return IPV4.sub(mascarar_ip, texto)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path)
    ap.add_argument("saida", type=Path)
    ap.add_argument("--host", action="append", default=[], metavar="NOME=APELIDO",
                    help="troca um hostname por um apelido; pode repetir")
    args = ap.parse_args()
    hosts = {}
    for item in args.host:
        nome, sep, apelido = item.partition("=")
        if not sep or not nome or not apelido:
            ap.error(f"--host espera NOME=APELIDO, recebeu {item!r}")
        hosts[nome] = apelido
    if args.entrada.resolve() == args.saida.resolve():
        ap.error("a saída precisa ser outro arquivo")
    saida = mascarar(args.entrada.read_text(encoding="utf-8", errors="replace"), hosts)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(saida, encoding="utf-8")
    # Depois da máscara, só sobra IPv4 completo se for loopback ou se a máscara falhou.
    sobras = sorted({m.group(0) for m in IPV4.finditer(saida) if m.group(1) != "127"})
    print(f"{args.saida}: {len(saida.splitlines())} linhas; hosts trocados: {list(hosts.values()) or 'nenhum'}")
    if sobras:
        print(f"ATENCAO: IPv4 sem mascara: {sobras[:5]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
