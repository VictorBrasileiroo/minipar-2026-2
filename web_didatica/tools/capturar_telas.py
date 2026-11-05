"""Captura as telas da Web didática usadas no relatório (WEB-05) e confere cada uma.

Abre a interface real (`server.py` + `src/service.py`) num Chrome ou Edge headless, executa os
passos do roteiro abaixo pela própria página (mesmos botões e campos que uma pessoa usa) e grava
uma captura PNG por passo em `docs/evidencias/WEB-05/`. Antes de cada captura o script confere o
que a tela mostra contra um oráculo que não vem da Web: códigos de diagnóstico das fixtures
geradas pelo compilador (`tools/gerar_fixtures.py`), stdout esperado do programa, oráculos do
Teste 11 (C-T11-v1 §3.1) e o SHA-256 dos `.arm` de referência de `tests/2026_2/test11/arm/`.
Se algum oráculo divergir, o script para com erro e não grava o manifesto.

`manifesto.json` registra, por captura: arquivo, SHA-256, o que foi conferido e os valores lidos
da página (request_id, códigos, stdout). As capturas são provas de tela; o oráculo é o que está
no manifesto, que pode ser repetido rodando o script de novo.

Comunicação com o navegador pelo Chrome DevTools Protocol, só com a biblioteca padrão. A porta
de depuração é escolhida pelo navegador e escuta só em 127.0.0.1; o perfil é temporário e
apagado no fim. Se `server.py` não estiver respondendo em 127.0.0.1:5001, o script o inicia com
o mesmo Python e o encerra no fim.

Uso, na raiz do repositório (precisa de g++ e de Chrome ou Edge instalados):
    .venv\\Scripts\\python.exe -B web_didatica/tools/capturar_telas.py
    .venv\\Scripts\\python.exe -B web_didatica/tools/capturar_telas.py --navegador "C:\\...\\chrome.exe"
    .venv\\Scripts\\python.exe -B web_didatica/tools/capturar_telas.py --saida <pasta>
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
RAIZ = WEB.parent
FIXTURES = WEB / "fixtures"
ARM_REF = RAIZ / "tests" / "2026_2" / "test11" / "arm"
SAIDA_PADRAO = RAIZ / "docs" / "evidencias" / "WEB-05"
BASE = "http://127.0.0.1:5001"
LARGURA, ALTURA = 1280, 860

NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

LACO_INFINITO = 'while (true) {\n    print(".");\n}\n'


class Falha(Exception):
    """Oráculo divergente ou passo que não terminou."""


# --------------------------------------------------------------------- WebSocket mínimo (RFC 6455)

class WebSocket:
    def __init__(self, url: str) -> None:
        partes = urllib.parse.urlparse(url)
        self.sock = socket.create_connection((partes.hostname, partes.port), timeout=120)
        chave = base64.b64encode(os.urandom(16)).decode()
        pedido = (f"GET {partes.path} HTTP/1.1\r\nHost: {partes.hostname}:{partes.port}\r\n"
                  f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {chave}\r\n"
                  "Sec-WebSocket-Version: 13\r\n\r\n")
        self.sock.sendall(pedido.encode())
        cabecalho = b""
        while b"\r\n\r\n" not in cabecalho:
            pedaco = self.sock.recv(1)
            if not pedaco:
                raise Falha("o navegador fechou a conexão de depuração")
            cabecalho += pedaco
        if b" 101 " not in cabecalho.split(b"\r\n", 1)[0]:
            raise Falha(f"handshake do WebSocket recusado: {cabecalho[:80]!r}")

    def _ler(self, n: int) -> bytes:
        dados = b""
        while len(dados) < n:
            pedaco = self.sock.recv(n - len(dados))
            if not pedaco:
                raise Falha("conexão de depuração encerrada")
            dados += pedaco
        return dados

    def _quadro(self, opcode: int, carga: bytes) -> None:
        mascara = os.urandom(4)
        n = len(carga)
        if n < 126:
            cab = struct.pack("!BB", 0x80 | opcode, 0x80 | n)
        elif n < 65536:
            cab = struct.pack("!BBH", 0x80 | opcode, 0x80 | 126, n)
        else:
            cab = struct.pack("!BBQ", 0x80 | opcode, 0x80 | 127, n)
        self.sock.sendall(cab + mascara + bytes(b ^ mascara[i % 4] for i, b in enumerate(carga)))

    def enviar(self, texto: str) -> None:
        self._quadro(0x1, texto.encode())

    def receber(self) -> str:
        mensagem = b""
        while True:
            b0, b1 = self._ler(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._ler(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._ler(8))[0]
            carga = self._ler(n)
            opcode = b0 & 0x0F
            if opcode == 0x9:
                self._quadro(0xA, carga)
                continue
            if opcode == 0x8:
                raise Falha("o navegador fechou o WebSocket")
            mensagem += carga
            if b0 & 0x80:
                return mensagem.decode()

    def fechar(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class CDP:
    def __init__(self, url: str) -> None:
        self.ws = WebSocket(url)
        self.n = 0

    def cmd(self, metodo: str, **params):
        self.n += 1
        self.ws.enviar(json.dumps({"id": self.n, "method": metodo, "params": params}))
        while True:
            msg = json.loads(self.ws.receber())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise Falha(f"{metodo}: {msg['error']}")
                return msg.get("result", {})

    def js(self, expressao: str):
        r = self.cmd("Runtime.evaluate", expression=expressao, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in r:
            detalhe = r["exceptionDetails"].get("exception", {}).get("description") or r["exceptionDetails"]
            raise Falha(f"erro de JavaScript na página: {detalhe}")
        return r["result"].get("value")

    def esperar(self, expressao: str, descricao: str, limite: float = 90.0):
        fim = time.monotonic() + limite
        while time.monotonic() < fim:
            valor = self.js(expressao)
            if valor:
                return valor
            time.sleep(0.2)
        raise Falha(f"tempo esgotado esperando: {descricao}")

    def navegar(self, url: str) -> None:
        self.cmd("Page.navigate", url=url)
        self.esperar("document.readyState === 'complete'", f"carregar {url}")
        self.js(AJUDANTES)

    def capturar(self, destino: Path) -> str:
        self.js("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
        dados = base64.b64decode(self.cmd("Page.captureScreenshot", format="png")["data"])
        destino.write_bytes(dados)
        return hashlib.sha256(dados).hexdigest()


# Funções usadas pelos passos. Só leem a página e acionam os mesmos controles de uma pessoa.
AJUDANTES = r"""
window.W5 = {
  q: (s) => document.querySelector(s),
  texto: (s) => (document.querySelector(s)?.innerText ?? ""),
  situacao: () => document.querySelector('#situacao')?.textContent ?? "",
  ocioso: () => {
    const a = document.querySelector('#analisar'), c = document.querySelector('#compilar');
    return Boolean(a && c) && a.textContent === 'Analisar' && c.textContent === 'Compilar e executar';
  },
  limparSituacao: () => { document.querySelector('#situacao').textContent = ''; },
  abrir: (arquivo) => {
    W5.limparSituacao();
    const s = document.querySelector('#fixture');
    s.value = arquivo;
    s.dispatchEvent(new Event('change'));
  },
  aba: (ancora) => { document.querySelector('#aba-' + ancora).click(); document.querySelector('#painel').scrollTop = 0; },
  botao: (rotulo) => [...document.querySelectorAll('button')].find((b) => b.textContent.trim() === rotulo),
  clicar: (rotulo) => { const b = W5.botao(rotulo); if (!b) throw new Error('botão ausente: ' + rotulo); b.click(); },
  codigo: (txt) => { const c = document.querySelector('#codigo'); c.value = txt; c.dispatchEvent(new Event('input')); },
  entrada: (txt) => { document.querySelector('#entrada').value = txt; },
  tempo: (s) => { document.querySelector('#tempo-limite').value = String(s); },
  rolarAte: (rotulo) => {
    const alvo = [...document.querySelectorAll('#painel h4')].find((h) => h.textContent.trim() === rotulo);
    if (!alvo) throw new Error('seção ausente: ' + rotulo);
    const p = document.querySelector('#painel');
    p.scrollTop += alvo.getBoundingClientRect().top - p.getBoundingClientRect().top - 8;
  },
  secao: (rotulo) => {
    const h = [...document.querySelectorAll('#painel h4')].find((x) => x.textContent.trim() === rotulo);
    // Linhas do bloco de código da seção (um <span> por linha; linha vazia aparece como " ").
    const pre = h?.parentElement.querySelector('pre');
    return pre ? [...pre.children].map((s) => s.textContent.trimEnd()).join('\n') : null;
  },
  codigos: () => [...document.querySelectorAll('#diagnosticos .erro-cartao')].map((c) => c.innerText),
  rodape: () => document.querySelector('#rodape')?.innerText ?? "",
};
true;
"""


def esperar_analise(cdp: CDP, descricao: str) -> str:
    return cdp.esperar(
        "W5.ocioso() && /^Análise concluída/.test(W5.situacao()) && W5.situacao()", descricao)


def esperar_execucao(cdp: CDP, descricao: str) -> str:
    # A execução termina quando os botões voltam ao rótulo normal e a seção Execução existe.
    return cdp.esperar(
        "W5.ocioso() && [...document.querySelectorAll('#painel h4')].some(h => h.textContent === 'Execução')"
        " && W5.situacao()", descricao, limite=180)


def conferir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise Falha(mensagem)


def codigos_esperados(arquivo: str) -> list[str]:
    dados = json.loads((FIXTURES / arquivo).read_text(encoding="utf-8"))
    return [d["code"] for d in dados["analyze"]["diagnostics"] if d["severity"] == "error"]


def normalizar(texto: str) -> str:
    """Texto como a página o mostra: sem CR, sem espaço no fim das linhas e sem a última quebra."""
    linhas = texto.replace("\r\n", "\n").split("\n")
    if linhas and linhas[-1] == "":
        linhas.pop()
    return "\n".join(linha.rstrip() for linha in linhas)


def sha256_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def id_da_compilacao(cdp: CDP) -> str:
    rodape = cdp.js("W5.rodape()")
    for linha in rodape.splitlines():
        if linha.startswith("request_id"):
            return linha.split()[-1]
    # O rodapé usa rótulo e valor em elementos vizinhos; sem quebra de linha, cai aqui.
    i = rodape.find("request_id")
    return rodape[i + len("request_id"):].split("source_hash")[0].strip() if i >= 0 else ""


# --------------------------------------------------------------------- roteiro

def roteiro(cdp: CDP, saida: Path, downloads: Path) -> list[dict]:
    registros: list[dict] = []

    def gravar(nome: str, titulo: str, conferido: list[str], lido: dict) -> None:
        arquivo = saida / f"{nome}.png"
        sha = cdp.capturar(arquivo)
        registros.append({"arquivo": arquivo.name, "sha256": sha, "titulo": titulo,
                          "conferido": conferido, "lido": lido})
        print(f"  PASS {arquivo.name}  {titulo}")

    cdp.navegar(BASE + "/static/index.html")
    cdp.esperar("W5.q('#fixture')?.options.length >= 8", "lista de exemplos")
    esperar_analise(cdp, "análise inicial do FIX-01")

    # 01–05: FIX-01 em cada fase.
    cdp.js("W5.abrir('fix-01-sucesso.json')")
    situacao = esperar_analise(cdp, "análise do FIX-01")
    conferir("sem erros" in situacao, f"FIX-01 deveria analisar sem erros: {situacao!r}")
    cdp.js("W5.aba('tokens')")
    tokens = cdp.js("W5.texto('#painel')")
    conferir("12 tokens" in tokens, "FIX-01 deveria ter 12 tokens")
    gravar("01_tokens", "FIX-01 analisado pelo serviço real: tabela de tokens",
           ["análise sem erros", "12 tokens (o mesmo número do envelope de fix-01-sucesso.json)"],
           {"situacao": situacao, "request_id": id_da_compilacao(cdp)})

    cdp.js("W5.aba('ast'); document.querySelector('#ast-n1 .no').click(); true")
    detalhe = cdp.js("W5.texto('#painel')")
    conferir("VarDecl" in detalhe, "nó VarDecl não apareceu na AST")
    gravar("02_ast", "FIX-01: AST recolhível com o nó VarDecl(x) selecionado e a linha destacada no editor",
           ["nó VarDecl(x) presente e selecionado"], {"estatistica": detalhe.split("\n")[2] if detalhe.count("\n") > 2 else ""})

    cdp.js("W5.aba('semantico')")
    sem = cdp.js("W5.texto('#painel')")
    gravar("03_semantico", "FIX-01: escopos e tabela de símbolos", ["painel do semântico aberto"], {"painel": sem[:400]})

    cdp.js("W5.aba('tac')")
    tac = cdp.js("W5.texto('#painel pre') || W5.texto('#painel')")
    gravar("04_tac", "FIX-01: código de três endereços (TAC)", ["painel do TAC aberto"], {"tac": tac[:400]})

    cdp.js("W5.aba('cpp')")
    cpp = cdp.js("W5.texto('#painel')")
    conferir("int main" in cpp, "o C++ gerado não tem main")
    gravar("05_cpp", "FIX-01: C++ gerado", ["C++ contém int main"], {})

    # 06: compilar e executar FIX-01.
    cdp.js("W5.entrada(''); W5.tempo(10); W5.limparSituacao(); W5.clicar('Compilar e executar'); true")
    situacao = esperar_execucao(cdp, "compilar e executar FIX-01")
    stdout = cdp.js("W5.secao('Saída (stdout)')")
    painel = cdp.js("W5.texto('#painel')")
    conferir(stdout is not None and stdout.strip() == "5", f"stdout de FIX-01 deveria ser 5: {stdout!r}")
    conferir("O programa terminou com código 0" in painel, "FIX-01 deveria terminar com código 0")
    conferir("código de retorno\n0" in painel or "código de retorno\t0" in painel, "g++ deveria retornar 0")
    gravar("06_compilar_executar", "FIX-01 compilado pelo g++ e executado: código 0, stdout 5",
           ["g++ com código de retorno 0", "execução com código 0", "stdout igual a '5'"],
           {"situacao": situacao, "stdout": stdout})
    cdp.js("W5.rolarAte('Saída (stdout)')")
    gravar("07_saida_e_downloads", "FIX-01: saída do programa e botões de download da compilação exibida",
           ["mesma execução da captura 06"], {})

    # 08–10: os três tipos de erro, com os códigos das fixtures geradas pelo compilador.
    for nome, arquivo, fase, aba in (("08_erro_lexico", "fix-02-erro-lexico.json", "léxico", "tokens"),
                                     ("09_erro_sintatico", "fix-03-erro-sintatico.json", "sintático", "ast"),
                                     ("10_erro_semantico", "fix-04-erro-semantico.json", "semântico", "semantico")):
        esperados = codigos_esperados(arquivo)
        cdp.js(f"W5.abrir({json.dumps(arquivo)})")
        situacao = esperar_analise(cdp, f"análise de {arquivo}")
        cdp.js(f"W5.aba({json.dumps(aba)})")
        cartoes = cdp.js("W5.codigos()")
        texto = "\n".join(cartoes)
        for codigo in esperados:
            conferir(codigo in texto, f"{arquivo}: código {codigo} esperado não aparece nos cartões")
        conferir(len(cartoes) == len(esperados), f"{arquivo}: {len(cartoes)} cartões, esperados {len(esperados)}")
        gravar(nome, f"Erro {fase} ({arquivo}): cartão do diagnóstico e fase com erro",
               [f"códigos {esperados} iguais aos da fixture gerada pelo compilador"],
               {"situacao": situacao, "cartoes": cartoes})

    # 11: programa maior (Teste 6) na AST.
    cdp.js("W5.abrir('prog-01-quicksort-classes.json')")
    situacao = esperar_analise(cdp, "análise do PROG-01")
    conferir("sem erros" in situacao, f"PROG-01 deveria analisar sem erros: {situacao!r}")
    cdp.js("W5.aba('ast')")
    estat = cdp.js("W5.texto('#painel .estat')")
    gravar("11_ast_programa_maior", "PROG-01 (Quicksort com classes, Teste 6): AST nos três primeiros níveis",
           ["análise sem erros"], {"situacao": situacao, "estatistica": estat})

    # 12: tempo esgotado.
    cdp.js("W5.abrir('fix-01-sucesso.json')")
    esperar_analise(cdp, "análise do FIX-01")
    cdp.js(f"W5.codigo({json.dumps(LACO_INFINITO)}); W5.tempo(2); W5.entrada(''); true")
    cdp.esperar("!W5.q('#compilar').disabled", "botão compilar habilitado")
    cdp.js("W5.limparSituacao(); W5.clicar('Compilar e executar'); true")
    esperar_execucao(cdp, "execução com laço infinito")
    painel = cdp.js("W5.texto('#painel')")
    conferir("Tempo esgotado" in painel, "laço infinito deveria terminar por tempo esgotado")
    conferir("tempo esgotado\nsim" in painel or "tempo esgotado\tsim" in painel, "timed_out deveria ser sim")
    cdp.js("W5.rolarAte('Execução')")
    gravar("12_tempo_esgotado", "Laço infinito com tempo limite de 2 s: encerrado pelo serviço, sem código de saída",
           ["caixa 'Tempo esgotado'", "timed_out = sim"], {})

    # 13–15: Teste 11 (MiniCompilador em MiniPar), casos 1 e 2, e o .arm.
    cdp.js("W5.abrir('/exemplos/t11.json')")
    situacao = esperar_analise(cdp, "análise do T11")
    conferir("sem erros" in situacao, f"T11 deveria analisar sem erros: {situacao!r}")
    cdp.js("W5.clicar('caso 1'); W5.tempo(10); W5.limparSituacao(); W5.clicar('Compilar e executar'); true")
    esperar_execucao(cdp, "compilar e executar o T11 (caso 1)")
    stdout = cdp.js("W5.secao('Saída (stdout)')") or ""
    conferir("➡️  22.0" in stdout, "caso 1 deveria imprimir ➡️  22.0")
    conferir("MUL    r8, r6, r7" not in stdout and "SUB    r8, r4, r7" in stdout,
             "caso 1 deveria terminar o Assembly com SUB r8, r4, r7")
    caso1_ref = (ARM_REF / "caso1.stdout.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    conferir(stdout == normalizar(caso1_ref),
             "stdout do caso 1 na Web difere de tests/2026_2/test11/arm/caso1.stdout.txt")
    id_t11 = id_da_compilacao(cdp)
    cdp.js("W5.rolarAte('Saída (stdout)')")
    gravar("13_t11_caso1", "Teste 11, caso 1 ((2+4)*7)-(5*4): stdout do MiniCompilador com resultado 22",
           ["stdout idêntico a tests/2026_2/test11/arm/caso1.stdout.txt", "resultado ➡️  22.0"], {})

    cdp.js("W5.clicar('caso 2'); W5.limparSituacao(); W5.clicar('Executar de novo com a entrada atual'); true")
    esperar_execucao(cdp, "executar de novo o T11 (caso 2)")
    stdout = cdp.js("W5.secao('Saída (stdout)')") or ""
    conferir("➡️  -84.0" in stdout, "caso 2 deveria imprimir ➡️  -84.0")
    caso2_ref = (ARM_REF / "caso2.stdout.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    conferir(stdout == normalizar(caso2_ref),
             "stdout do caso 2 na Web difere de tests/2026_2/test11/arm/caso2.stdout.txt")
    binario = cdp.js("W5.texto('#painel').match(/binário\\s+([0-9a-f]{32})/g)?.map(s => s.slice(-32)) ?? []")
    conferir(len(set(binario)) == 1 and binario[0] == id_t11,
             f"o caso 2 deveria rodar no binário {id_t11} da compilação do caso 1: {binario}")
    cdp.js("W5.rolarAte('Execução')")
    gravar("14_t11_caso2_executar_de_novo", "Teste 11, caso 2 ((10 -8*7)+4)*2 no mesmo binário, sem recompilar: -84",
           ["stdout idêntico a tests/2026_2/test11/arm/caso2.stdout.txt", "resultado ➡️  -84.0",
            "binário da execução igual ao da compilação do caso 1"], {"binario": id_t11})

    antes = set(downloads.iterdir())
    cdp.js("W5.rolarAte('Assembly ARMv7 (Teste 11)'); W5.clicar('Baixar .arm'); true")
    fim = time.monotonic() + 20
    novos: list[Path] = []
    while time.monotonic() < fim:
        novos = [p for p in set(downloads.iterdir()) - antes if p.suffix == ".arm"]
        if novos:
            break
        time.sleep(0.2)
    conferir(len(novos) == 1, "o download do .arm não aconteceu")
    sha_arm = sha256_arquivo(novos[0])
    sha_ref = sha256_arquivo(ARM_REF / "caso2.arm")
    conferir(sha_arm == sha_ref, f".arm baixado ({sha_arm}) difere de caso2.arm ({sha_ref})")
    situacao = cdp.js("W5.situacao()")
    cdp.js("W5.rolarAte('Assembly ARMv7 (Teste 11)')")
    gravar("15_t11_baixar_arm", "Teste 11: .arm do caso 2 recortado do stdout e baixado pelo navegador",
           [f"SHA-256 do .arm baixado igual ao de tests/2026_2/test11/arm/caso2.arm ({sha_ref[:16]}…)"],
           {"situacao": situacao, "arquivo": novos[0].name, "sha256": sha_arm})

    # 16: teste do recorte do .arm no navegador.
    cdp.navegar(BASE + "/static/testes/arm.html")
    resultado = json.loads(cdp.esperar("document.body.dataset.resultado", "resultado de arm.html"))
    conferir(resultado["passaram"] == resultado["total"] == 7, f"arm.html: {resultado['passaram']}/{resultado['total']}")
    gravar("16_teste_arm_html", "static/testes/arm.html: recorte do .arm no navegador igual ao de extrair_arm.py",
           ["7/7 PASS"], {"resultado": resultado})

    # 17: modo mock, para comparação.
    cdp.navegar(BASE + "/static/index.html?fonte=mock#executar")
    cdp.esperar("W5.q('#fixture')?.options.length >= 7", "lista de exemplos do mock")
    cdp.js("W5.abrir('exec-01-fix01.json')")
    cdp.esperar("W5.q('#painel').textContent.includes('O programa terminou com código 0')", "painel do EXEC-01 no mock")
    conferir("MOCK" in cdp.js("W5.texto('#aviso-mock')"), "aviso de mock ausente")
    gravar("17_modo_mock", "Modo mock (?fonte=mock): resultado gravado do EXEC-01, com Compilar e downloads desabilitados",
           ["faixa MOCK visível"], {})
    return registros


# --------------------------------------------------------------------- infraestrutura

def servidor_no_ar() -> bool:
    try:
        with urllib.request.urlopen(BASE + "/fixtures/index.json", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def achar_navegador(indicado: str | None) -> str:
    candidatos = [indicado] if indicado else [os.environ.get("CHROME"), *NAVEGADORES]
    for c in candidatos:
        if c and Path(c).is_file():
            return c
    raise Falha("Chrome/Edge não encontrado; informe --navegador ou a variável CHROME")


def abrir_navegador(executavel: str, perfil: Path) -> tuple[subprocess.Popen, CDP, str]:
    proc = subprocess.Popen([
        executavel, "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={perfil}", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--lang=pt-BR",
        f"--window-size={LARGURA},{ALTURA}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    arquivo = perfil / "DevToolsActivePort"
    fim = time.monotonic() + 30
    while not arquivo.exists() or not arquivo.read_text().strip():
        if time.monotonic() > fim or proc.poll() is not None:
            raise Falha("o navegador não abriu a porta de depuração")
        time.sleep(0.1)
    porta = arquivo.read_text().splitlines()[0].strip()
    with urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=5) as r:
        versao = json.load(r)["Browser"]
    with urllib.request.urlopen(f"http://127.0.0.1:{porta}/json/list", timeout=5) as r:
        pagina = next(t for t in json.load(r) if t["type"] == "page")
    return proc, CDP(pagina["webSocketDebuggerUrl"]), versao


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--navegador", help="caminho do Chrome ou Edge")
    ap.add_argument("--saida", type=Path, default=SAIDA_PADRAO, help="pasta das capturas")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    servidor = None
    if not servidor_no_ar():
        print("Iniciando web_didatica/server.py…")
        servidor = subprocess.Popen([sys.executable, "-B", str(WEB / "server.py")], cwd=RAIZ,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        fim = time.monotonic() + 30
        while not servidor_no_ar():
            if time.monotonic() > fim or servidor.poll() is not None:
                raise Falha("server.py não respondeu em 127.0.0.1:5001")
            time.sleep(0.2)

    perfil = Path(tempfile.mkdtemp(prefix="web05_perfil_"))
    downloads = Path(tempfile.mkdtemp(prefix="web05_downloads_"))
    proc = cdp = None
    try:
        executavel = achar_navegador(args.navegador)
        proc, cdp, versao = abrir_navegador(executavel, perfil)
        cdp.cmd("Page.enable")
        cdp.cmd("Emulation.setDeviceMetricsOverride", width=LARGURA, height=ALTURA, deviceScaleFactor=1, mobile=False)
        cdp.cmd("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
        cdp.cmd("Browser.setDownloadBehavior", behavior="allow", downloadPath=str(downloads))
        args.saida.mkdir(parents=True, exist_ok=True)
        print(f"Navegador: {versao}  ->  {args.saida}")
        inicio = datetime.now(timezone.utc).astimezone()
        registros = roteiro(cdp, args.saida, downloads)
        gpp = subprocess.run([os.environ.get("CXX", "g++"), "--version"], capture_output=True, text=True)
        manifesto = {
            "card": "WEB-05",
            "gerado_por": "web_didatica/tools/capturar_telas.py",
            "data": inicio.isoformat(timespec="seconds"),
            "ambiente": {
                "sistema": platform.platform(),
                "python": platform.python_version(),
                "navegador": versao,
                "gpp": gpp.stdout.splitlines()[0] if gpp.returncode == 0 and gpp.stdout else "indisponível",
                "janela": f"{LARGURA}x{ALTURA}, tema claro",
                "url": BASE,
            },
            "capturas": registros,
        }
        (args.saida / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
                                                   encoding="utf-8")
        print(f"PASS: {len(registros)} capturas conferidas; manifesto em {args.saida / 'manifesto.json'}")
        return 0
    except Falha as erro:
        print(f"FAIL: {erro}", file=sys.stderr)
        return 1
    finally:
        if cdp:
            cdp.ws.fechar()
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        if servidor:
            servidor.terminate()
            servidor.wait(timeout=10)
        time.sleep(0.5)
        shutil.rmtree(perfil, ignore_errors=True)
        shutil.rmtree(downloads, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
