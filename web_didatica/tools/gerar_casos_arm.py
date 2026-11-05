"""Gera static/testes/arm_casos.json: as seis saídas de teste do recorte do .arm (WEB-04).

C-WEB-v1 §1.10 pede que a extração do .arm na Web seja testada com seis saídas: bloco válido com
fim de linha `\\n`, o mesmo com `\\r\\n`, título ausente, título repetido, bloco que não começa com
`.global _start` e bloco sem linha vazia de fechamento. As seis partem do stdout real do caso 1
(`tests/2026_2/test11/arm/caso1.stdout.txt`, gerado pelo MiniCompilador no T11-03). O resultado
esperado de cada uma vem do próprio script `tests/2026_2/test11/extrair_arm.py`: texto do .arm ou
a mensagem de erro. A página `static/testes/arm.html` roda `static/js/arm.js` sobre os mesmos
casos e compara byte a byte.

Uso, na raiz do repositório:
    .venv\\Scripts\\python.exe -B web_didatica/tools/gerar_casos_arm.py           (grava)
    .venv\\Scripts\\python.exe -B web_didatica/tools/gerar_casos_arm.py --conferir (só confere)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
RAIZ = WEB.parent
T11 = RAIZ / "tests" / "2026_2" / "test11"
sys.path.insert(0, str(T11))

from extrair_arm import TITLE_SUFFIX, ExtractionError, extract_arm  # noqa: E402

STDOUT_CASO1 = T11 / "arm" / "caso1.stdout.txt"
SAIDA = WEB / "static" / "testes" / "arm_casos.json"


def _linha_titulo(linhas: list[str]) -> int:
    return next(i for i, linha in enumerate(linhas) if linha.endswith(TITLE_SUFFIX))


def entradas(stdout: str) -> list[tuple[str, str, str]]:
    """(id, descrição, stdout) das seis saídas, derivadas do stdout real com \\n."""
    linhas = stdout.split("\n")
    t = _linha_titulo(linhas)
    fim_bloco = linhas.index("", t + 1)  # primeira linha vazia depois do título
    sem_titulo = linhas[:t] + linhas[t + 1:]
    repetido = linhas[:fim_bloco + 1] + [linhas[t]] + linhas[t + 1:fim_bloco + 1] + linhas[fim_bloco + 1:]
    sem_global = linhas[:t + 1] + [".globl _start"] + linhas[t + 2:]
    sem_vazia = linhas[:fim_bloco]  # termina na última instrução, sem a linha vazia
    return [
        ("valido_lf", "bloco válido, fim de linha \\n (stdout real do caso 1)", stdout),
        ("valido_crlf", "o mesmo bloco com \\r\\n, como o stdout no Windows", stdout.replace("\n", "\r\n")),
        ("titulo_ausente", "linha de título removida", "\n".join(sem_titulo)),
        ("titulo_repetido", "título e bloco aparecem duas vezes", "\n".join(repetido)),
        ("sem_global_start", "primeira linha do bloco é .globl, não .global _start", "\n".join(sem_global)),
        ("sem_linha_vazia", "saída termina na última instrução, sem a linha vazia que fecha o bloco", "\n".join(sem_vazia)),
    ]


def gerar() -> dict:
    stdout = STDOUT_CASO1.read_bytes().decode("utf-8")
    casos = []
    for ident, descricao, texto in entradas(stdout):
        try:
            esperado = {"arm": extract_arm(texto)}
        except ExtractionError as erro:
            esperado = {"erro": str(erro)}
        casos.append({"id": ident, "descricao": descricao, "stdout": texto, "esperado": esperado})
    return {
        "origem": "tests/2026_2/test11/arm/caso1.stdout.txt; esperado calculado por tests/2026_2/test11/extrair_arm.py",
        "gerador": "web_didatica/tools/gerar_casos_arm.py",
        "casos": casos,
    }


def serializar(dados: dict) -> bytes:
    return (json.dumps(dados, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--conferir", action="store_true", help="só confere se o arquivo gravado está atualizado")
    args = parser.parse_args()
    dados = gerar()
    conteudo = serializar(dados)
    if args.conferir:
        # Compara o JSON lido, não os bytes: o Git pode trocar o fim de linha do arquivo
        # (core.autocrlf), mas os \r\n dos casos estão escapados dentro das strings.
        if not SAIDA.is_file() or json.loads(SAIDA.read_bytes().decode("utf-8")) != dados:
            print(f"FAIL: {SAIDA} desatualizado; rode sem --conferir.")
            return 1
        print(f"OK: {SAIDA} confere com extrair_arm.py.")
        return 0
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_bytes(conteudo)
    print(f"Gravado {SAIDA}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
