# Web didática

Área do Eixo B. Desenvolver separada da Web original, integrando pela API acordada (contrato C-WEB-v1, `docs/02_CONTRATOS_TECNICOS.md` §1).

**Estado atual: integrada ao serviço real para análise (WEB-03).** Por padrão a página manda o código do editor a `server.py`, que chama `analyze` de `src/service.py` (Eixo A, `CORE-08`) e devolve o envelope `minipar.compile.v1` sem alterar nada. Tokens, AST, escopos, símbolos, TAC, C++ e diagnósticos vêm do compilador no momento do pedido; nenhum resultado de fase é lido de arquivo. As fixtures só fornecem o código dos exemplos. Compilar e executar e os downloads continuam desabilitados até o WEB-04. O modo mock do WEB-01 continua disponível com `?fonte=mock`.

## Como abrir

**Serviço real (padrão).** Precisa da `.venv` do projeto com Flask 3.0.0 (`requeriments.txt`; ver `docs/10_GUIA_SETUP_REPOSITORIO.md`). Na raiz do repositório:

```bash
.venv\Scripts\python.exe -B web_didatica/server.py
```

Depois abrir `http://127.0.0.1:5001/`. O servidor escuta só em `127.0.0.1:5001` (§1.8), sem modo debug.

**Modo mock (WEB-01).** Abrir `http://127.0.0.1:5001/static/index.html?fonte=mock` com o servidor acima, ou servir só os arquivos, sem Flask:

```bash
py -B -m http.server 5001 --bind 127.0.0.1 --directory web_didatica
```

e abrir `http://127.0.0.1:5001/static/index.html?fonte=mock`. Sem `?fonte=mock`, esse servidor de arquivos não tem a rota `/api/v1/analyze` e a página avisa que a análise falhou; ela nunca troca para o mock sozinha.

## Servidor (`server.py`)

Camada fina do §1.1: valida a requisição, chama `src/service.py` e serializa o `dict` devolvido. Não reimplementa fase nem lê stdout/stderr do compilador. B não edita `src/`.

| Rota | Resposta |
|---|---|
| `POST /api/v1/analyze` com `{"source": "..."}` | HTTP 200 com o envelope de `service.analyze`, inclusive quando o programa tem erro (`ok: false`) |
| `GET /` | redireciona para `/static/index.html` |
| `GET /static/…` | arquivos da interface |
| `GET /fixtures/<nome>.json` | fixtures (código dos exemplos e modo mock); outros arquivos dão 404 |

- **HTTP 400** `{"error": {"code": "BAD_REQUEST", "message": ...}}`: corpo que não é JSON (ou sem `Content-Type: application/json`), JSON que não é objeto, `source` ausente ou que não é texto, texto que não é UTF-8 válido, código acima de 200 000 bytes em UTF-8. Corpo acima de 1,6 MB nem é lido e também dá 400.
- **HTTP 500** `{"error": {"code": "INTERNAL_ERROR", ...}}` só para falha do próprio servidor, sem stack trace na resposta (vai para o log). Erro interno do compilador já chega como `INTERNAL_ERROR` dentro do envelope, com HTTP 200.
- As chaves do envelope saem na ordem do serviço (`sort_keys` desligado), então as fases ficam na ordem do §1.3.
- As rotas `compile`, `execute` e `artifacts/<id>/<kind>` do §1.8 entram no WEB-04.

## Fluxo da análise no navegador

- Ao escolher um exemplo, o código dele vai para o editor e é analisado na hora pelo serviço. O botão **Analisar** (ou Ctrl+Enter no editor) envia o código atual. A linha abaixo dos botões mostra o andamento, a duração informada pelo serviço e a quantidade de erros.
- **Descarte por `source_hash` (§1.3):** quando a resposta chega, a página calcula o SHA-256 do código que está no editor naquele momento. Se não for o `source_hash` da resposta, ela é descartada inteira e a página avisa (teste: editar o código durante uma análise lenta). Uma resposta de uma análise anterior ou de outro exemplo também é ignorada. Editar depois de uma análise marca as fases como desatualizadas até a próxima análise.
- **Fase com erro sem resultado:** se uma fase termina com `error` sem o campo que o painel desenha (ex.: `cpp` sem `text`), o painel diz que a fase falhou e mostra os diagnósticos dela e os internos. Sem diagnóstico, mostra só a falha genérica, sem inventar mensagem (orientação do handoff do `CORE-08`).
- **Códigos fora do catálogo v1:** o serviço local já emite códigos propostos na `docs/CR-CORE08-DIAGNOSTICOS.md` (ex.: `CPP_UNSUPPORTED_FEATURE`, `SEM_FJ_07`), ainda sem ratificação A+B. A Web mostra esses diagnósticos com a mensagem do compilador e o texto genérico de código sem explicação; não há explicação própria para eles até a CR ser aprovada.
- Falha de rede, HTTP 400/500 ou resposta que não é envelope aparecem na linha de andamento, com a instrução para iniciar `server.py` ou usar `?fonte=mock`.
- O exemplo EXEC-01 (compilar e executar) só aparece no modo mock até o WEB-04.

## O que a tela mostra

- **Editor** com o código do exemplo e numeração de linhas. Ao editar, a análise exibida fica desatualizada porque o `source_hash` deixa de bater (regra do §1.3); no modo real, Analisar reanalisa o código atual. O botão Restaurar volta ao código do exemplo (no modo real aparece sempre que o editor difere do exemplo; no mock, quando a resposta foi descartada).
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
- `static/js/fonte_real.js` (padrão) e `static/js/fonte_mock.js` (`?fonte=mock`): as únicas partes que sabem de onde vêm os dados. As duas devolvem o mesmo formato; só a real tem `analisar()`, que faz o `POST /api/v1/analyze`.
- `server.py`: servidor Flask da Web didática (seção acima).
- `tests/test_server.py`: testes do servidor com o cliente de teste do Flask e o serviço real, sem abrir porta: `.venv\Scripts\python.exe -B -m unittest discover -s web_didatica/tests -v`.
- `fixtures/`: respostas mock no formato do contrato. Ver [fixtures/README.md](fixtures/README.md).
- `tools/`: `gerar_fixtures.py` gera as fixtures a partir das fases reais de `src/` (só leitura) e `validar_fixtures.py` as confere contra o contrato. A Web não usa esses scripts.
