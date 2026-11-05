"""Servidor da Web didática (WEB-03), contrato C-WEB-v1 §1.1 e §1.8.

Camada fina do Eixo B: valida a requisição, repassa o código a `src/service.py`
(Eixo A) e devolve o envelope como JSON, sem alterar nada. Não reimplementa
nenhuma fase e não lê stdout/stderr do compilador. Escuta só em 127.0.0.1.

Rotas deste card: `POST /api/v1/analyze`. As rotas `compile`, `execute` e
`artifacts` do §1.8 entram no WEB-04.

Uso, na raiz do repositório:
    .venv\\Scripts\\python.exe -B web_didatica/server.py
e abrir http://127.0.0.1:5001/
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory
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

_logger = logging.getLogger(__name__)


def _erro(status: int, codigo: str, mensagem: str):
    return jsonify({"error": {"code": codigo, "message": mensagem}}), status


def _ler_fonte():
    """Devolve (source, None) ou (None, resposta 400) conforme §1.8."""
    if not request.is_json:
        return None, _erro(400, "BAD_REQUEST", "O corpo precisa ser JSON (Content-Type: application/json).")
    corpo = request.get_json(silent=True)
    if not isinstance(corpo, dict):
        return None, _erro(400, "BAD_REQUEST", "JSON inválido ou não é um objeto.")
    fonte = corpo.get("source")
    if not isinstance(fonte, str):
        return None, _erro(400, "BAD_REQUEST", "Campo 'source' ausente ou não é texto.")
    try:
        tamanho = len(fonte.encode("utf-8"))
    except UnicodeEncodeError:
        return None, _erro(400, "BAD_REQUEST", "Campo 'source' não é UTF-8 válido.")
    if tamanho > LIMITE_FONTE_BYTES:
        return None, _erro(400, "BAD_REQUEST",
                           f"Código com {tamanho} bytes; o limite é {LIMITE_FONTE_BYTES} bytes.")
    return fonte, None


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

    @app.post("/api/v1/analyze")
    def analisar():
        fonte, falha = _ler_fonte()
        if falha:
            return falha
        # HTTP 200 inclusive com erro de compilação (ok: false), §1.8.
        return jsonify(service.analyze(fonte)), 200

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
