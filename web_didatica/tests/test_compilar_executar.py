"""Testes das rotas de compilação, execução e download da Web didática (WEB-04).

Contrato C-WEB-v1 §1.3, §1.6, §1.7 e §1.8. Usam o cliente de teste do Flask (sem abrir porta),
o serviço real de src/service.py e o g++ de verdade: cada compilação gera e executa um binário.
Na raiz do repositório:
    .venv\\Scripts\\python.exe -B -m unittest discover -s web_didatica/tests -v
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
WEB = AQUI.parent
RAIZ = WEB.parent
sys.path.insert(0, str(WEB))
sys.path.insert(0, str(WEB / "tools"))

import server  # noqa: E402
import gerar_casos_arm  # noqa: E402
from extrair_arm import CASES, extract_arm  # noqa: E402  (tests/2026_2/test11, via gerar_casos_arm)

FASES = ["lexer", "parser", "semantic", "tac", "cpp", "gpp"]
ARM_REFERENCIA = RAIZ / "tests" / "2026_2" / "test11" / "arm"
EXTENSAO_BINARIO = ".exe" if os.name == "nt" else ""


def lf(texto: str) -> str:
    return texto.replace("\r\n", "\n")


def processos_vivos(caminho: str) -> bool:
    """True se algum processo com este executável ainda roda (só Windows; Linux não é o ambiente da prova)."""
    if os.name != "nt":
        return False
    saida = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {Path(caminho).name}", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, errors="replace").stdout
    return Path(caminho).name.lower() in saida.lower()


class Rotas:
    cliente = server.app.test_client()

    @classmethod
    def compilar(cls, fonte):
        resposta = cls.cliente.post("/api/v1/compile", json={"source": fonte})
        assert resposta.status_code == 200, resposta.get_data(as_text=True)
        return resposta.get_json()

    @classmethod
    def executar(cls, artefato, stdin="", timeout_sec=10, status=200):
        resposta = cls.cliente.post("/api/v1/execute", json={"artifact_id": artefato, "stdin": stdin, "timeout_sec": timeout_sec})
        assert resposta.status_code == status, resposta.get_data(as_text=True)
        return resposta.get_json()

    @classmethod
    def baixar(cls, artefato, tipo):
        return cls.cliente.get(f"/api/v1/artifacts/{artefato}/{tipo}")

    @classmethod
    def texto_baixado(cls, artefato, tipo):
        resposta = cls.baixar(artefato, tipo)
        try:
            assert resposta.status_code == 200, resposta.status_code
            return resposta.get_data(as_text=True)
        finally:
            resposta.close()


class CompilarExecutarTests(unittest.TestCase, Rotas):
    """Programas que o g++ compila: um por classe de teste para não recompilar à toa."""

    @classmethod
    def setUpClass(cls):
        cls.fix01 = cls.compilar("var x = 2 + 3;\nprint(x);\n")
        cls.um = cls.compilar("print(1);\n")
        cls.dois = cls.compilar("print(2);\n")
        cls.eco = cls.compilar('var a = input("");\nprint(a);\nvar b = input("");\nprint(b);\n')
        cls.laco = cls.compilar('while (true) {\n    print(".");\n}\n')
        cls.falha = cls.compilar('var s = "abc";\nprint(substr(s, 5, 2));\n')

    # ------------------------------------------------------------ compilação real

    def test_compile_fix01_tem_seis_fases_ok_e_binario_desta_requisicao(self):
        c = self.fix01
        self.assertEqual(c["contract"], "minipar.compile.v1")
        self.assertEqual(c["operation"], "compile")
        self.assertEqual(list(c["phases"]), FASES)
        self.assertTrue(c["ok"])
        for fase in FASES:
            self.assertEqual(c["phases"][fase]["status"], "ok", fase)
        gpp = c["phases"]["gpp"]
        self.assertEqual(gpp["returncode"], 0)  # returncode validado pelo serviço e conferido aqui
        self.assertIn("-o", gpp["command"])
        self.assertEqual(c["artifacts"], {"cpp_id": c["request_id"], "tac_id": c["request_id"], "binary_id": c["request_id"]})
        self.assertEqual(c["source_hash"], "sha256:" + hashlib.sha256(b"var x = 2 + 3;\nprint(x);\n").hexdigest())

    def test_execute_fix01_imprime_5_com_codigo_0(self):
        r = self.executar(self.fix01["artifacts"]["binary_id"])
        self.assertEqual(r["contract"], "minipar.execute.v1")
        self.assertEqual(r["artifact_id"], self.fix01["request_id"])
        self.assertTrue(r["ok"])
        self.assertEqual(r["exit_code"], 0)
        self.assertFalse(r["timed_out"])
        self.assertEqual(lf(r["stdout"]), "5\n")
        self.assertIsNone(r["error"])

    def test_stdin_inteiro_e_uma_linha_por_input(self):
        r = self.executar(self.eco["artifacts"]["binary_id"], stdin="primeira\nsegunda\n")
        self.assertTrue(r["ok"], r)
        self.assertEqual(lf(r["stdout"]), "primeira\nsegunda\n")

    def test_codigo_de_saida_diferente_de_zero_e_ok_false(self):
        self.assertTrue(self.falha["ok"])  # compila; o erro é de execução
        r = self.executar(self.falha["artifacts"]["binary_id"])
        self.assertFalse(r["ok"])
        self.assertNotEqual(r["exit_code"], 0)
        self.assertIsNotNone(r["exit_code"])
        self.assertFalse(r["timed_out"])
        self.assertIn("substr", r["stderr"])

    def test_timeout_encerra_o_processo_e_vem_no_envelope(self):
        artefato = self.laco["artifacts"]["binary_id"]
        caminho = server.service.get_artifact(artefato, "binary")["path"]
        inicio = time.monotonic()
        r = self.executar(artefato, timeout_sec=2)
        decorrido = time.monotonic() - inicio
        self.assertFalse(r["ok"])
        self.assertTrue(r["timed_out"])
        self.assertIsNone(r["exit_code"])
        self.assertLess(r["duration_ms"], 3500)
        self.assertLess(decorrido, 5)
        self.assertTrue(r["stdout"].startswith("."))
        self.assertFalse(processos_vivos(caminho), "binário ainda vivo depois do timeout")

    # ------------------------------------------------------------ downloads

    def test_downloads_sao_os_artefatos_desta_compilacao(self):
        c = self.fix01
        ident = c["request_id"]
        esperados = {
            "cpp": (f"minipar_{ident[:8]}.cpp", "text/x-c++src", c["phases"]["cpp"]["text"].encode("utf-8")),
            "tac": (f"minipar_{ident[:8]}.tac", "text/plain", c["phases"]["tac"]["text"].encode("utf-8")),
        }
        for tipo, (nome, midia, conteudo) in esperados.items():
            with self.subTest(tipo):
                resposta = self.baixar(ident, tipo)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta.mimetype, midia)
                self.assertIn("attachment", resposta.headers["Content-Disposition"])
                self.assertIn(nome, resposta.headers["Content-Disposition"])
                self.assertEqual(resposta.headers["Cache-Control"], "no-store")
                self.assertEqual(resposta.headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(resposta.get_data(), conteudo)
                resposta.close()

    def test_download_do_binario_e_o_executavel_que_roda(self):
        ident = self.fix01["request_id"]
        resposta = self.baixar(ident, "binary")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.mimetype, "application/octet-stream")
        self.assertIn(f"minipar_{ident[:8]}{EXTENSAO_BINARIO}", resposta.headers["Content-Disposition"])
        dados = resposta.get_data()
        resposta.close()
        caminho = Path(server.service.get_artifact(ident, "binary")["path"])
        self.assertEqual(hashlib.sha256(dados).hexdigest(), hashlib.sha256(caminho.read_bytes()).hexdigest())
        if os.name == "nt":
            self.assertEqual(dados[:2], b"MZ")

    def test_isolamento_cada_id_executa_e_baixa_a_propria_compilacao(self):
        id1, id2 = self.um["request_id"], self.dois["request_id"]
        self.assertNotEqual(id1, id2)
        self.assertNotEqual(self.um["source_hash"], self.dois["source_hash"])
        self.assertEqual(lf(self.executar(id1)["stdout"]), "1\n")
        self.assertEqual(lf(self.executar(id2)["stdout"]), "2\n")
        cpp1 = self.texto_baixado(id1, "cpp")
        cpp2 = self.texto_baixado(id2, "cpp")
        self.assertEqual(cpp1, self.um["phases"]["cpp"]["text"])
        self.assertEqual(cpp2, self.dois["phases"]["cpp"]["text"])
        self.assertNotEqual(cpp1, cpp2)

    def test_execucao_repetida_do_mesmo_binario_com_outra_entrada(self):
        artefato = self.eco["artifacts"]["binary_id"]
        self.assertEqual(lf(self.executar(artefato, stdin="a\nb\n")["stdout"]), "a\nb\n")
        self.assertEqual(lf(self.executar(artefato, stdin="c\nd\n")["stdout"]), "c\nd\n")


class FalhasDeCompilacaoTests(unittest.TestCase, Rotas):
    def test_erro_semantico_nao_chama_gpp_nem_registra_artefato(self):
        c = self.compilar("print(y);\n")
        self.assertFalse(c["ok"])
        self.assertEqual(c["phases"]["semantic"]["status"], "error")
        for fase in ("tac", "cpp", "gpp"):
            self.assertEqual(c["phases"][fase], {"status": "skipped", "reason": "previous_phase_failed"})
        self.assertEqual(c["artifacts"], {"cpp_id": None, "tac_id": None, "binary_id": None})
        self.assertEqual(self.baixar(c["request_id"], "cpp").status_code, 404)

    def test_gpp_ausente_vira_gpp_not_found_sem_binario(self):
        with mock.patch.dict(os.environ, {"CXX": str(RAIZ / "nao_existe_gpp_web04.exe")}):
            c = self.compilar("print(1);\n")
        self.assertFalse(c["ok"])
        self.assertEqual(c["phases"]["gpp"]["status"], "error")
        self.assertIn("GPP_NOT_FOUND", [d["code"] for d in c["diagnostics"]])
        self.assertIsNone(c["artifacts"]["binary_id"])
        self.assertEqual(c["artifacts"]["cpp_id"], c["request_id"])
        resposta = self.baixar(c["request_id"], "binary")
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.get_json()["error"]["code"], "ARTIFACT_NOT_FOUND")
        # O .cpp desta compilação continua disponível.
        self.assertEqual(self.texto_baixado(c["request_id"], "cpp"), c["phases"]["cpp"]["text"])
        r = self.executar(c["request_id"])
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"]["code"], "ARTIFACT_NOT_FOUND")

    def test_gpp_com_codigo_de_retorno_diferente_de_zero_vira_gpp_failed(self):
        # Um "compilador" que sempre falha: o Python recusa as opções do g++ com código 2.
        with mock.patch.dict(os.environ, {"CXX": sys.executable}):
            c = self.compilar("print(1);\n")
        gpp = c["phases"]["gpp"]
        self.assertFalse(c["ok"])
        self.assertEqual(gpp["status"], "error")
        self.assertNotEqual(gpp["returncode"], 0)
        self.assertTrue(gpp["stderr"])
        self.assertIn("GPP_FAILED", [d["code"] for d in c["diagnostics"]])
        self.assertIsNone(c["artifacts"]["binary_id"])


class ValidacaoDasRotasTests(unittest.TestCase, Rotas):
    def test_compile_rejeita_requisicao_malformada_como_analyze(self):
        casos = [
            dict(data="não é json", content_type="application/json"),
            dict(json=[1, 2]),
            dict(json={}),
            dict(json={"source": 5}),
            dict(json={"source": "a" * (server.LIMITE_FONTE_BYTES + 1)}),
        ]
        for kwargs in casos:
            with self.subTest(kwargs=str(kwargs)[:60]):
                resposta = self.cliente.post("/api/v1/compile", **kwargs)
                self.assertEqual(resposta.status_code, 400)
                self.assertEqual(resposta.get_json()["error"]["code"], "BAD_REQUEST")

    def test_execute_rejeita_timeout_e_campos_invalidos_com_400(self):
        valido = "0" * 32
        casos = [
            {"artifact_id": valido, "timeout_sec": 0},
            {"artifact_id": valido, "timeout_sec": 31},
            {"artifact_id": valido, "timeout_sec": "10"},
            {"artifact_id": valido, "timeout_sec": 10.0},
            {"artifact_id": valido, "timeout_sec": True},
            {"artifact_id": valido, "stdin": 3},
            {"stdin": ""},
            {"artifact_id": 7},
        ]
        for corpo in casos:
            with self.subTest(corpo=corpo):
                resposta = self.cliente.post("/api/v1/execute", json=corpo)
                self.assertEqual(resposta.status_code, 400)
                self.assertEqual(resposta.get_json()["error"]["code"], "BAD_REQUEST")
        resposta = self.cliente.post("/api/v1/execute", data="x", content_type="text/plain")
        self.assertEqual(resposta.status_code, 400)

    def test_execute_id_invalido_ou_inexistente_vem_no_envelope(self):
        r = self.executar("../x")
        self.assertEqual(r["contract"], "minipar.execute.v1")
        self.assertEqual(r["error"]["code"], "INVALID_ARGUMENT")
        self.assertIsNone(r["exit_code"])
        r = self.executar("f" * 32)
        self.assertEqual(r["error"]["code"], "ARTIFACT_NOT_FOUND")
        self.assertFalse(r["ok"])

    def test_execute_sem_timeout_usa_o_padrao_de_10(self):
        with mock.patch.object(server.service, "execute", return_value={"contract": "minipar.execute.v1"}) as chamado:
            resposta = self.cliente.post("/api/v1/execute", json={"artifact_id": "a" * 32})
        self.assertEqual(resposta.status_code, 200)
        chamado.assert_called_once_with("a" * 32, stdin="", timeout_sec=10)

    def test_download_tipo_ou_id_invalido_e_400_inexistente_e_404(self):
        for caminho in [f"/api/v1/artifacts/{'0' * 32}/arm", "/api/v1/artifacts/zz/cpp", "/api/v1/artifacts/..%2Fx/cpp"]:
            with self.subTest(caminho):
                resposta = self.cliente.get(caminho)
                self.assertIn(resposta.status_code, (400, 404))
                self.assertIn("error", resposta.get_json())
        resposta = self.baixar("0" * 32, "arm")
        self.assertEqual(resposta.status_code, 400)
        resposta = self.baixar("f" * 32, "binary")
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.get_json()["error"]["code"], "ARTIFACT_NOT_FOUND")

    def test_metodos_errados_respondem_json(self):
        self.assertEqual(self.cliente.get("/api/v1/compile").status_code, 405)
        self.assertEqual(self.cliente.get("/api/v1/execute").status_code, 405)
        self.assertEqual(self.cliente.post(f"/api/v1/artifacts/{'0' * 32}/cpp").status_code, 405)


class TesteOnzeTests(unittest.TestCase, Rotas):
    """T11 pela Web: compila o MiniCompilador, executa os três casos e recorta o .arm."""

    def test_exemplo_t11_e_o_programa_do_repositorio(self):
        resposta = self.cliente.get("/exemplos/t11.json")
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.get_json()
        self.assertEqual(dados["fixture"], "T11")
        self.assertEqual(dados["source"], server.PROGRAMA_T11.read_text(encoding="utf-8"))
        self.assertEqual(dados["stdin"], CASES["caso1"] + "\n")

    def test_tres_casos_geram_o_mesmo_arm_do_script_e_da_referencia(self):
        fonte = self.cliente.get("/exemplos/t11.json").get_json()["source"]
        c = self.compilar(fonte)
        self.assertTrue(c["ok"], [d["code"] for d in c["diagnostics"]])
        for nome, expressao in CASES.items():
            with self.subTest(nome):
                r = self.executar(c["artifacts"]["binary_id"], stdin=expressao + "\n", timeout_sec=30)
                self.assertTrue(r["ok"], r.get("stderr"))
                self.assertFalse(r["stdout_truncated"])
                arm = extract_arm(r["stdout"])
                self.assertEqual(arm.encode("utf-8"), (ARM_REFERENCIA / f"{nome}.arm").read_bytes())


class CasosArmTests(unittest.TestCase):
    """O arquivo que a página static/testes/arm.html usa confere com extrair_arm.py."""

    def test_arm_casos_json_atualizado(self):
        # JSON lido, não bytes: o fim de linha do arquivo pode mudar no checkout (core.autocrlf).
        gravado = json.loads(gerar_casos_arm.SAIDA.read_bytes().decode("utf-8"))
        self.assertEqual(gravado, gerar_casos_arm.gerar())

    def test_seis_casos_dois_validos_iguais_a_referencia(self):
        casos = gerar_casos_arm.gerar()["casos"]
        self.assertEqual(len(casos), 6)
        validos = [c["esperado"]["arm"] for c in casos if "arm" in c["esperado"]]
        self.assertEqual([c["id"] for c in casos if "arm" in c["esperado"]], ["valido_lf", "valido_crlf"])
        self.assertEqual(validos[0], validos[1])
        self.assertEqual(validos[0].encode("utf-8"), (ARM_REFERENCIA / "caso1.arm").read_bytes())
        erros = {c["id"]: c["esperado"]["erro"] for c in casos if "erro" in c["esperado"]}
        self.assertEqual(erros, {
            "titulo_ausente": "título do Assembly ausente",
            "titulo_repetido": "título do Assembly repetido",
            "sem_global_start": "bloco do Assembly não começa com .global _start",
            "sem_linha_vazia": "bloco do Assembly sem a linha vazia que o fecha",
        })


if __name__ == "__main__":
    unittest.main()
