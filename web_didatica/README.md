# Web didática

Área do Eixo B. Desenvolver separada da Web original, integrando pela API acordada (contrato C-WEB-v1, `docs/02_CONTRATOS_TECNICOS.md` §1).

**Estado atual: wireframe navegável em modo mock (WEB-01).** A interface mostra as fases a partir das fixtures e avisa no topo que os dados são mock. Ainda não chama o compilador: Analisar, Compilar e executar e os downloads ficam desabilitados até a integração (WEB-03/WEB-04).

## Como abrir

Os dados são lidos com `fetch`, então a pasta precisa ser servida por HTTP; abrir o `index.html` direto do disco não funciona. Na raiz do repositório:

```bash
py -B -m http.server 5001 --bind 127.0.0.1 --directory web_didatica
```

Depois abrir `http://127.0.0.1:5001/static/index.html`. O servidor do Python serve só arquivos e escuta apenas em `127.0.0.1`. O servidor Flask com as rotas `/api/v1/…` (§1.8 do contrato) entra no WEB-03.

## O que a tela mostra

- **Editor** com o código do exemplo e numeração de linhas. Ao editar, a resposta é descartada porque o `source_hash` deixa de bater (regra do §1.3); o botão Restaurar volta ao código do exemplo.
- **Diagnósticos legíveis (WEB-02)**: cada erro aparece como um cartão com a fase, a linha e a coluna, o trecho do código com um `^` na coluna (quando a fase informa coluna), uma explicação em português e a mensagem original do compilador com o código do catálogo. Os 24 códigos do §1.5 do contrato têm explicação; um código novo mostra um texto genérico. Clicar no cabeçalho abre a fase e destaca a linha no editor. O painel da fase com erro repete o cartão e destaca a linha ao abrir.
- **Trilha de fases** Tokens → AST → Semântico → TAC → C++ → Compilar e executar, com o status de cada uma (`ok`, `error`, `skipped`). Cada fase tem âncora própria (`#tokens`, `#ast`, `#semantico`, `#tac`, `#cpp`, `#executar`), e as setas do teclado trocam de fase.
- **Painéis**: tabela de tokens; AST recolhível (detalhes abaixo); escopos aninhados com os símbolos de cada um; TAC e C++ com numeração; resultado do g++ e da execução (no exemplo EXEC-01).
- **Programas grandes (WEB-02)**: tokens, símbolos e linhas de TAC, C++ e saída são desenhados em blocos de 500, com o botão "Mostrar mais" para o bloco seguinte. Passar o mouse ou clicar num token destaca a linha dele no editor; clicar num símbolo também. Os símbolos têm um filtro por nome (sem diferenciar maiúsculas) que mostra só os escopos com resultados.
- **AST recolhível (WEB-02)**: abre com três níveis; a seta ao lado de cada nó abre ou fecha, e um nó fechado mostra quantos descendentes esconde (`+N`). Há botões para expandir tudo, recolher tudo e voltar aos primeiros níveis. Os filhos de um nó só são desenhados quando ele é aberto, e nós com muitos filhos mostram 200 por vez com o item "Mostrar mais". O marcador `Truncated` do contrato fica sempre visível no fim. Com a árvore em foco: setas para cima e para baixo, direita abre ou desce ao primeiro filho, esquerda fecha ou sobe ao pai, Home/End, Enter ou espaço abre e fecha.
- **Nó selecionado (WEB-02)**: ao lado da árvore aparecem tipo, papel no pai, linha, nível, filhos, atributos e o caminho até a raiz (cada ancestral é clicável). A linha do nó fica destacada no editor, que rola até ela. Blocos `seq`/`par` não destacam linha: o parser atual grava sempre 1 neles, e o painel avisa. No marcador `Truncated`, o painel explica o limite do contrato e quantos nós ficaram de fora. Clicar num diagnóstico também destaca a linha dele.
- Fase `skipped` explica o motivo (`previous_phase_failed` ou `not_requested`) em vez de ficar vazia.

## Organização

- `static/index.html`, `static/css/app.css`, `static/js/app.js`: interface.
- `static/js/arvore_ast.js`: árvore da AST com renderização sob demanda e teclado no padrão de árvore do WAI-ARIA.
- `static/js/erros.js`: catálogo de explicações por código de diagnóstico e cartão de erro com trecho e marcador. As explicações são textos da Web; a mensagem do compilador não é alterada.
- `static/js/fonte_mock.js`: única parte que sabe de onde vêm os dados. Na integração, uma fonte que chama `/api/v1/…` substitui esta, devolvendo o mesmo formato.
- `fixtures/`: respostas mock no formato do contrato. Ver [fixtures/README.md](fixtures/README.md).
- `tools/`: `gerar_fixtures.py` gera as fixtures a partir das fases reais de `src/` (só leitura) e `validar_fixtures.py` as confere contra o contrato. A Web não usa esses scripts.
