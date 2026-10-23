// Web didática — wireframe navegável (WEB-01). Desenha as fases a partir do envelope C-WEB-v1.
import * as fonte from "./fonte_mock.js";

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
  gpp: "Compila o C++ com o g++ e executa o binário desta compilação.",
};

const $ = (id) => document.getElementById(id);
const estado = { exemplos: [], exemplo: null, fase: "lexer", descartada: false };

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
  if (estado.descartada) return "stale";
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
  const diagnosticos = estado.exemplo.analise.diagnostics;
  if (!diagnosticos.length) {
    lista.append(h("li", { class: "diag-vazio" }, "Nenhum diagnóstico."));
    return;
  }
  for (const d of diagnosticos) {
    const onde = [d.line ? `linha ${d.line}` : null, d.column ? `coluna ${d.column}` : null].filter(Boolean).join(", ");
    lista.append(h("li", { class: d.severity === "warning" ? "diag-aviso" : "diag-erro" },
      h("button", {
        type: "button",
        onclick: () => {
          if (NOME_FASE[d.phase] && d.phase !== "internal") selecionarFase(d.phase);
          if (d.line) selecionarLinha(d.line);
        },
      },
        h("span", { class: "diag-codigo" }, `${d.code} · ${NOME_FASE[d.phase] || d.phase}${onde ? " · " + onde : ""}`),
        h("span", {}, d.message))));
  }
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
      h("span", {}, "A operação analyze não chama o g++. Compilar e executar entram com o serviço real (WEB-04); o exemplo EXEC-01 mostra como fica."));
  }
  const falhou = primeiraFaseComErro();
  return h("div", { class: "caixa pulado" }, h("strong", {}, "Fase não executada"),
    h("span", {}, `A fase ${NOME_FASE[falhou] || "anterior"} terminou com erro, então esta não rodou.`));
}

function tabela(colunas, linhas) {
  return h("table", {},
    h("thead", {}, h("tr", {}, colunas.map((c) => h("th", { scope: "col" }, c)))),
    h("tbody", {}, linhas));
}

function painelTokens(dados) {
  const linhas = dados.tokens.map((t) => h("tr", {},
    h("td", { class: t.type === "UNKNOWN" ? "desconhecido" : null }, t.type),
    h("td", {}, t.type === "STRING_LITERAL" ? JSON.stringify(t.lexeme) : t.lexeme),
    h("td", {}, t.line), h("td", {}, t.column)));
  return [
    dados.status === "error" ? h("div", { class: "caixa erro" }, h("strong", {}, "Erro léxico"),
      h("span", {}, "Os tokens abaixo foram lidos mesmo assim; o token inválido aparece em vermelho.")) : null,
    h("p", { class: "estat" }, `${dados.tokens.length} tokens (END_OF_FILE não entra na lista)`),
    tabela(["tipo", "lexema", "linha", "coluna"], linhas),
  ];
}

function noAst(no) {
  const atributos = Object.entries(no.attributes)
    .filter(([, v]) => v !== null && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => `${k}=${Array.isArray(v) ? "[" + v.join(", ") + "]" : JSON.stringify(v)}`);
  const papel = no.role === null ? null : no.index === null ? no.role : `${no.role}[${no.index}]`;
  return h("li", {},
    h("span", { class: `no${no.kind === "Truncated" ? " no-truncado" : ""}` },
      h("span", { class: "no-rotulo", title: no.kind }, no.label),
      papel ? h("span", { class: "no-papel" }, papel) : null,
      atributos.length && no.kind !== "Truncated" ? h("span", { class: "no-attr" }, atributos.join(" ")) : null,
      h("span", { class: "no-linha" }, `L${no.line}`)),
    no.children.length ? h("ul", {}, no.children.map(noAst)) : null);
}

function painelAst(dados) {
  if (!dados.ast) {
    return h("div", { class: "caixa erro" }, h("strong", {}, "Erro sintático"),
      h("span", {}, "O parser para no primeiro erro e não devolve AST. O diagnóstico ao lado mostra onde."));
  }
  const s = dados.ast_stats;
  return [
    h("p", { class: "estat" },
      `${s.emitted} de ${s.nodes} nós · profundidade ${s.depth}${s.truncated ? " · árvore truncada" : ""}`),
    h("ul", { class: "arvore" }, noAst(dados.ast)),
  ];
}

function rotuloEscopo(e) {
  return e.name ? `${e.kind} ${e.name}` : e.kind;
}

function painelSemantico(dados) {
  const filhos = new Map();
  for (const e of dados.scopes) {
    if (!filhos.has(e.parent)) filhos.set(e.parent, []);
    filhos.get(e.parent).push(e);
  }
  const porEscopo = new Map();
  for (const s of dados.symbols) {
    if (!porEscopo.has(s.scope)) porEscopo.set(s.scope, []);
    porEscopo.get(s.scope).push(s);
  }
  const escopo = (e) => {
    const simbolos = porEscopo.get(e.id) || [];
    return h("li", { class: "escopo" },
      h("div", { class: "escopo-cab" }, rotuloEscopo(e), " ", h("small", {}, `${e.id} · linha ${e.line}`)),
      simbolos.length ? h("div", { class: "simbolos" }, tabela(["nome", "categoria", "tipo", "linha", "parâmetros"],
        simbolos.map((s) => h("tr", {},
          h("td", {}, s.name), h("td", {}, s.kind), h("td", { class: s.type === null ? "vazio" : null }, s.type ?? "—"),
          h("td", {}, s.line), h("td", { class: s.params.length ? null : "vazio" }, s.params.join(", ") || "—"))))) : null,
      filhos.has(e.id) ? h("ul", {}, filhos.get(e.id).map(escopo)) : null);
  };
  return [
    dados.status === "error" ? h("div", { class: "caixa erro" }, h("strong", {}, "Erro semântico"),
      h("span", {}, "O semântico percorre o programa inteiro; abaixo está tudo o que foi registrado até o fim.")) : null,
    h("p", { class: "estat" }, `${dados.scopes.length} escopos · ${dados.symbols.length} símbolos`),
    h("ul", { class: "escopos" }, (filhos.get(null) || []).map(escopo)),
  ];
}

function blocoCodigo(texto) {
  const linhas = texto.endsWith("\n") ? texto.slice(0, -1).split("\n") : texto.split("\n");
  return h("pre", { class: "codigo" }, linhas.map((l) => h("span", {}, l || " ")));
}

function painelTac(dados) {
  return [h("p", { class: "estat" }, `${dados.lines} linhas`), blocoCodigo(dados.text)];
}

function painelCpp(dados) {
  return [h("p", { class: "estat" }, `${dados.text.split("\n").length - 1} linhas`), blocoCodigo(dados.text)];
}

function painelExecucao(dados) {
  const analise = estado.exemplo.analise;
  const run = estado.exemplo.execucao;
  const baixar = ["cpp", "tac", "binary"].map((tipo) => h("button", {
    type: "button", disabled: true, title: "Download pelo serviço real (WEB-04)",
  }, `Baixar ${tipo === "binary" ? "binário" : "." + tipo}`));
  const partes = [
    h("section", {}, h("h3", {}, "g++"), h("dl", {},
      h("dt", {}, "status"), h("dd", {}, dados.status),
      h("dt", {}, "comando"), h("dd", {}, dados.command.join(" ")),
      h("dt", {}, "código de saída"), h("dd", {}, dados.returncode),
      h("dt", {}, "duração"), h("dd", {}, `${dados.duration_ms} ms`),
      h("dt", {}, "artefatos"), h("dd", {}, analise.artifacts.binary_id ?? "nenhum"))),
    dados.stderr ? blocoCodigo(dados.stderr) : null,
    h("div", { class: "acoes" }, baixar),
  ];
  if (run) {
    partes.push(h("section", {}, h("h3", {}, "Execução"), h("dl", {},
      h("dt", {}, "entrada (stdin)"), h("dd", {}, estado.exemplo.entrada ? JSON.stringify(estado.exemplo.entrada) : "(vazia)"),
      h("dt", {}, "código de saída"), h("dd", {}, run.exit_code ?? "—"),
      h("dt", {}, "tempo esgotado"), h("dd", {}, run.timed_out ? "sim" : "não"),
      h("dt", {}, "duração"), h("dd", {}, `${run.duration_ms} ms`))),
    h("h3", {}, "Saída (stdout)"), blocoCodigo(run.stdout || "\n"));
    if (run.stderr) partes.push(h("h3", {}, "Erros (stderr)"), blocoCodigo(run.stderr));
  }
  return h("div", { class: "execucao" }, partes);
}

const PAINEIS = { lexer: painelTokens, parser: painelAst, semantic: painelSemantico, tac: painelTac, cpp: painelCpp, gpp: painelExecucao };

function desenharPainel() {
  const painel = $("painel");
  const f = FASES.find((x) => x.chave === estado.fase);
  painel.setAttribute("aria-labelledby", `aba-${f.ancora}`);
  painel.replaceChildren(h("h3", {}, f.nome), h("p", { class: "explica" }, EXPLICA[f.chave]));
  if (estado.descartada) {
    painel.append(h("div", { class: "caixa descartado" }, h("strong", {}, "Resposta descartada"),
      h("span", {}, "O código no editor não é mais o que foi analisado (o source_hash mudou). No modo mock não há reanálise: restaure o código do exemplo ou, na integração, use Analisar.")));
    return;
  }
  const dados = dadosFase(f.chave);
  if (dados.status === "skipped") painel.append(caixaPulada(dados));
  else painel.append(...[PAINEIS[f.chave](dados)].flat().filter(Boolean));
  painel.scrollTop = 0;
}

// ---------------------------------------------------------------- rodapé e exemplo

function desenharRodape() {
  const a = estado.exemplo.analise;
  const item = (rotulo, valor) => h("span", {}, `${rotulo} `, h("b", {}, valor));
  $("rodape").replaceChildren(
    item("fonte", fonte.modo),
    item("exemplo", estado.exemplo.id),
    item("operação", a.operation),
    item("ok", estado.descartada ? "descartado" : String(a.ok)),
    item("request_id", a.request_id),
    item("source_hash", a.source_hash.slice(0, 19) + "…"),
  );
}

function desenharTudo() {
  $("restaurar").hidden = !estado.descartada;
  desenharTrilha();
  desenharPainel();
  desenharDiagnosticos();
  desenharRodape();
}

async function abrirExemplo(arquivo) {
  estado.exemplo = await fonte.carregarExemplo(arquivo);
  estado.descartada = false;
  $("codigo").value = estado.exemplo.codigo;
  $("aviso-mock").title = estado.exemplo.notas.join("\n");
  atualizarNumeros();
  desenharTudo();
}

$("codigo").addEventListener("input", async () => {
  atualizarNumeros();
  const atual = $("codigo").value;
  const hash = await sha256(atual);
  if ($("codigo").value !== atual) return; // outra digitação já chegou
  const descartada = hash === null ? atual !== estado.exemplo.codigo : hash !== estado.exemplo.analise.source_hash;
  if (descartada !== estado.descartada) {
    estado.descartada = descartada;
    desenharTudo();
  }
});
$("codigo").addEventListener("scroll", () => { $("numeros").scrollTop = $("codigo").scrollTop; });
$("restaurar").addEventListener("click", () => {
  $("codigo").value = estado.exemplo.codigo;
  $("codigo").dispatchEvent(new Event("input"));
});
$("fixture").addEventListener("change", (e) => abrirExemplo(e.target.value).catch(mostrarFalha));

function mostrarFalha(erro) {
  $("painel").replaceChildren(h("div", { class: "caixa erro" }, h("strong", {}, "Falha ao carregar os exemplos"),
    h("span", {}, `${erro.message} Sirva a pasta web_didatica por HTTP (veja web_didatica/README.md); abrir o arquivo direto no navegador não funciona.`)));
}

async function iniciar() {
  estado.exemplos = await fonte.listarExemplos();
  $("fixture").replaceChildren(...estado.exemplos.map((e) => h("option", { value: e.file }, `${e.fixture} · ${e.title}`)));
  const inicial = FASES.find((f) => "#" + f.ancora === location.hash);
  if (inicial) estado.fase = inicial.chave;
  await abrirExemplo(estado.exemplos[0].file);
}

iniciar().catch(mostrarFalha);
