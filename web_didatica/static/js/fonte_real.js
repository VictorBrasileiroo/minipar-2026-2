// Fonte de dados do serviço real (WEB-03): envia o código a web_didatica/server.py, que chama
// src/service.py (Eixo A). Nenhum resultado de fase vem de arquivo: as fixtures só fornecem o
// código-fonte dos exemplos, e a análise é sempre feita pelo compilador no momento do pedido.
const BASE_FIXTURES = "/fixtures/";
const API = "/api/v1/";

export const modo = "real";

async function lerJson(arquivo) {
  const resposta = await fetch(BASE_FIXTURES + arquivo, { cache: "no-store" });
  if (!resposta.ok) throw new Error(`Não foi possível ler ${arquivo} (HTTP ${resposta.status}).`);
  return resposta.json();
}

export async function listarExemplos() {
  const indice = await lerJson("index.json");
  // EXEC-* são exemplos de compilar e executar, que entram com as rotas do WEB-04.
  return indice.fixtures.filter((e) => !e.fixture.startsWith("EXEC-"));
}

// Devolve só o código do exemplo; `analise` fica null até a resposta de analisar().
export async function carregarExemplo(arquivo) {
  const dados = await lerJson(arquivo);
  return { id: dados.fixture, titulo: dados.title, codigo: dados.source, entrada: "", notas: [], analise: null, execucao: null };
}

// POST /api/v1/analyze (C-WEB-v1 §1.8). HTTP 200 traz o envelope minipar.compile.v1, mesmo com
// erro de compilação; 400/500 trazem {"error": {code, message}}.
export async function analisar(source) {
  let resposta;
  try {
    resposta = await fetch(API + "analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
      cache: "no-store",
    });
  } catch (erro) {
    throw new Error(`O servidor da Web didática não respondeu (${erro.message}).`);
  }
  let corpo = null;
  try { corpo = await resposta.json(); } catch { /* corpo não é JSON */ }
  if (resposta.ok && corpo?.contract === "minipar.compile.v1") return corpo;
  if (corpo?.error) throw new Error(`HTTP ${resposta.status} ${corpo.error.code}: ${corpo.error.message}`);
  throw new Error(`HTTP ${resposta.status}: a rota /api/v1/analyze não devolveu um envelope minipar.compile.v1.`);
}
