"""Testes do servidor da Web didática (WEB-03), contrato C-WEB-v1 §1.3 e §1.8.

Usam o cliente de teste do Flask (sem abrir porta) e o serviço real de src/service.py.
Na raiz do repositório:
    .venv\\Scripts\\python.exe -B -m unittest discover -s web_didatica/tests -v
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
WEB = AQUI.parent
sys.path.insert(0, str(WEB))

import server  # noqa: E402

FIXTURES = WEB / "fixtures"
FASES = ["lexer", "parser", "semantic", "tac", "cpp", "gpp"]


def fixture(nome):
    return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))


def sem_volateis(envelope):
    """Remove só o que o ACE-01 do contrato permite ignorar: request_id, duration_ms e o texto C++."""
    e = copy.deepcopy(envelope)
    e.pop("request_id")
    e.pop("duration_ms")
    e["phases"]["cpp"].pop("text", None)
    return e


class ServidorAnalyzeTests(unittest.TestCase):
    def setUp(self):
        self.cliente = server.app.test_client()

    def analisar(self, fonte):
        return self.cliente.post("/api/v1/analyze", json={"source": fonte})

    # ------------------------------------------------------------ fidelidade ao compilador real

    def test_fixtures_01_a_04_pelo_servico_real(self):
        """Positivo e erros léxico, sintático e semântico iguais às fixtures aprovadas (§1.9)."""
        for nome in ["fix-01-sucesso.json", "fix-02-erro-lexico.json", "fix-03-erro-sintatico.json", "fix-04-erro-semantico.json"]:
            with self.subTest(nome):
                dados = fixture(nome)
                resposta = self.analisar(dados["source"])
                self.assertEqual(resposta.status_code, 200)
                corpo = resposta.get_json()
                self.assertEqual(sem_volateis(corpo), sem_volateis(dados["analyze"]))
                # Não é a fixture devolvida: o id é novo, não o "000…01" gravado no arquivo.
                self.assertNotEqual(corpo["request_id"], dados["analyze"]["request_id"])
                self.assertRegex(corpo["request_id"], r"^[0-9a-f]{32}$")

    def test_codigo_novo_nao_vem_de_fixture(self):
        fonte = "var resposta = 6 * 7;\nprint(resposta);\n"
        corpo = self.analisar(fonte).get_json()
        self.assertTrue(corpo["ok"])
        self.assertEqual(corpo["source_hash"], "sha256:" + hashlib.sha256(fonte.encode("utf-8")).hexdigest())
        lexemas = [t["lexeme"] for t in corpo["phases"]["lexer"]["tokens"]]
        self.assertEqual(lexemas[:7], ["var", "resposta", "=", "6", "*", "7", ";"])
        self.assertIn("resposta", [s["name"] for s in corpo["phases"]["semantic"]["symbols"]])
        self.assertEqual(corpo["diagnostics"], [])

    def test_erro_novo_e_fiel(self):
        corpo = self.analisar("var a = 1;\nprint(zeta);\n").get_json()
        self.assertFalse(corpo["ok"])
        self.assertEqual([d["code"] for d in corpo["diagnostics"]], ["SEM_UNDECLARED_VARIABLE"])
        self.assertEqual(corpo["diagnostics"][0]["line"], 2)
        self.assertIn("zeta", corpo["diagnostics"][0]["message"])
        self.assertEqual(corpo["phases"]["tac"], {"status": "skipped", "reason": "previous_phase_failed"})

    def test_ids_novos_a_cada_chamada(self):
        fonte = fixture("fix-01-sucesso.json")["source"]
        a, b = self.analisar(fonte).get_json(), self.analisar(fonte).get_json()
        self.assertNotEqual(a["request_id"], b["request_id"])
        self.assertEqual(a["source_hash"], b["source_hash"])

    def test_utf8_e_crlf_sao_repassados_sem_alteracao(self):
        fonte = 'var s = "ação";\r\nprint(s);\r\n'
        corpo = self.analisar(fonte).get_json()
        self.assertEqual(corpo["source_hash"], "sha256:" + hashlib.sha256(fonte.encode("utf-8")).hexdigest())

    def test_ordem_das_fases_no_json(self):
        texto = self.analisar("print(1);\n").get_data(as_text=True)
        posicoes = [texto.index(f'"{fase}"') for fase in FASES]
        self.assertEqual(posicoes, sorted(posicoes))
        self.assertEqual(list(json.loads(texto)["phases"]), FASES)

    def test_analyze_nunca_pede_gpp_nem_artefatos(self):
        corpo = self.analisar("print(1);\n").get_json()
        self.assertEqual(corpo["phases"]["gpp"], {"status": "skipped", "reason": "not_requested"})
        self.assertEqual(corpo["artifacts"], {"cpp_id": None, "tac_id": None, "binary_id": None})

    # ------------------------------------------------------------ HTTP 400 (§1.8)

    def assert_bad_request(self, resposta):
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["error"]["code"], "BAD_REQUEST")
        self.assertTrue(resposta.get_json()["error"]["message"])

    def test_requisicoes_malformadas(self):
        url = "/api/v1/analyze"
        casos = {
            "json inválido": dict(data="{source:", content_type="application/json"),
            "não é objeto": dict(json=["print(1);"]),
            "source ausente": dict(json={"codigo": "print(1);"}),
            "source não é texto": dict(json={"source": 42}),
            "source null": dict(json={"source": None}),
            "sem content-type json": dict(data='{"source": "print(1);"}', content_type="text/plain"),
            "surrogate isolado": dict(data='{"source": "\\ud800"}', content_type="application/json"),
        }
        for nome, kwargs in casos.items():
            with self.subTest(nome):
                self.assert_bad_request(self.cliente.post(url, **kwargs))

    def test_limite_de_200000_bytes(self):
        no_limite = "#" * (server.LIMITE_FONTE_BYTES - len("\nprint(1);\n")) + "\nprint(1);\n"
        self.assertEqual(len(no_limite.encode("utf-8")), server.LIMITE_FONTE_BYTES)
        resposta = self.analisar(no_limite)
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.get_json()["ok"])
        self.assert_bad_request(self.analisar(no_limite + " "))
        # Conta bytes UTF-8, não caracteres: 100 001 "é" são 200 002 bytes.
        self.assert_bad_request(self.analisar("é" * 100_001))

    def test_corpo_acima_do_teto_vira_400(self):
        corpo = json.dumps({"source": "a" * (server.LIMITE_CORPO_BYTES + 1)})
        self.assert_bad_request(self.cliente.post("/api/v1/analyze", data=corpo, content_type="application/json"))

    def test_metodo_errado_e_rota_inexistente_respondem_json(self):
        r = self.cliente.get("/api/v1/analyze")
        self.assertEqual(r.status_code, 405)
        self.assertIn("error", r.get_json())
        r = self.cliente.post("/api/v1/nada", json={"source": ""})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"]["code"], "NOT_FOUND")

    # ------------------------------------------------------------ falha do servidor (§1.8: HTTP 500)

    def test_falha_do_servidor_vira_500_sem_stack_trace(self):
        with mock.patch.object(server.service, "analyze", side_effect=RuntimeError("segredo interno")), \
             self.assertLogs(server.__name__, level="ERROR"):
            r = self.analisar("print(1);\n")
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.get_json()["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("segredo", r.get_data(as_text=True))


class ServidorArquivosTests(unittest.TestCase):
    def setUp(self):
        self.cliente = server.app.test_client()

    def test_pagina_e_estaticos(self):
        r = self.cliente.get("/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/static/index.html"))
        for caminho in ["/static/index.html", "/static/js/app.js", "/static/js/fonte_real.js", "/static/css/app.css"]:
            with self.subTest(caminho):
                r = self.cliente.get(caminho)
                self.assertEqual(r.status_code, 200)
                r.close()

    def test_fixtures_so_json_da_pasta(self):
        r = self.cliente.get("/fixtures/index.json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("fixtures", r.get_json())
        r.close()
        for caminho in ["/fixtures/README.md", "/fixtures/..%2Fserver.py", "/fixtures/../server.py", "/fixtures/..%2F..%2Fsrc%2Fservice.json"]:
            with self.subTest(caminho):
                r = self.cliente.get(caminho)
                self.assertEqual(r.status_code, 404)
                r.close()

    def test_escuta_so_localhost(self):
        self.assertEqual(server.HOST, "127.0.0.1")
        self.assertEqual(server.PORTA, 5001)


if __name__ == "__main__":
    unittest.main()
