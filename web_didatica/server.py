"""Servidor da Web didática (WEB-03 e WEB-04), contrato C-WEB-v1 §1.1 e §1.8.

Camada fina do Eixo B: valida a requisição, repassa o código a `src/service.py`
(Eixo A) e devolve o envelope como JSON, sem alterar nada. Não reimplementa
nenhuma fase e não lê stdout/stderr do compilador. Escuta só em 127.0.0.1.

Rotas: `POST /api/v1/analyze` (WEB-03); `POST /api/v1/compile`,
`POST /api/v1/execute` e `GET /api/v1/artifacts/<id>/<kind>` (WEB-04).

Uso, na raiz do repositório:
    .venv\\Scripts\\python.exe -B web_didatica/server.py
e abrir http://127.0.0.1:5001/
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import service  # noqa: E402  (precisa da raiz no sys.path)

HOST = "127.0.0.1"
PORTA = 5001
LIMITE_FONTE_BYTES = 200_000  # §1.8: código acima disso é HTTP 400
# O corpo JSON pode ser bem maior que o código (escapes \uXXXX ocupam 6 bytes por
# caractere). Acima deste teto o corpo nem é lido; a resposta continua sendo 400.
LIMITE_CORPO_BYTES = 8 * LIMITE_FONTE_BYTES
TIMEOUT_PADRAO, TIMEOUT_MIN, TIMEOUT_MAX = 10, 1, 30  # §1.6 e §1.8
# Programa do Teste 11 (MiniCompilador em MiniPar, Eixo B), oferecido como exemplo de
# compilar e executar. Só leitura; o .arm sai do stdout da execução (§1.7).
PROGRAMA_T11 = RAIZ / "tests" / "2026_2" / "test11" / "minicompilador.minipar"
ENTRADA_T11 = "((2+4)*7)-(5*4)\n"  # caso 1 de C-T11-v1 §3.1

_logger = logging.getLogger(__name__)


def _erro(status: int, codigo: str, mensagem: str):
    return jsonify({"error": {"code": codigo, "message": mensagem}}), status


def _utf8_valido(texto: str) -> bool:
    try:
        texto.encode("utf-8")
    except UnicodeEncodeError:  # substitutos isolados vindos de escapes do JSON
        return False
    return True


def _ler_corpo():
    """Devolve (objeto JSON, None) ou (None, resposta 400)."""
    if not request.is_json:
        return None, _erro(400, "BAD_REQUEST", "O corpo precisa ser JSON (Content-Type: application/json).")
    corpo = request.get_json(silent=True)
    if not isinstance(corpo, dict):
        return None, _erro(400, "BAD_REQUEST", "JSON inválido ou não é um objeto.")
    return corpo, None


def _ler_fonte():
    """Devolve (source, None) ou (None, resposta 400) conforme §1.8."""
    corpo, falha = _ler_corpo()
    if falha:
        return None, falha
    fonte = corpo.get("source")
    if not isinstance(fonte, str):
        return None, _erro(400, "BAD_REQUEST", "Campo 'source' ausente ou não é texto.")
    if not _utf8_valido(fonte):
        return None, _erro(400, "BAD_REQUEST", "Campo 'source' não é UTF-8 válido.")
    tamanho = len(fonte.encode("utf-8"))
    if tamanho > LIMITE_FONTE_BYTES:
        return None, _erro(400, "BAD_REQUEST",
                           f"Código com {tamanho} bytes; o limite é {LIMITE_FONTE_BYTES} bytes.")
    return fonte, None


def _ler_execucao():
    """Devolve ((artifact_id, stdin, timeout_sec), None) ou (None, resposta 400) conforme §1.8.

    O formato do artifact_id não é conferido aqui: o serviço responde INVALID_ARGUMENT
    ou ARTIFACT_NOT_FOUND dentro do envelope minipar.execute.v1 (§1.6).
    """
    corpo, falha = _ler_corpo()
    if falha:
        return None, falha
    artefato = corpo.get("artifact_id")
    if not isinstance(artefato, str):
        return None, _erro(400, "BAD_REQUEST", "Campo 'artifact_id' ausente ou não é texto.")
    entrada = corpo.get("stdin", "")
    if not isinstance(entrada, str):
        return None, _erro(400, "BAD_REQUEST", "Campo 'stdin' não é texto.")
    if not _utf8_valido(entrada):
        return None, _erro(400, "BAD_REQUEST", "Campo 'stdin' não é UTF-8 válido.")
    limite = corpo.get("timeout_sec", TIMEOUT_PADRAO)
    # bool é subclasse de int em Python: true/false não são tempo limite; 10.0 também não.
    if type(limite) is not int or not TIMEOUT_MIN <= limite <= TIMEOUT_MAX:
        return None, _erro(400, "BAD_REQUEST",
                           f"Campo 'timeout_sec' precisa ser inteiro de {TIMEOUT_MIN} a {TIMEOUT_MAX}.")
    return (artefato, entrada, limite), None


def criar_app() -> Flask:
    app = Flask(__name__, static_folder=str(AQUI / "static"), static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = LIMITE_CORPO_BYTES
    app.json.ensure_ascii = False
    app.json.sort_keys = False  # preserva a ordem das fases do envelope (§1.3)

    @app.get("/")
    def inicio():
        return redirect("/static/index.html")

    # Fixtures: código dos exemplos e o modo mock (?fonte=mock). Só arquivos .json da pasta.
    @app.get("/fixtures/<nome>")
    def fixtures(nome: str):
        if not nome.endswith(".json"):
            return _erro(404, "NOT_FOUND", "Fixture inexistente.")
        return send_from_directory(AQUI / "fixtures", nome, max_age=0)

    # Exemplo do Teste 11: o código do MiniCompilador e a entrada do caso 1 (C-T11-v1 §3.1).
    @app.get("/exemplos/t11.json")
    def exemplo_t11():
        try:
            fonte = PROGRAMA_T11.read_text(encoding="utf-8")
        except OSError:
            return _erro(404, "NOT_FOUND", "Programa do Teste 11 não encontrado.")
        return jsonify({"fixture": "T11", "title": "Teste 11: MiniCompilador em MiniPar (gera o .arm)",
                        "source": fonte, "stdin": ENTRADA_T11})

    @app.post("/api/v1/analyze")
    def analisar():
        fonte, falha = _ler_fonte()
        if falha:
            return falha
        # HTTP 200 inclusive com erro de compilação (ok: false), §1.8.
        return jsonify(service.analyze(fonte)), 200

    @app.post("/api/v1/compile")
    def compilar():
        fonte, falha = _ler_fonte()
        if falha:
            return falha
        # Inclui o g++; ok só com o binário desta requisição (§1.3). Erro do programa é HTTP 200.
        return jsonify(service.compile_program(fonte)), 200

    @app.post("/api/v1/execute")
    def executar():
        argumentos, falha = _ler_execucao()
        if falha:
            return falha
        artefato, entrada, limite = argumentos
        # Timeout, código de saída ≠ 0 e artefato inexistente vêm no envelope (§1.6), com HTTP 200.
        return jsonify(service.execute(artefato, stdin=entrada, timeout_sec=limite)), 200

    @app.get("/api/v1/artifacts/<artefato>/<tipo>")
    def baixar(artefato: str, tipo: str):
        achado = service.get_artifact(artefato, tipo)
        if not achado.get("ok"):
            erro = achado.get("error") or {}
            if erro.get("code") == "INVALID_ARGUMENT":
                return _erro(400, "BAD_REQUEST", erro.get("message") or "ID ou tipo de artefato inválido.")
            return _erro(404, erro.get("code") or "ARTIFACT_NOT_FOUND", erro.get("message") or "Artefato não encontrado.")
        # O caminho vem do registro do serviço para este id (§1.7), nunca de outra compilação.
        resposta = send_file(achado["path"], mimetype=achado["media_type"], as_attachment=True,
                             download_name=achado["filename"], max_age=0)
        resposta.headers["Cache-Control"] = "no-store"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        return resposta

    @app.errorhandler(RequestEntityTooLarge)
    def corpo_grande(_erro_http):
        return _erro(400, "BAD_REQUEST", f"Corpo da requisição acima de {LIMITE_CORPO_BYTES} bytes.")

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        if request.path.startswith("/api/"):
            codigo = "BAD_REQUEST" if erro.code == 400 else "NOT_FOUND" if erro.code == 404 else "HTTP_ERROR"
            return _erro(erro.code or 500, codigo, erro.description or erro.name)
        return erro

    @app.errorhandler(Exception)
    def erro_servidor(_excecao):
        # Só falha do próprio servidor chega aqui; o serviço já devolve INTERNAL_ERROR no envelope.
        _logger.exception("Falha no servidor da Web didática")
        return _erro(500, "INTERNAL_ERROR", "Falha no servidor da Web didática.")

    return app


app = criar_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Só 127.0.0.1 (§1.8). threaded: o serviço aceita chamadas simultâneas (§1.2, regra 4).
    app.run(host=HOST, port=PORTA, debug=False, threaded=True)
