// Fonte de dados do modo mock (WEB-01): lê as fixtures de web_didatica/fixtures/.
// Só é usada com ?fonte=mock; o padrão é a fonte real (fonte_real.js, WEB-03), com o mesmo formato.
// Não tem analisar(): no mock o botão Analisar fica desabilitado.
const BASE = "/fixtures/";

async function lerJson(arquivo) {
  const resposta = await fetch(BASE + arquivo, { cache: "no-store" });
  if (!resposta.ok) throw new Error(`Não foi possível ler ${arquivo} (HTTP ${resposta.status}).`);
  return resposta.json();
}

export const modo = "mock";

export async function listarExemplos() {
  const indice = await lerJson("index.json");
  return indice.fixtures;
}

// Devolve { id, titulo, codigo, entrada, notas, analise, execucao }.
// `analise` é o envelope minipar.compile.v1 (analyze ou compile); `execucao` é minipar.execute.v1 ou null.
export async function carregarExemplo(arquivo) {
  const dados = await lerJson(arquivo);
  return {
    id: dados.fixture,
    titulo: dados.title,
    codigo: dados.source,
    entrada: dados.stdin ?? "",
    notas: dados.notes || [],
    analise: dados.analyze || dados.compile,
    execucao: dados.execute || null,
  };
}
