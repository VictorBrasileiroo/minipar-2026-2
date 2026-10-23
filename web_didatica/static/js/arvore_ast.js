// AST recolhível (WEB-02). Os filhos de um nó só viram DOM quando ele é aberto, então uma AST
// de 5000 nós abre desenhando poucas dezenas. Teclado no padrão de árvore do WAI-ARIA.
const NIVEL_ABERTO_INICIAL = 2; // raiz e filhos abertos: o usuário vê três níveis
const LOTE = 200; // filhos desenhados por vez em nós muito largos (ex.: Program com mil declarações)

function formatarAtributos(dado) {
  if (dado.kind === "Truncated") return "";
  return Object.entries(dado.attributes)
    .filter(([, v]) => v !== null && !(Array.isArray(v) && !v.length))
    .map(([k, v]) => `${k}=${Array.isArray(v) ? "[" + v.join(", ") + "]" : JSON.stringify(v)}`)
    .join(" ");
}

function span(classe, texto) {
  const el = document.createElement("span");
  el.className = classe;
  el.textContent = texto;
  return el;
}

// Monta o modelo sem recursão: a AST pode ter até 200 níveis (§1.4).
function preparar(raiz) {
  const nos = [];
  const porId = new Map();
  const pilha = [{ dado: raiz, pai: null, nivel: 1 }];
  while (pilha.length) {
    const { dado, pai, nivel } = pilha.pop();
    const no = { dado, pai, nivel, filhos: [], descendentes: 0, aberto: nivel <= NIVEL_ABERTO_INICIAL, li: null,
                 mostrar: LOTE, mais: null };
    nos.push(no);
    porId.set(dado.id, no);
    if (pai) pai.filhos.push(no);
    for (let i = dado.children.length - 1; i >= 0; i--) pilha.push({ dado: dado.children[i], pai: no, nivel: nivel + 1 });
  }
  for (let i = nos.length - 1; i > 0; i--) nos[i].pai.descendentes += 1 + nos[i].descendentes;
  return { nos, porId };
}

// O parser atual não grava `line` em SeqBlock/ParBlock (fica 1); a Web não aponta linha errada.
const LINHA_NAO_CONFIAVEL = new Set(["SeqBlock", "ParBlock"]);
const CAMINHO_MAX = 6; // ancestrais mostrados antes de abreviar com "…"

const EXPLICA_TRUNCADO = {
  max_nodes: (n) => `A AST foi enviada só até o limite de 5000 nós do contrato. ${n} nós desta parte da árvore ficaram de fora.`,
  max_depth: (n) => `Esta subárvore passava do limite de 200 níveis do contrato. ${n} nós ficaram de fora.`,
};

// aoSelecionar(linha | null): chamado a cada seleção, com a linha do nó quando ela é confiável.
export function criarArvoreAst(raiz, { aoSelecionar = () => {} } = {}) {
  const { nos, porId } = preparar(raiz);
  const primeiro = nos[0];
  let selecionado = primeiro;

  const lista = document.createElement("ul");
  lista.className = "arvore";
  lista.setAttribute("role", "tree");
  lista.setAttribute("aria-label", "Árvore sintática abstrata");
  lista.tabIndex = 0;

  const contagem = span("estat arvore-contagem", "");
  const barra = document.createElement("div");
  barra.className = "arvore-barra";
  for (const [rotulo, acao] of [["Expandir tudo", () => definirAbertos(() => true)],
                                ["Recolher tudo", () => definirAbertos((no) => no === primeiro)],
                                ["Primeiros níveis", () => definirAbertos((no) => no.nivel <= NIVEL_ABERTO_INICIAL)]]) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.textContent = rotulo;
    botao.addEventListener("click", acao);
    barra.append(botao);
  }
  barra.append(contagem);

  const detalhes = document.createElement("aside");
  detalhes.className = "ast-detalhes";
  detalhes.setAttribute("aria-label", "Detalhes do nó selecionado");

  const corpo = document.createElement("div");
  corpo.className = "ast-corpo";
  corpo.append(lista, detalhes);

  const elemento = document.createElement("div");
  elemento.className = "arvore-ast";
  elemento.append(barra, corpo);

  // ------------------------------------------------------------ detalhes do nó

  function linhaConfiavel(no) {
    return !no.ehMais && !LINHA_NAO_CONFIAVEL.has(no.dado.kind);
  }

  function par(dl, rotulo, valor) {
    const dt = document.createElement("dt");
    dt.textContent = rotulo;
    const dd = document.createElement("dd");
    if (valor instanceof Node) dd.append(valor);
    else dd.textContent = valor;
    dl.append(dt, dd);
  }

  function caminhoAte(no) {
    const ancestrais = [];
    for (let p = no.pai; p; p = p.pai) ancestrais.unshift(p);
    const nav = document.createElement("nav");
    nav.className = "ast-caminho";
    nav.setAttribute("aria-label", "Caminho até a raiz");
    const mostrados = ancestrais.length > CAMINHO_MAX ? [ancestrais[0], null, ...ancestrais.slice(-(CAMINHO_MAX - 1))] : ancestrais;
    for (const anc of mostrados) {
      if (anc === null) {
        nav.append(span("ast-caminho-sep", "… ›"));
        continue;
      }
      const botao = document.createElement("button");
      botao.type = "button";
      botao.textContent = anc.dado.label;
      botao.addEventListener("click", () => {
        selecionar(anc);
        lista.focus({ preventScroll: true });
      });
      nav.append(botao, span("ast-caminho-sep", "›"));
    }
    nav.append(span("ast-caminho-atual", no.ehMais ? "mais filhos" : no.dado.label));
    return nav;
  }

  function desenharDetalhes(no) {
    const titulo = document.createElement("h4");
    const dl = document.createElement("dl");
    if (no.ehMais) {
      titulo.textContent = "Mais filhos";
      par(dl, "nó pai", no.pai.dado.label);
      par(dl, "ainda ocultos", `${partes(no.pai).restantes} filhos`);
      detalhes.replaceChildren(titulo, dl, caminhoAte(no));
      return;
    }
    const { dado } = no;
    titulo.textContent = dado.label;
    par(dl, "tipo", dado.kind);
    par(dl, "papel no pai", dado.role === null ? "raiz" : dado.index === null ? dado.role : `${dado.role}[${dado.index}]`);
    par(dl, "linha", linhaConfiavel(no) ? String(dado.line) : `${dado.line} (não confiável)`);
    par(dl, "nível", String(no.nivel));
    if (dado.kind !== "Truncated") {
      par(dl, "filhos", `${no.filhos.length} diretos · ${no.descendentes} no total`);
      const atributos = Object.entries(dado.attributes);
      if (atributos.length) {
        const tabela = document.createElement("dl");
        tabela.className = "ast-atributos";
        for (const [k, v] of atributos) par(tabela, k, v === null ? "null" : Array.isArray(v) ? `[${v.join(", ")}]` : JSON.stringify(v));
        par(dl, "atributos", tabela);
      }
    }
    const partesDetalhe = [titulo, dl];
    if (dado.kind === "Truncated") {
      const { reason, omitted_nodes: omitidos } = dado.attributes;
      const aviso = document.createElement("p");
      aviso.className = "ast-aviso";
      aviso.textContent = (EXPLICA_TRUNCADO[reason] || ((n) => `${n} nós ficaram de fora.`))(omitidos);
      partesDetalhe.push(aviso);
    } else if (!linhaConfiavel(no)) {
      const aviso = document.createElement("p");
      aviso.className = "ast-aviso";
      aviso.textContent = "O parser atual não registra a linha de blocos seq/par e devolve sempre 1. Por isso a linha não é destacada no editor. A correção é do Eixo A.";
      partesDetalhe.push(aviso);
    }
    partesDetalhe.push(caminhoAte(no));
    detalhes.replaceChildren(...partesDetalhe);
  }

  function anunciar() {
    desenharDetalhes(selecionado);
    aoSelecionar(linhaConfiavel(selecionado) && !selecionado.ehMais ? selecionado.dado.line : null);
  }

  // ------------------------------------------------------------ DOM sob demanda

  function atualizarLinha(no) {
    const li = no.li;
    if (!li) return;
    const temFilhos = no.filhos.length > 0;
    if (temFilhos) li.setAttribute("aria-expanded", String(no.aberto));
    li.querySelector(".alternar").textContent = temFilhos ? (no.aberto ? "▾" : "▸") : "·";
    const ocultos = li.querySelector(":scope > .item-linha .ocultos");
    ocultos.textContent = temFilhos && !no.aberto ? `+${no.descendentes}` : "";
  }

  function criarItem(no) {
    const { dado } = no;
    const li = document.createElement("li");
    li.id = `ast-${dado.id}`;
    li.setAttribute("role", "treeitem");
    li.setAttribute("aria-level", String(no.nivel));
    li.setAttribute("aria-selected", String(no === selecionado));
    const linha = document.createElement("div");
    linha.className = `item-linha${dado.kind === "Truncated" ? " no-truncado" : ""}`;
    const papel = dado.role === null ? "" : dado.index === null ? dado.role : `${dado.role}[${dado.index}]`;
    const conteudo = document.createElement("span");
    conteudo.className = "no";
    const rotulo = span("no-rotulo", dado.label);
    rotulo.title = dado.kind;
    conteudo.append(rotulo);
    if (papel) conteudo.append(span("no-papel", papel));
    const atributos = formatarAtributos(dado);
    if (atributos) conteudo.append(span("no-attr", atributos));
    conteudo.append(span("no-linha", `L${dado.line}`), span("ocultos", ""));
    linha.append(span("alternar", ""), conteudo);
    li.append(linha);
    no.li = li;
    atualizarLinha(no);
    if (no.aberto && no.filhos.length) li.append(criarGrupo(no));
    return li;
  }

  // O marcador Truncated é sempre o último filho (§1.4) e fica visível mesmo com o lote incompleto,
  // para o estudante ver que a árvore foi cortada.
  function partes(no) {
    const ultimo = no.filhos[no.filhos.length - 1];
    const marcador = ultimo && ultimo.dado.kind === "Truncated" ? ultimo : null;
    const comuns = marcador ? no.filhos.slice(0, -1) : no.filhos;
    return { visiveis: comuns.slice(0, no.mostrar), restantes: Math.max(0, comuns.length - no.mostrar), marcador };
  }

  function criarMais(no, restantes) {
    const li = document.createElement("li");
    li.id = `ast-mais-${no.dado.id}`;
    li.setAttribute("role", "treeitem");
    li.setAttribute("aria-level", String(no.nivel + 1));
    li.setAttribute("aria-selected", "false");
    const linha = document.createElement("div");
    linha.className = "item-linha item-mais";
    linha.append(span("alternar", "…"), span("no", `Mostrar mais ${Math.min(LOTE, restantes)} (faltam ${restantes})`));
    li.append(linha);
    no.mais = { ehMais: true, pai: no, dado: { id: `mais-${no.dado.id}` }, li, filhos: [] };
    return li;
  }

  function criarGrupo(no) {
    const grupo = document.createElement("ul");
    grupo.setAttribute("role", "group");
    const { visiveis, restantes, marcador } = partes(no);
    for (const filho of visiveis) grupo.append(criarItem(filho));
    no.mais = null;
    if (restantes) grupo.append(criarMais(no, restantes));
    if (marcador) grupo.append(criarItem(marcador));
    return grupo;
  }

  function mostrarMais(no) {
    const anterior = no.mais;
    const primeiroNovo = partes(no).visiveis.length;
    no.mostrar += LOTE;
    const { visiveis, restantes } = partes(no);
    const novos = visiveis.slice(primeiroNovo);
    const fragmento = document.createDocumentFragment();
    for (const filho of novos) fragmento.append(criarItem(filho));
    no.mais = null;
    if (restantes) fragmento.append(criarMais(no, restantes));
    anterior.li.replaceWith(fragmento);
    selecionar(novos[0]);
    atualizarContagem();
  }

  function soltarDescendentes(no) {
    const pilha = [...no.filhos];
    while (pilha.length) {
      const atual = pilha.pop();
      if (!atual.li) continue;
      atual.li = null;
      pilha.push(...atual.filhos);
    }
  }

  function desenharTudo() {
    soltarDescendentes({ filhos: [primeiro] });
    lista.replaceChildren(criarItem(primeiro));
    marcarSelecionado();
    atualizarContagem();
  }

  function atualizarContagem() {
    const desenhados = lista.getElementsByTagName("li").length;
    contagem.textContent = `${desenhados} de ${nos.length} itens desenhados`;
  }

  // ------------------------------------------------------------ ações

  function abrir(no) {
    if (!no.filhos.length || no.aberto) return;
    no.aberto = true;
    if (no.li) no.li.append(criarGrupo(no));
    atualizarLinha(no);
    atualizarContagem();
  }

  function fechar(no) {
    if (!no.filhos.length || !no.aberto) return;
    no.aberto = false;
    if (ehAncestral(no, selecionado)) selecionar(no);
    no.li?.querySelector(":scope > ul[role=group]")?.remove();
    soltarDescendentes(no);
    atualizarLinha(no);
    atualizarContagem();
  }

  function ehAncestral(possivel, no) {
    for (let p = no.pai; p; p = p.pai) if (p === possivel) return true;
    return false;
  }

  function definirAbertos(regra) {
    for (const no of nos) no.aberto = no.filhos.length > 0 && regra(no);
    if (selecionado.ehMais) selecionado = selecionado.pai; // o item "mostrar mais" é recriado
    if (!estaVisivel(selecionado)) selecionado = primeiro;
    desenharTudo();
    anunciar();
  }

  function estaVisivel(no) {
    if (no.ehMais) return no.pai.aberto && estaVisivel(no.pai);
    for (let p = no.pai; p; p = p.pai) if (!p.aberto) return false;
    return Boolean(no.li);
  }

  function marcarSelecionado() {
    lista.setAttribute("aria-activedescendant", `ast-${selecionado.dado.id}`);
    selecionado.li?.setAttribute("aria-selected", "true");
  }

  function selecionar(no) {
    if (selecionado.li) selecionado.li.setAttribute("aria-selected", "false");
    selecionado = no;
    marcarSelecionado();
    selecionado.li?.querySelector(".item-linha")?.scrollIntoView({ block: "nearest" });
    anunciar();
  }

  // Ordem visível (pré-ordem pelos nós abertos, respeitando o lote e o "mostrar mais"), para as setas.
  function visiveis() {
    const saida = [];
    const pilha = [primeiro];
    while (pilha.length) {
      const no = pilha.pop();
      saida.push(no);
      if (!no.aberto || !no.filhos.length) continue;
      const { visiveis: filhos, marcador } = partes(no);
      const ordem = [...filhos, ...(no.mais ? [no.mais] : []), ...(marcador ? [marcador] : [])];
      for (let i = ordem.length - 1; i >= 0; i--) pilha.push(ordem[i]);
    }
    return saida;
  }

  // ------------------------------------------------------------ eventos

  lista.addEventListener("click", (evento) => {
    const li = evento.target.closest("li[role=treeitem]");
    if (!li) return;
    if (li.id.startsWith("ast-mais-")) {
      mostrarMais(porId.get(li.id.slice(9)));
      lista.focus({ preventScroll: true });
      return;
    }
    const no = porId.get(li.id.slice(4));
    if (evento.target.closest(".alternar")) {
      if (no.aberto) fechar(no);
      else abrir(no);
    }
    selecionar(no);
    lista.focus({ preventScroll: true });
  });

  lista.addEventListener("keydown", (evento) => {
    const no = selecionado;
    if (no.ehMais && (evento.key === "Enter" || evento.key === " ")) {
      evento.preventDefault();
      mostrarMais(no.pai);
      return;
    }
    switch (evento.key) {
      case "ArrowDown":
      case "ArrowUp": {
        const ordem = visiveis();
        const i = ordem.indexOf(no) + (evento.key === "ArrowDown" ? 1 : -1);
        if (i >= 0 && i < ordem.length) selecionar(ordem[i]);
        break;
      }
      case "ArrowRight":
        if (no.filhos.length && !no.aberto) abrir(no);
        else if (no.aberto && no.filhos.length) selecionar(no.filhos[0]);
        break;
      case "ArrowLeft":
        if (no.aberto && no.filhos.length) fechar(no);
        else if (no.pai) selecionar(no.pai);
        break;
      case "Home":
        selecionar(primeiro);
        break;
      case "End": {
        const ordem = visiveis();
        selecionar(ordem[ordem.length - 1]);
        break;
      }
      case "Enter":
      case " ":
        if (no.aberto) fechar(no);
        else abrir(no);
        break;
      default:
        return;
    }
    evento.preventDefault();
  });

  desenharTudo();
  desenharDetalhes(selecionado);
  return { elemento, anunciar };
}
