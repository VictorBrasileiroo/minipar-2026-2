// Erros legíveis (WEB-02): trecho do código com marcador na coluna e uma explicação didática por
// código do catálogo do contrato C-WEB-v1 §1.5. A mensagem original do compilador é sempre mantida.

const TITULO_FASE = {
  lexer: "Erro léxico",
  parser: "Erro sintático",
  semantic: "Erro semântico",
  tac: "Aviso do TAC",
  cpp: "Erro na geração de C++",
  gpp: "Erro do g++",
  internal: "Erro interno",
};

const EMBUTIDAS = "exp, random, range, len, to_number e parse_ints";

// Primeiro e segundo trechos entre aspas simples da mensagem, ex.: "Metodo 'x' nao declarado em 'C'."
function citados(mensagem) {
  return [...mensagem.matchAll(/'([^']*)'/g)].map((m) => m[1]);
}

function codigo(texto) {
  const el = document.createElement("code");
  el.textContent = texto;
  return el;
}

// Cada entrada devolve uma lista de partes (texto ou nó) para montar a explicação.
const CATALOGO = {
  LEX_UNKNOWN_CHAR: (d) => {
    const [c = "?"] = citados(d.message);
    const partes = ["O caractere ", codigo(c), " não faz parte do MiniPar. O analisador léxico não consegue formar nenhum token com ele, então a análise para aqui."];
    if (c === "&" || c === "|") partes.push(" No MiniPar, o E e o OU lógicos têm dois caracteres: ", codigo("&&"), " e ", codigo("||"), ".");
    else partes.push(" Confira se não é um erro de digitação ou um operador de outra linguagem.");
    return partes;
  },
  LEX_UNTERMINATED_STRING: () => ["A string que começa aqui não tem as aspas de fechamento. O analisador léxico leu até o fim do arquivo procurando o ", codigo("\""), " final. Feche a string."],
  SYN_EXPECTED_TOKEN: (d) => {
    const m = /^Esperado (.*) \(Encontrado: '(.*)'\)$/.exec(d.message);
    if (!m) return ["O parser esperava outro símbolo neste ponto."];
    const encontrado = m[2] === "" ? "o fim do arquivo" : codigo(m[2]);
    return ["O parser esperava “", m[1], "” e encontrou ", encontrado,
      ". Muitas vezes o problema está logo antes deste ponto: um ", codigo(";"), " esquecido ou um parêntese ou chave sem par."];
  },
  SYN_EXPECTED_EXPRESSION: (d, ctx) => {
    const token = ctx.tokenEm(d.line, d.column);
    const encontrado = token ? codigo(token.lexeme) : "o fim do arquivo";
    return ["Neste ponto o parser esperava um valor: um número, uma string, um nome, uma chamada de função ou uma expressão entre parênteses. Encontrou ",
      encontrado, ". Como o parser para no primeiro erro, não há AST para mostrar."];
  },
  SYN_INVALID_ASSIGNMENT: () => ["O lado esquerdo do ", codigo("="), " não pode receber valor. Só variáveis, atributos (", codigo("obj.campo"), ") e posições de lista (", codigo("lista[i]"), ") podem ser atribuídos."],
  SYN_INVALID_STATEMENT: () => ["Esta instrução é só uma expressão solta, que não faz nada. Uma instrução que começa com um nome precisa ser uma atribuição (", codigo("x = ...;"), ") ou uma chamada (", codigo("f(...);"), ")."],
  SYN_UNRECOGNIZED_STATEMENT: (d) => {
    const [t = "?"] = citados(d.message);
    return ["Nenhuma instrução do MiniPar começa com ", codigo(t), ". Instruções começam com uma palavra-chave (",
      codigo("var"), ", ", codigo("if"), ", ", codigo("while"), ", ", codigo("for"), ", ", codigo("func"), ", ", codigo("class"), ", ",
      codigo("print"), ", ", codigo("return"), "…), com um tipo (", codigo("number"), ", ", codigo("string"), "…) ou com um nome."];
  },
  SEM_REDECLARED: (d) => {
    const [n = "?"] = citados(d.message);
    return [codigo(n), " já foi declarado neste mesmo escopo. Use outro nome ou, se a ideia era mudar o valor, troque a declaração por uma atribuição: ", codigo(`${n} = ...;`)];
  },
  SEM_UNDECLARED_VARIABLE: (d) => {
    const [n = "?"] = citados(d.message);
    return [codigo(n), " é usado sem ter sido declarado em nenhum escopo visível daqui. Declare antes de usar, por exemplo ", codigo(`var ${n} = 0;`), ", ou confira a grafia."];
  },
  SEM_TYPE_MISMATCH: (d) => {
    const m = /esperado (\S+), recebido ([^.]+)/.exec(d.message);
    return m
      ? ["O valor tem tipo ", codigo(m[2]), ", mas a variável foi declarada como ", codigo(m[1]), ". Converta o valor ou mude o tipo da declaração."]
      : ["O tipo do valor atribuído não combina com o tipo registrado para a variável."];
  },
  SEM_NUMERIC_OPERANDS: (d) => {
    const [op = "?"] = citados(d.message);
    return ["O operador ", codigo(op), " só funciona com números, e pelo menos um dos lados não é número. Só o ", codigo("+"), " também aceita strings."];
  },
  SEM_OUTSIDE_LOOP: () => [codigo("break"), " e ", codigo("continue"), " só fazem sentido dentro de um laço (", codigo("while"), ", ", codigo("do"), " ou ", codigo("for"), ")."],
  SEM_UNDECLARED_FUNCTION: (d) => {
    const [n = "?"] = citados(d.message);
    return ["A função ", codigo(n), " não foi declarada no programa nem é uma das embutidas (", EMBUTIDAS, ")."];
  },
  SEM_UNDECLARED_CLASS: (d) => {
    const [n = "?"] = citados(d.message);
    return [codigo(`new ${n}(...)`), " usa uma classe que não foi declarada no programa."];
  },
  SEM_UNDECLARED_SUPERCLASS: (d) => {
    const [n = "?"] = citados(d.message);
    return ["A classe herda de ", codigo(n), ", que não foi declarada no programa."];
  },
  SEM_UNDECLARED_METHOD: (d) => {
    const [m = "?", c = "?"] = citados(d.message);
    return ["A classe ", codigo(c), " não tem um método ", codigo(m), ". Confira a grafia ou declare o método com ", codigo("func"), " dentro da classe."];
  },
  SEM_UNDECLARED_ATTRIBUTE: (d) => {
    const [a = "?", c = "?"] = citados(d.message);
    return ["A classe ", codigo(c), " não tem um atributo ", codigo(a), ". Atributos são declarados com ", codigo("var"), " no corpo da classe."];
  },
  SEM_ARITY: () => ["A chamada passa uma quantidade de argumentos diferente da quantidade de parâmetros da declaração. A mensagem mostra quantos eram esperados e quantos vieram."],
  TAC_HARDCODED: () => ["O TAC deste programa é um texto fixo do compilador atual, não foi gerado a partir da AST. Não use este TAC como exemplo; a correção está no card CORE-02 do Eixo A."],
  GPP_FAILED: () => ["O C++ gerado não compilou no g++. A saída do g++ aparece na fase Compilar e executar. Como o programa passou na análise, o problema pode estar no gerador de C++, e não no seu código."],
  GPP_NO_BINARY: () => ["O g++ terminou sem erro, mas não gerou o executável. Isso não depende do seu programa; avise quem mantém o compilador."],
  GPP_TIMEOUT: () => ["A compilação do C++ passou de 120 segundos e foi interrompida."],
  GPP_NOT_FOUND: () => ["O compilador C++ (g++) não foi encontrado na máquina do servidor. Isso é um problema de ambiente, não do seu programa."],
  INTERNAL_ERROR: () => ["O compilador falhou de um jeito inesperado. Isso não é um erro do seu programa; avise quem mantém o compilador."],
};

// ctx: { codigo: string, tokens: lista de tokens da fase lexer (pode ser vazia) }
export function criarCartaoErro(d, ctx, { aoAbrir } = {}) {
  const linhas = ctx.codigo.split("\n");
  const cartao = document.createElement("article");
  cartao.className = `erro-cartao ${d.severity === "warning" ? "aviso" : "erro"}`;

  const onde = [d.line ? `linha ${d.line}` : null, d.column ? `coluna ${d.column}` : null].filter(Boolean).join(", ");
  const cabecalho = document.createElement(aoAbrir ? "button" : "div");
  cabecalho.className = "erro-cabecalho";
  if (aoAbrir) {
    cabecalho.type = "button";
    cabecalho.title = "Abrir a fase e mostrar a linha no código";
    cabecalho.addEventListener("click", () => aoAbrir(d));
  }
  cabecalho.textContent = `${TITULO_FASE[d.phase] || "Erro"}${onde ? " · " + onde : ""}`;
  cartao.append(cabecalho);

  if (d.line && d.line <= linhas.length) {
    const texto = linhas[d.line - 1];
    const margem = String(d.line).length;
    const pre = document.createElement("pre");
    pre.className = "erro-trecho";
    pre.append(`${d.line} │ ${texto}`);
    if (d.column) {
      // Mantém tabs para o marcador cair na coluna certa mesmo com indentação por tab.
      const recuo = [...texto.slice(0, d.column - 1)].map((c) => (c === "\t" ? "\t" : " ")).join("");
      const marcador = document.createElement("span");
      marcador.className = "erro-marcador";
      marcador.textContent = "^";
      pre.append(`\n${" ".repeat(margem)} │ ${recuo}`, marcador);
    }
    cartao.append(pre);
  }

  const explicacao = document.createElement("p");
  explicacao.className = "erro-explicacao";
  const montar = CATALOGO[d.code];
  explicacao.append(...(montar ? montar(d, ctx) : ["Ainda não há explicação para este código. Veja a mensagem do compilador abaixo."]));
  if (d.line && !d.column && d.phase === "semantic") explicacao.append(" O semântico só informa a linha, por isso não há marcador de coluna.");
  cartao.append(explicacao);

  const original = document.createElement("p");
  original.className = "erro-original";
  original.append("Mensagem do compilador: ", d.message, " · ", codigo(d.code));
  cartao.append(original);
  return cartao;
}

export function contextoErros(codigoFonte, tokens) {
  return {
    codigo: codigoFonte,
    tokenEm: (linha, coluna) => tokens.find((t) => t.line === linha && t.column === coluna) || null,
  };
}

export const CODIGOS_COM_EXPLICACAO = Object.keys(CATALOGO);
