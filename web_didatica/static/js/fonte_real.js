// Fonte de dados do serviço real (WEB-03 e WEB-04): envia o código a web_didatica/server.py, que
// chama src/service.py (Eixo A). Nenhum resultado de fase ou de execução vem de arquivo: as
// fixtures só fornecem o código-fonte (e a entrada) dos exemplos, e análise, compilação e execução
// são sempre feitas pelo compilador e pelo binário no momento do pedido.
const BASE_FIXTURES = "/fixtures/";
const API = "/api/v1/";

export const modo = "real";

async function lerJson(url) {
  const resposta = await fetch(url, { cache: "no-store" });
  if (!resposta.ok) throw new Error(`Não foi possível ler ${url} (HTTP ${resposta.status}).`);
  return resposta.json();
}

// Os exemplos das fixtures e o programa do Teste 11, servido por server.py a partir de
// tests/2026_2/test11/minicompilador.minipar.
export async function listarExemplos() {
  const indice = await lerJson(BASE_FIXTURES + "index.json");
  return [...indice.fixtures, { fixture: "T11", title: "Teste 11: MiniCompilador em MiniPar (gera o .arm)", file: "/exemplos/t11.json" }];
}

// Devolve só o código e a entrada do exemplo; `analise` e `execucao` ficam null até o pedido.
export async function carregarExemplo(arquivo) {
  const dados = await lerJson(arquivo.startsWith("/") ? arquivo : BASE_FIXTURES + arquivo);
  return { id: dados.fixture, titulo: dados.title, codigo: dados.source, entrada: dados.stdin ?? "", notas: [], analise: null, execucao: null };
}

// POST com corpo JSON. HTTP 200 traz o envelope `contrato`, mesmo com erro do programa;
// 400/404/500 trazem {"error": {code, message}} (C-WEB-v1 §1.8).
async function postar(rota, corpo, contrato) {
  let resposta;
  try {
    resposta = await fetch(API + rota, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
      cache: "no-store",
    });
  } catch (erro) {
    throw new Error(`O servidor da Web didática não respondeu (${erro.message}).`);
  }
  let dados = null;
  try { dados = await resposta.json(); } catch { /* corpo não é JSON */ }
  if (resposta.ok && dados?.contract === contrato) return dados;
  if (dados?.error) throw new Error(`HTTP ${resposta.status} ${dados.error.code}: ${dados.error.message}`);
  throw new Error(`HTTP ${resposta.status}: a rota /api/v1/${rota} não devolveu um envelope ${contrato}.`);
}

// POST /api/v1/analyze: Lexer até C++, sem g++.
export function analisar(source) {
  return postar("analyze", { source }, "minipar.compile.v1");
}

// POST /api/v1/compile: as seis fases, com g++ e artefatos desta requisição.
export function compilar(source) {
  return postar("compile", { source }, "minipar.compile.v1");
}

// POST /api/v1/execute: executa o binário do artifact_id informado (minipar.execute.v1).
export function executar(artifactId, stdin, timeoutSec) {
  return postar("execute", { artifact_id: artifactId, stdin, timeout_sec: timeoutSec }, "minipar.execute.v1");
}

// GET /api/v1/artifacts/<id>/<kind>: o navegador baixa o arquivo com o nome do §1.7.
export function urlArtefato(artifactId, tipo) {
  return `${API}artifacts/${encodeURIComponent(artifactId)}/${encodeURIComponent(tipo)}`;
}
