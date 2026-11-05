// Web didática. Desenha as fases a partir do envelope C-WEB-v1. Por padrão os dados vêm do serviço
// real (fonte_real.js → server.py → src/service.py: análise no WEB-03, compilação, execução e
// downloads no WEB-04); com ?fonte=mock, das fixtures (WEB-01).
import { armDaExecucao, SUFIXO_TITULO } from "./arm.js";
import * as fonteMock from "./fonte_mock.js";
import * as fonteReal from "./fonte_real.js";
import { criarArvoreAst } from "./arvore_ast.js";
import { contextoErros, criarCartaoErro } from "./erros.js";

const FASES = [
  { chave: "lexer", ancora: "tokens", nome: "Tokens" },
  { chave: "parser", ancora: "ast", nome: "AST" },
  { chave: "semantic", ancora: "semantico", nome: "Semântico" },
  { chave: "tac", ancora: "tac", nome: "TAC" },
  { chave: "cpp", ancora: "cpp", nome: "C++" },
  { chave: "gpp", ancora: "executar", nome: "Compilar e executar" },
];
const NOME_FASE = Object.fromEntries(FASES.map((f) => [f.chave, f.nome]));
NOME_FASE.internal = "Interno";

const EXPLICA = {
  lexer: "O analisador léxico lê o código caractere a caractere e agrupa os caracteres em tokens: palavras-chave, nomes, números, operadores e pontuação.",
  parser: "O analisador sintático organiza os tokens numa árvore (AST) que segue a gramática do MiniPar. Cada nó mostra o campo do pai que o contém e a linha de origem.",
  semantic: "O analisador semântico confere se nomes foram declarados, se tipos são compatíveis e quantos argumentos cada chamada recebe. Aqui aparecem os escopos abertos e os símbolos de cada um.",
  tac: "O código de três endereços (TAC) quebra o programa em instruções simples, com no máximo um operador cada, usando temporários t0, t1…",
  cpp: "O gerador traduz a AST para C++. Este é o texto que seria gravado no arquivo .cpp e entregue ao g++.",
  gpp: "Compila o C++ com o g++ e executa o binário desta compilação, com a entrada (stdin) e o tempo limite escolhidos ao lado do editor. Os downloads são os arquivos desta compilação, identificados pelo request_id.",
};

const fonte = new URLSearchParams(location.search).get("fonte") === "mock" ? fonteMock : fonteReal;
const REAL = fonte.modo === "real";

const $ = (id) => document.getElementById(id);
// exemplo.codigo: código original do exemplo (Restaurar). exemplo.codigoAnalisado: código que gerou
// exemplo.analise; é dele que saem os trechos dos diagnósticos.
// estado.ocupado: null, "analisar", "compilar" ou "executar" (pedido em andamento no serviço).
const estado = { exemplos: [], exemplo: null, fase: "lexer", descartada: false, arvore: null, linhaDestacada: null,
  filtroSimbolos: "", ocupado: null };

// Os três casos obrigatórios do Teste 11 (C-T11-v1 §3.1), uma expressão por execução.
const CASOS_T11 = [["caso 1", "((2+4)*7)-(5*4)"], ["caso 2", "((10 -8*7)+4)*2"], ["caso 3", "((2+4)*7)-(5*4)"]];

function h(tag, atributos = {}, ...filhos) {
  const el = document.createElement(tag);
  for (const [nome, valor] of Object.entries(atributos)) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (nome === "class") el.className = valor;
    else if (nome.startsWith("on")) el.addEventListener(nome.slice(2), valor);
    else el.setAttribute(nome, valor === true ? "" : valor);
  }
  for (const filho of filhos.flat()) {
    if (filho === null || filho === undefined || filho === false) continue;
    el.append(filho instanceof Node ? filho : String(filho));
  }
  return el;
}

async function sha256(texto) {
  if (!globalThis.crypto?.subtle) return null;
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return "sha256:" + [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// ---------------------------------------------------------------- estado das fases

function dadosFase(chave) {
  return estado.exemplo.analise.phases[chave];
}

function statusFase(chave) {
  if (estado.descartada || !estado.exemplo.analise) return "stale";
  if (chave === "gpp" && estado.exemplo.execucao && dadosFase("gpp").status === "ok") {
    return estado.exemplo.execucao.ok ? "ok" : "error";
  }
  return dadosFase(chave).status;
}

function primeiraFaseComErro() {
  return FASES.find((f) => dadosFase(f.chave).status === "error")?.chave;
}

// ---------------------------------------------------------------- editor e diagnósticos

function atualizarNumeros() {
  const linhas = $("codigo").value.split("\n").length;
  $("numeros").textContent = Array.from({ length: linhas }, (_, i) => i + 1).join("\n");
}

// Faixa atrás do texto do editor marcando uma linha (nó da AST selecionado ou diagnóstico).
function posicionarDestaque() {
  const faixa = $("linha-destaque");
  const linha = estado.linhaDestacada;
  faixa.hidden = !linha;
  if (!linha) return;
  const area = $("codigo");
  const estilo = getComputedStyle(area);
  const altura = parseFloat(estilo.lineHeight);
  faixa.style.top = `${parseFloat(estilo.paddingTop) + (linha - 1) * altura - area.scrollTop}px`;
  faixa.style.height = `${altura}px`;
}

function destacarLinha(linha) {
  estado.linhaDestacada = linha || null;
  if (linha) {
    const area = $("codigo");
    const altura = parseFloat(getComputedStyle(area).lineHeight);
    const topo = (linha - 1) * altura;
    if (topo < area.scrollTop || topo + altura > area.scrollTop + area.clientHeight - altura) {
      area.scrollTop = Math.max(0, topo - area.clientHeight / 2);
      $("numeros").scrollTop = area.scrollTop;
    }
  }
  posicionarDestaque();
}

function selecionarLinha(linha) {
  const texto = $("codigo").value;
  let inicio = 0;
  for (let i = 1; i < linha; i++) {
    const quebra = texto.indexOf("\n", inicio);
    if (quebra < 0) break;
    inicio = quebra + 1;
  }
  const fim = texto.indexOf("\n", inicio);
  const area = $("codigo");
  area.focus();
  area.setSelectionRange(inicio, fim < 0 ? texto.length : fim);
}

function desenharDiagnosticos() {
  const lista = $("diagnosticos");
  lista.replaceChildren();
  if (estado.descartada) {
    lista.append(h("li", { class: "caixa descartado" }, "Diagnósticos ocultos: a resposta foi descartada porque o código mudou."));
    return;
  }
  if (!estado.exemplo.analise) {
    lista.append(h("li", { class: "diag-vazio" }, estado.ocupado ? "Aguardando o serviço…" : "Sem análise."));
    return;
  }
  const diagnosticos = estado.exemplo.analise.diagnostics;
  if (!diagnosticos.length) {
    lista.append(h("li", { class: "diag-vazio" }, "Nenhum diagnóstico."));
    return;
  }
  const ctx = contextoDosErros();
  for (const d of diagnosticos) lista.append(h("li", {}, criarCartaoErro(d, ctx, { aoAbrir: abrirDiagnostico })));
}

function contextoDosErros() {
  return contextoErros(estado.exemplo.codigoAnalisado, dadosFase("lexer").tokens || []);
}

function abrirDiagnostico(d) {
  if (NOME_FASE[d.phase] && d.phase !== "internal") selecionarFase(d.phase);
  if (d.line) {
    selecionarLinha(d.line);
    destacarLinha(d.line);
  }
}

// Cartões dos diagnósticos de uma fase, repetidos no painel dela.
function cartoesDaFase(fase) {
  const ctx = contextoDosErros();
  return estado.exemplo.analise.diagnostics.filter((d) => d.phase === fase)
    .map((d) => criarCartaoErro(d, ctx, { aoAbrir: (x) => x.line && destacarLinha(x.line) }));
}

// ---------------------------------------------------------------- trilha de fases

function desenharTrilha() {
  const trilha = $("trilha");
  trilha.replaceChildren();
  FASES.forEach((f, i) => {
    if (i > 0) trilha.append(h("span", { class: "seta", "aria-hidden": "true" }, "→"));
    const selecionada = f.chave === estado.fase;
    trilha.append(h("button", {
      type: "button", role: "tab", id: `aba-${f.ancora}`, "aria-selected": String(selecionada),
      "aria-controls": "painel", tabindex: selecionada ? "0" : "-1", title: `status: ${statusFase(f.chave)}`,
      onclick: () => selecionarFase(f.chave),
    }, h("span", { class: `ponto ${statusFase(f.chave)}`, "aria-hidden": "true" }), f.nome));
  });
}

function selecionarFase(chave) {
  estado.fase = chave;
  const ancora = FASES.find((f) => f.chave === chave).ancora;
  if (location.hash !== "#" + ancora) history.replaceState(null, "", "#" + ancora);
  desenharTrilha();
  desenharPainel();
}

$("trilha").addEventListener("keydown", (evento) => {
  const passo = { ArrowRight: 1, ArrowLeft: -1 }[evento.key];
  if (!passo) return;
  const i = FASES.findIndex((f) => f.chave === estado.fase);
  const proxima = FASES[(i + passo + FASES.length) % FASES.length];
  selecionarFase(proxima.chave);
  $(`aba-${proxima.ancora}`).focus();
});

// ---------------------------------------------------------------- painéis

function caixaPulada(dados) {
  if (dados.reason === "not_requested") {
    return h("div", { class: "caixa pulado" }, h("strong", {}, "Fase não solicitada"),
      h("span", {}, REAL
        ? "A operação analyze não chama o g++. Clique em Compilar e executar para gerar o binário desta compilação e rodá-lo."
        : "A operação analyze não chama o g++. No modo mock não há compilação; o exemplo EXEC-01 mostra o resultado gravado de uma compilação e execução."));
  }
  const falhou = primeiraFaseComErro();
  return h("div", { class: "caixa pulado" }, h("strong", {}, "Fase não executada"),
    h("span", {}, `A fase ${NOME_FASE[falhou] || "anterior"} terminou com erro, então esta não rodou.`));
}

// Listas longas (tokens, linhas de TAC/C++, símbolos) são desenhadas em blocos: o primeiro bloco
// aparece na hora e o resto só quando o usuário pede, para o painel não travar em programas grandes.
const LOTE_LINHAS = 500;

function emBlocos(container, total, criar, nomeItens) {
  let feitos = 0;
  const botao = h("button", { type: "button", class: "mais-blocos" });
  const desenhar = () => {
    const fim = Math.min(total, feitos + LOTE_LINHAS);
    const fragmento = document.createDocumentFragment();
    for (let i = feitos; i < fim; i++) fragmento.append(criar(i));
    container.append(fragmento);
    feitos = fim;
    const faltam = total - feitos;
    botao.hidden = faltam === 0;
    botao.textContent = `Mostrar mais ${Math.min(LOTE_LINHAS, faltam)} ${nomeItens} (faltam ${faltam})`;
  };
  botao.addEventListener("click", desenhar);
  desenhar();
  return botao;
}

function painelTokens(dados) {
  const tokens = dados.tokens;
  const corpo = h("tbody", {
    // Passar o mouse ou clicar num token destaca a linha dele no editor.
    onmouseover: (e) => { const tr = e.target.closest("tr[data-linha]"); if (tr) destacarLinha(+tr.dataset.linha); },
    onclick: (e) => { const tr = e.target.closest("tr[data-linha]"); if (tr) destacarLinha(+tr.dataset.linha); },
  });
  const mais = emBlocos(corpo, tokens.length, (i) => {
    const t = tokens[i];
    return h("tr", { "data-linha": t.line },
      h("td", { class: t.type === "UNKNOWN" ? "desconhecido" : null }, t.type),
      h("td", {}, t.type === "STRING_LITERAL" ? JSON.stringify(t.lexeme) : t.lexeme),
      h("td", {}, t.line), h("td", {}, t.column));
  }, "tokens");
  return [
    dados.status === "error" ? h("div", { class: "caixa erro" }, h("strong", {}, "Erro léxico"),
      h("span", {}, "Os tokens abaixo foram lidos mesmo assim; o token inválido aparece em vermelho.")) : null,
    dados.status === "error" ? h("div", { class: "cartoes-fase" }, cartoesDaFase("lexer")) : null,
    h("p", { class: "estat" }, `${tokens.length} tokens (END_OF_FILE não entra na lista) · passe o mouse num token para ver a linha no código`),
    h("table", { class: "tabela-tokens" },
      h("thead", {}, h("tr", {}, ["tipo", "lexema", "linha", "coluna"].map((c) => h("th", { scope: "col" }, c)))),
      corpo),
    mais,
  ];
}

function painelAst(dados) {
  if (!dados.ast) {
    return [
      h("div", { class: "caixa erro" }, h("strong", {}, "Erro sintático"),
        h("span", {}, "O parser para no primeiro erro e não devolve AST. Veja abaixo onde ele parou e por quê.")),
      h("div", { class: "cartoes-fase" }, cartoesDaFase("parser")),
    ];
  }
  const s = dados.ast_stats;
  // A árvore guarda o que está aberto; criada uma vez por exemplo, sobrevive à troca de aba.
  estado.arvore ??= criarArvoreAst(dados.ast, { aoSelecionar: destacarLinha });
  return [
    h("p", { class: "estat" },
      `${s.emitted} de ${s.nodes} nós · profundidade ${s.depth}${s.truncated ? " · árvore truncada no limite do contrato" : ""}`),
    estado.arvore.elemento,
  ];
}

function rotuloEscopo(e) {
  return e.name ? `${e.kind} ${e.name}` : e.kind;
}

function linhaSimbolo(s) {
  return h("tr", { "data-linha": s.line },
    h("td", {}, s.name), h("td", {}, s.kind), h("td", { class: s.type === null ? "vazio" : null }, s.type ?? "—"),
    h("td", {}, s.line), h("td", { class: s.params.length ? null : "vazio" }, s.params.join(", ") || "—"));
}

// Árvore de escopos com os símbolos de cada um. Com filtro, só aparecem os escopos que têm
// (direta ou indiretamente) símbolos cujo nome contém o texto.
function arvoreEscopos(dados, filtro) {
  const termo = filtro.trim().toLowerCase();
  const filhos = new Map();
  for (const e of dados.scopes) {
    if (!filhos.has(e.parent)) filhos.set(e.parent, []);
    filhos.get(e.parent).push(e);
  }
  const porEscopo = new Map();
  let encontrados = 0;
  for (const s of dados.symbols) {
    if (termo && !s.name.toLowerCase().includes(termo)) continue;
    encontrados++;
    if (!porEscopo.has(s.scope)) porEscopo.set(s.scope, []);
    porEscopo.get(s.scope).push(s);
  }
  const temSimbolos = new Map();
  const conta = (e) => {
    const n = (porEscopo.get(e.id)?.length || 0) + (filhos.get(e.id) || []).reduce((acc, f) => acc + conta(f), 0);
    temSimbolos.set(e.id, n);
    return n;
  };
  (filhos.get(null) || []).forEach(conta);
  const escopo = (e) => {
    const simbolos = porEscopo.get(e.id) || [];
    const visiveis = (filhos.get(e.id) || []).filter((f) => !termo || temSimbolos.get(f.id));
    let tabelaSimbolos = null;
    if (simbolos.length) {
      const corpo = h("tbody", {});
      const mais = emBlocos(corpo, simbolos.length, (i) => linhaSimbolo(simbolos[i]), "símbolos");
      tabelaSimbolos = h("div", { class: "simbolos" },
        h("table", {}, h("thead", {}, h("tr", {}, ["nome", "categoria", "tipo", "linha", "parâmetros"].map((c) => h("th", { scope: "col" }, c)))), corpo),
        mais);
    }
    return h("li", { class: "escopo" },
      h("div", { class: "escopo-cab" }, rotuloEscopo(e), " ", h("small", {}, `${e.id} · linha ${e.line}`)),
      tabelaSimbolos,
      visiveis.length ? h("ul", {}, visiveis.map(escopo)) : null);
  };
  const raizes = (filhos.get(null) || []).filter((e) => !termo || temSimbolos.get(e.id));
  return {
    lista: h("ul", {
      class: "escopos",
      onclick: (ev) => { const tr = ev.target.closest("tr[data-linha]"); if (tr) destacarLinha(+tr.dataset.linha); },
    }, raizes.map(escopo)),
    encontrados,
  };
}

function painelSemantico(dados) {
  const resumo = h("p", { class: "estat" });
  const local = h("div", {});
  const desenhar = () => {
    const { lista, encontrados } = arvoreEscopos(dados, estado.filtroSimbolos);
    resumo.textContent = estado.filtroSimbolos.trim()
      ? `${encontrados} de ${dados.symbols.length} símbolos com “${estado.filtroSimbolos.trim()}” no nome`
      : `${dados.scopes.length} escopos · ${dados.symbols.length} símbolos · clique num símbolo para ver a linha no código`;
    local.replaceChildren(lista);
  };
  const filtro = h("input", {
    type: "search", id: "filtro-simbolos", placeholder: "Filtrar símbolos pelo nome", "aria-label": "Filtrar símbolos pelo nome",
    oninput: (e) => { estado.filtroSimbolos = e.target.value; desenhar(); },
  });
  filtro.value = estado.filtroSimbolos;
  desenhar();
  return [
    dados.status === "error" ? h("div", { class: "caixa erro" }, h("strong", {}, "Erro semântico"),
      h("span", {}, "O semântico percorre o programa inteiro e acumula todos os erros; os escopos e símbolos registrados aparecem depois deles.")) : null,
    dados.status === "error" ? h("div", { class: "cartoes-fase" }, cartoesDaFase("semantic")) : null,
    filtro,
    resumo,
    local,
  ];
}

// Código numerado (TAC, C++, saída), desenhado em blocos de LOTE_LINHAS linhas.
function blocoCodigo(texto) {
  const linhas = texto.endsWith("\n") ? texto.slice(0, -1).split("\n") : texto.split("\n");
  const pre = h("pre", { class: "codigo" });
  const mais = emBlocos(pre, linhas.length, (i) => h("span", {}, linhas[i] || " "), "linhas");
  return mais.hidden ? pre : h("div", { class: "codigo-em-blocos" }, pre, mais);
}

function painelTac(dados) {
  return [h("p", { class: "estat" }, `${dados.lines} linhas`), blocoCodigo(dados.text)];
}

function painelCpp(dados) {
  return [h("p", { class: "estat" }, `${dados.text.split("\n").length - 1} linhas`), blocoCodigo(dados.text)];
}

// Salva um Blob com o nome dado, pelo próprio navegador.
function salvarArquivo(blob, nome) {
  const url = URL.createObjectURL(blob);
  const a = h("a", { href: url, download: nome, hidden: true });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function nomeDoCabecalho(disposicao) {
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposicao || "");
  return m ? decodeURIComponent(m[1]) : null;
}

// GET /api/v1/artifacts/<id>/<kind> do artefato desta compilação (§1.7). Artefato inexistente ou
// expirado (HTTP 404) e id/tipo inválido (HTTP 400) aparecem na linha de andamento.
async function baixarArtefato(id, tipo) {
  try {
    const resposta = await fetch(fonte.urlArtefato(id, tipo), { cache: "no-store" });
    if (!resposta.ok) {
      let corpo = null;
      try { corpo = await resposta.json(); } catch { /* corpo não é JSON */ }
      throw new Error(corpo?.error ? `HTTP ${resposta.status} ${corpo.error.code}: ${corpo.error.message}` : `HTTP ${resposta.status}`);
    }
    const blob = await resposta.blob();
    const nome = nomeDoCabecalho(resposta.headers.get("Content-Disposition")) || `minipar_${id.slice(0, 8)}`;
    salvarArquivo(blob, nome);
    informar(`Baixado ${nome} (${blob.size} bytes), artefato ${tipo} da compilação ${id.slice(0, 8)}.`, "ok");
  } catch (erro) {
    informar(`Falha ao baixar o artefato ${tipo} da compilação ${id.slice(0, 8)}: ${erro.message}`, "erro");
  }
}

function botoesDownload(analise, gpp) {
  const ids = { cpp: analise.artifacts.cpp_id, tac: analise.artifacts.tac_id, binary: analise.artifacts.binary_id };
  return ["cpp", "tac", "binary"].map((tipo) => {
    const rotulo = `Baixar ${tipo === "binary" ? "binário" : "." + tipo}`;
    const id = ids[tipo];
    if (!REAL) return h("button", { type: "button", disabled: true, title: "No modo mock não há artefatos: os downloads vêm do serviço real." }, rotulo);
    if (!id) {
      const motivo = tipo === "binary" && gpp.status !== "ok" ? "O g++ não gerou binário nesta compilação." : "Esta compilação não registrou o artefato.";
      return h("button", { type: "button", disabled: true, title: motivo }, rotulo);
    }
    return h("button", { type: "button", title: `Artefato ${tipo} da compilação ${id}`, onclick: () => baixarArtefato(id, tipo) }, rotulo);
  });
}

// O envelope traz ok; a página confere com os campos que o definem (§1.6): exit_code 0 e sem timeout.
function execucaoBemSucedida(run) {
  return run.exit_code === 0 && run.timed_out === false && !run.error;
}

function caixaResultadoExecucao(run, pedido) {
  if (run.error) {
    return h("div", { class: "caixa erro" }, h("strong", {}, `Execução não realizada: ${run.error.code}`),
      h("span", {}, run.error.code === "ARTIFACT_NOT_FOUND"
        ? `${run.error.message}. O binário desta compilação não está mais disponível; compile de novo.`
        : run.error.message));
  }
  const coerente = run.ok === execucaoBemSucedida(run);
  const aviso = coerente ? null : h("span", {}, `Atenção: o envelope diz ok: ${run.ok}, mas exit_code é ${run.exit_code} e timed_out é ${run.timed_out}.`);
  if (run.timed_out) {
    return h("div", { class: "caixa erro" }, h("strong", {}, "Tempo esgotado"),
      h("span", {}, `O programa passou do tempo limite${pedido ? ` de ${pedido.timeout} s` : ""} e foi encerrado pelo serviço; não há código de saída. A saída abaixo é o que foi produzido até o encerramento.`), aviso);
  }
  if (run.exit_code !== 0) {
    return h("div", { class: "caixa erro" }, h("strong", {}, `O programa terminou com código ${run.exit_code}`),
      h("span", {}, "Código de saída diferente de 0 indica falha durante a execução. Veja stdout e stderr abaixo."), aviso);
  }
  return h("div", { class: run.ok ? "caixa ok" : "caixa erro" }, h("strong", {}, "O programa terminou com código 0"), aviso);
}

// .arm do Teste 11 recortado do stdout desta execução (§1.7), gerado no navegador. Aparece no
// exemplo T11 e em qualquer execução cujo stdout tenha o título do Assembly.
function secaoArm(run) {
  if (estado.exemplo.id !== "T11" && !run.stdout.includes(SUFIXO_TITULO)) return null;
  const mensagem = h("p", { class: "nota", role: "status" });
  const baixar = () => {
    try {
      const { texto, nome } = armDaExecucao(run);
      salvarArquivo(new Blob([new TextEncoder().encode(texto)], { type: "text/plain;charset=utf-8" }), nome);
      mensagem.textContent = "";
      informar(`Baixado ${nome}: ${texto.split("\n").length - 2} linhas de Assembly recortadas do stdout desta execução.`, "ok");
    } catch (erro) {
      mensagem.textContent = `Não foi possível gerar o .arm: ${erro.message}.`;
    }
  };
  return h("section", {}, h("h4", {}, "Assembly ARMv7 (Teste 11)"),
    h("p", { class: "explica" }, "Recorta do stdout, sem alterar nada, as linhas entre o título “Assembly ARMv7 (CPUlator):” e a primeira linha vazia, pelas mesmas regras de tests/2026_2/test11/extrair_arm.py. O arquivo é gerado no navegador."),
    h("div", { class: "acoes" }, h("button", { type: "button", onclick: baixar }, "Baixar .arm")),
    mensagem);
}

function painelExecucao(dados) {
  const analise = estado.exemplo.analise;
  const run = estado.exemplo.execucao;
  const pedido = estado.exemplo.pedidoExecucao;
  const binario = analise.artifacts.binary_id;
  const partes = [
    dados.status === "error" ? h("div", { class: "caixa erro" }, h("strong", {}, "O g++ falhou"),
      h("span", {}, dados.returncode === null
        ? "O compilador C++ não terminou normalmente (tempo esgotado ou compilador ausente). Não há binário desta compilação."
        : `O g++ terminou com código ${dados.returncode}. Não há binário desta compilação; a mensagem do g++ está abaixo.`)) : null,
    dados.status === "error" ? h("div", { class: "cartoes-fase" }, cartoesDaFase("gpp")) : null,
    h("section", {}, h("h4", {}, "g++"), h("dl", {},
      h("dt", {}, "status"), h("dd", {}, dados.status),
      h("dt", {}, "comando"), h("dd", {}, dados.command.join(" ")),
      h("dt", {}, "código de retorno"), h("dd", {}, dados.returncode ?? "— (não terminou)"),
      h("dt", {}, "duração"), h("dd", {}, `${dados.duration_ms} ms`),
      h("dt", {}, "compilação"), h("dd", {}, analise.request_id),
      h("dt", {}, "binário"), h("dd", {}, binario ?? "nenhum"))),
    dados.stdout ? [h("h4", {}, "Saída do g++ (stdout)"), blocoCodigo(dados.stdout)] : null,
    dados.stderr ? [h("h4", {}, "Mensagens do g++ (stderr)"), blocoCodigo(dados.stderr),
      dados.stderr_truncated ? h("p", { class: "nota" }, "stderr do g++ truncado no limite de 64 KB.") : null] : null,
    h("div", { class: "acoes" }, botoesDownload(analise, dados)),
  ];
  if (REAL && binario) {
    partes.push(h("div", { class: "acoes" }, h("button", {
      type: "button", disabled: Boolean(estado.ocupado), onclick: executarDeNovo,
      title: `Executa de novo o binário ${binario.slice(0, 8)} com a entrada e o tempo limite atuais, sem recompilar`,
    }, estado.ocupado === "executar" ? "Executando…" : "Executar de novo com a entrada atual")));
  }
  if (run) {
    const entrada = pedido ? pedido.stdin : estado.exemplo.entrada;
    partes.push(h("section", {}, h("h4", {}, "Execução"), caixaResultadoExecucao(run, pedido),
      run.error ? null : h("dl", {},
        h("dt", {}, "binário"), h("dd", {}, run.artifact_id),
        h("dt", {}, "entrada (stdin)"), h("dd", {}, entrada ? JSON.stringify(entrada) : "(vazia)"),
        h("dt", {}, "tempo limite"), h("dd", {}, pedido ? `${pedido.timeout} s` : "—"),
        h("dt", {}, "código de saída"), h("dd", {}, run.exit_code ?? "— (sem código)"),
        h("dt", {}, "tempo esgotado"), h("dd", {}, run.timed_out ? "sim" : "não"),
        h("dt", {}, "duração"), h("dd", {}, `${run.duration_ms} ms`))));
    if (!run.error) {
      partes.push(h("section", {}, h("h4", {}, "Saída (stdout)"), blocoCodigo(run.stdout || "\n"),
        run.stdout_truncated ? h("p", { class: "nota" }, "stdout truncado no limite de 1 MB.") : null));
      if (run.stderr || run.stderr_truncated) {
        partes.push(h("section", {}, h("h4", {}, "Erros (stderr)"), blocoCodigo(run.stderr || "\n"),
          run.stderr_truncated ? h("p", { class: "nota" }, "stderr truncado no limite de 1 MB.") : null));
      }
      partes.push(secaoArm(run));
    }
  }
  return h("div", { class: "execucao" }, partes.flat());
}

const PAINEIS = { lexer: painelTokens, parser: painelAst, semantic: painelSemantico, tac: painelTac, cpp: painelCpp, gpp: painelExecucao };

// Campo sem o qual o painel da fase não tem o que desenhar. O parser sem AST já tem painel próprio.
const PAYLOAD = { lexer: "tokens", semantic: "scopes", tac: "text", cpp: "text", gpp: "command" };

// Fase com erro que não trouxe resultado parcial (§1.3). Mostra os diagnósticos da fase e os
// internos; sem nenhum, uma falha genérica, sem inventar mensagem (handoff do CORE-08).
function painelErroSemResultado(chave) {
  const ctx = contextoDosErros();
  const cartoes = estado.exemplo.analise.diagnostics.filter((d) => d.phase === chave || d.phase === "internal")
    .map((d) => criarCartaoErro(d, ctx, { aoAbrir: (x) => x.line && destacarLinha(x.line) }));
  return [
    h("div", { class: "caixa erro" }, h("strong", {}, `A fase ${NOME_FASE[chave]} terminou com erro`),
      h("span", {}, cartoes.length
        ? "O serviço não devolveu resultado parcial desta fase. O diagnóstico abaixo explica o motivo."
        : "O serviço não devolveu resultado nem diagnóstico para esta fase, então não há detalhe a mostrar.")),
    cartoes.length ? h("div", { class: "cartoes-fase" }, cartoes) : null,
  ];
}

function desenharPainel() {
  const painel = $("painel");
  const f = FASES.find((x) => x.chave === estado.fase);
  painel.setAttribute("aria-labelledby", `aba-${f.ancora}`);
  painel.replaceChildren(h("h3", {}, f.nome), h("p", { class: "explica" }, EXPLICA[f.chave]));
  destacarLinha(null);
  if (!estado.exemplo.analise) {
    painel.append(h("div", { class: "caixa descartado" }, h("strong", {}, "Sem análise"),
      h("span", {}, estado.ocupado ? "Aguardando o serviço real…" : "Clique em Analisar para enviar o código ao compilador.")));
    return;
  }
  if (estado.descartada) {
    painel.append(h("div", { class: "caixa descartado" }, h("strong", {}, "Resposta descartada"),
      h("span", {}, REAL
        ? "O código no editor não é mais o que foi analisado (o source_hash mudou). Clique em Analisar (Ctrl+Enter) ou em Compilar e executar para processar o código atual."
        : "O código no editor não é mais o que foi analisado (o source_hash mudou). No modo mock não há reanálise: restaure o código do exemplo.")));
    return;
  }
  const dados = dadosFase(f.chave);
  if (dados.status === "skipped") painel.append(caixaPulada(dados));
  else if (dados.status === "error" && PAYLOAD[f.chave] && dados[PAYLOAD[f.chave]] === undefined) painel.append(...painelErroSemResultado(f.chave).filter(Boolean));
  else painel.append(...[PAINEIS[f.chave](dados)].flat().filter(Boolean));
  painel.scrollTop = 0;
  if (f.chave === "parser" && dados.ast) estado.arvore.anunciar(); // reaplica a linha do nó selecionado
  else {
    const erro = estado.exemplo.analise.diagnostics.find((d) => d.phase === f.chave && d.line);
    if (erro) destacarLinha(erro.line);
  }
}

// ---------------------------------------------------------------- rodapé e exemplo

function desenharRodape() {
  const a = estado.exemplo.analise;
  const item = (rotulo, valor) => h("span", {}, `${rotulo} `, h("b", {}, valor));
  const itens = [item("fonte", fonte.modo), item("exemplo", estado.exemplo.id)];
  if (a) {
    itens.push(
      item("operação", a.operation),
      item("ok", estado.descartada ? "descartado" : String(a.ok)),
      item("request_id", a.request_id),
      item("source_hash", a.source_hash.slice(0, 19) + "…"),
      item("duração", `${a.duration_ms} ms`),
    );
  }
  $("rodape").replaceChildren(...itens);
}

function atualizarAcoes() {
  // Restaurar: no mock, só quando a resposta foi descartada; no real, sempre que o editor difere do exemplo.
  $("restaurar").hidden = REAL ? $("codigo").value === estado.exemplo?.codigo : !estado.descartada;
  const analisar = $("analisar");
  analisar.disabled = !fonte.analisar || Boolean(estado.ocupado) || !estado.exemplo;
  analisar.textContent = estado.ocupado === "analisar" ? "Analisando…" : "Analisar";
  const compilar = $("compilar");
  compilar.disabled = !fonte.compilar || Boolean(estado.ocupado) || !estado.exemplo;
  compilar.textContent = { compilar: "Compilando…", executar: "Executando…" }[estado.ocupado] || "Compilar e executar";
}

function informar(texto, tipo = "") {
  const linha = $("situacao");
  linha.textContent = texto;
  linha.className = `situacao ${tipo}`.trim();
}

function desenharTudo() {
  atualizarAcoes();
  desenharTrilha();
  desenharPainel();
  desenharDiagnosticos();
  desenharRodape();
}

// Cada análise e cada troca de exemplo recebe um número; uma resposta que chega depois de outra
// análise ou de outro exemplo ter começado é ignorada.
let sequencia = 0;

// Envia o código atual do editor ao serviço real. A resposta só é aplicada se o source_hash dela
// for o hash do código que está no editor quando ela chega (C-WEB-v1 §1.3); senão é descartada.
// true se a resposta é do código que está no editor agora; false se o código mudou (a resposta é
// descartada); null se outra ação começou enquanto o hash era calculado.
async function confereHash(resposta, enviado, minha) {
  const atual = $("codigo").value;
  const hashAtual = await sha256(atual);
  if (minha !== sequencia) return null;
  return hashAtual === null ? atual === enviado : resposta.source_hash === hashAtual;
}

function aplicarEnvelope(resposta, enviado) {
  estado.exemplo.analise = resposta;
  estado.exemplo.codigoAnalisado = enviado;
  estado.exemplo.execucao = null;
  estado.exemplo.pedidoExecucao = null;
  estado.descartada = false;
  estado.arvore = null;
}

function falhaDeConexao(acao, erro) {
  informar(`Falha ao ${acao}: ${erro.message} Inicie o servidor com web_didatica/server.py (veja web_didatica/README.md) ou abra com ?fonte=mock.`, "erro");
}

async function analisarCodigo() {
  if (!fonte.analisar || estado.ocupado) return;
  const minha = ++sequencia;
  const enviado = $("codigo").value;
  estado.ocupado = "analisar";
  atualizarAcoes();
  if (!estado.exemplo.analise) desenharPainel();
  informar("Analisando no serviço real…");
  try {
    const resposta = await fonte.analisar(enviado);
    if (minha !== sequencia) return;
    const confere = await confereHash(resposta, enviado, minha);
    if (confere === null) return;
    if (!confere) {
      informar(`Resposta ${resposta.request_id.slice(0, 8)} descartada: o código mudou durante a análise (source_hash diferente). Clique em Analisar de novo.`, "aviso");
      return;
    }
    aplicarEnvelope(resposta, enviado);
    const erros = resposta.diagnostics.filter((d) => d.severity === "error").length;
    informar(resposta.ok
      ? `Análise concluída em ${resposta.duration_ms} ms, sem erros.`
      : `Análise concluída em ${resposta.duration_ms} ms com ${erros} erro(s).`, resposta.ok ? "ok" : "erro");
  } catch (erro) {
    if (minha !== sequencia) return;
    falhaDeConexao("analisar", erro);
  } finally {
    if (minha === sequencia) {
      estado.ocupado = null;
      desenharTudo();
    }
  }
}

// Entrada e tempo limite da execução, conferidos antes de enviar (o servidor também confere, §1.8).
function lerPedidoExecucao() {
  const campo = $("tempo-limite");
  const timeout = Number(campo.value);
  if (campo.value.trim() === "" || !Number.isInteger(timeout) || timeout < 1 || timeout > 30) {
    informar("Tempo limite inválido: use um número inteiro de 1 a 30 segundos (C-WEB-v1 §1.6).", "erro");
    campo.focus();
    return null;
  }
  return { stdin: $("entrada").value, timeout };
}

function resumoExecucao(run, pedido) {
  if (run.error) return [`Execução não realizada: ${run.error.code} (${run.error.message}).`, "erro"];
  if (run.timed_out) return [`Tempo esgotado: o programa passou de ${pedido.timeout} s e foi encerrado.`, "erro"];
  if (run.exit_code !== 0) return [`O programa terminou com código ${run.exit_code} em ${run.duration_ms} ms.`, "erro"];
  return [`Executado em ${run.duration_ms} ms, código de saída 0.`, run.ok && execucaoBemSucedida(run) ? "ok" : "erro"];
}

// Executa o binário da compilação exibida (artifacts.binary_id desta aba) e guarda o resultado
// se a compilação exibida ainda for a mesma quando a resposta chegar.
async function executarBinario(analise, pedido, minha) {
  estado.ocupado = "executar";
  atualizarAcoes();
  if (estado.fase === "gpp") desenharPainel();
  informar(`Executando o binário ${analise.artifacts.binary_id.slice(0, 8)} (tempo limite ${pedido.timeout} s)…`);
  const run = await fonte.executar(analise.artifacts.binary_id, pedido.stdin, pedido.timeout);
  if (minha !== sequencia || estado.exemplo.analise !== analise) return;
  estado.exemplo.execucao = run;
  estado.exemplo.pedidoExecucao = pedido;
  informar(...resumoExecucao(run, pedido));
}

async function compilarExecutar() {
  if (!fonte.compilar || estado.ocupado) return;
  const pedido = lerPedidoExecucao();
  if (!pedido) return;
  const minha = ++sequencia;
  const enviado = $("codigo").value;
  estado.ocupado = "compilar";
  atualizarAcoes();
  informar("Compilando no serviço real (Lexer até g++)…");
  try {
    const resposta = await fonte.compilar(enviado);
    if (minha !== sequencia) return;
    const confere = await confereHash(resposta, enviado, minha);
    if (confere === null) return;
    if (!confere) {
      informar(`Compilação ${resposta.request_id.slice(0, 8)} descartada: o código mudou enquanto compilava (source_hash diferente). Nada foi executado.`, "aviso");
      return;
    }
    aplicarEnvelope(resposta, enviado);
    const falhou = FASES.find((f) => resposta.phases[f.chave].status === "error");
    estado.fase = falhou ? falhou.chave : "gpp";
    history.replaceState(null, "", "#" + FASES.find((f) => f.chave === estado.fase).ancora);
    if (!resposta.ok || !resposta.artifacts.binary_id) {
      informar(`Compilação ${resposta.request_id.slice(0, 8)} falhou na fase ${NOME_FASE[falhou?.chave ?? "gpp"]} em ${resposta.duration_ms} ms; nada foi executado.`, "erro");
      return;
    }
    desenharTudo();
    await executarBinario(resposta, pedido, minha);
  } catch (erro) {
    if (minha !== sequencia) return;
    falhaDeConexao(estado.ocupado === "executar" ? "executar" : "compilar", erro);
  } finally {
    if (minha === sequencia) {
      estado.ocupado = null;
      desenharTudo();
    }
  }
}

// Executa de novo o binário exibido, com a entrada e o tempo limite atuais, sem recompilar.
async function executarDeNovo() {
  const analise = estado.exemplo?.analise;
  if (!fonte.executar || estado.ocupado || !analise?.artifacts.binary_id || estado.descartada) return;
  const pedido = lerPedidoExecucao();
  if (!pedido) return;
  const minha = ++sequencia;
  try {
    await executarBinario(analise, pedido, minha);
  } catch (erro) {
    if (minha !== sequencia) return;
    falhaDeConexao("executar", erro);
  } finally {
    if (minha === sequencia) {
      estado.ocupado = null;
      desenharTudo();
    }
  }
}

async function abrirExemplo(arquivo) {
  const minha = ++sequencia;
  const exemplo = await fonte.carregarExemplo(arquivo);
  if (minha !== sequencia) return;
  estado.exemplo = exemplo;
  estado.exemplo.codigoAnalisado = exemplo.codigo;
  estado.descartada = false;
  estado.ocupado = null;
  estado.arvore = null;
  estado.filtroSimbolos = "";
  $("codigo").value = estado.exemplo.codigo;
  $("entrada").value = estado.exemplo.entrada;
  prepararCasosT11();
  $("aviso-mock").title = estado.exemplo.notas.join("\n");
  atualizarNumeros();
  informar("");
  desenharTudo();
  if (REAL) await analisarCodigo();
}

$("codigo").addEventListener("input", async () => {
  atualizarNumeros();
  atualizarAcoes();
  if (!estado.exemplo?.analise) return;
  const atual = $("codigo").value;
  const hash = await sha256(atual);
  if ($("codigo").value !== atual || !estado.exemplo.analise) return; // outra digitação já chegou
  const descartada = hash === null ? atual !== estado.exemplo.codigoAnalisado : hash !== estado.exemplo.analise.source_hash;
  if (descartada !== estado.descartada) {
    estado.descartada = descartada;
    desenharTudo();
  }
});
$("codigo").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    analisarCodigo();
  }
});
$("codigo").addEventListener("scroll", () => {
  $("numeros").scrollTop = $("codigo").scrollTop;
  posicionarDestaque();
});
$("restaurar").addEventListener("click", () => {
  $("codigo").value = estado.exemplo.codigo;
  $("codigo").dispatchEvent(new Event("input"));
});
$("analisar").addEventListener("click", analisarCodigo);
$("compilar").addEventListener("click", compilarExecutar);

// Atalhos para a entrada dos três casos do Teste 11, só no exemplo T11.
function prepararCasosT11() {
  const local = $("casos-t11");
  local.hidden = estado.exemplo.id !== "T11";
  local.replaceChildren("Entrada do Teste 11:", ...CASOS_T11.map(([nome, expressao]) => h("button", {
    type: "button", title: expressao, onclick: () => { $("entrada").value = expressao + "\n"; },
  }, nome)));
}
$("fixture").addEventListener("change", (e) => abrirExemplo(e.target.value).catch(mostrarFalha));

function mostrarFalha(erro) {
  $("painel").replaceChildren(h("div", { class: "caixa erro" }, h("strong", {}, "Falha ao carregar os exemplos"),
    h("span", {}, `${erro.message} Sirva a pasta web_didatica por HTTP (veja web_didatica/README.md); abrir o arquivo direto no navegador não funciona.`)));
}

function prepararModo() {
  const aviso = $("aviso-mock");
  if (REAL) {
    aviso.textContent = "SERVIÇO REAL · src/service.py via /api/v1 (analyze, compile, execute, artifacts)";
    aviso.classList.add("real");
    $("analisar").title = "Envia o código do editor ao compilador real (Ctrl+Enter)";
    $("compilar").title = "Compila o código do editor com o g++ e executa o binário desta compilação com a entrada abaixo";
  } else {
    $("analisar").title = "Indisponível no modo mock: abra sem ?fonte=mock, com o servidor web_didatica/server.py";
    $("compilar").title = "Indisponível no modo mock: abra sem ?fonte=mock, com o servidor web_didatica/server.py";
    // No mock a entrada mostra o stdin gravado na fixture, sem execução.
    $("entrada").readOnly = true;
    $("tempo-limite").disabled = true;
  }
}

async function iniciar() {
  prepararModo();
  estado.exemplos = await fonte.listarExemplos();
  $("fixture").replaceChildren(...estado.exemplos.map((e) => h("option", { value: e.file }, `${e.fixture} · ${e.title}`)));
  const inicial = FASES.find((f) => "#" + f.ancora === location.hash);
  if (inicial) estado.fase = inicial.chave;
  await abrirExemplo(estado.exemplos[0].file);
}

iniciar().catch(mostrarFalha);
