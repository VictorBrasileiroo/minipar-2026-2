# Web didática

Área do Eixo B. Desenvolver separada da Web original, integrando pela API acordada (contrato C-WEB-v1, `docs/02_CONTRATOS_TECNICOS.md` §1).

**Estado atual: integrada ao serviço real para análise (WEB-03), compilação, execução e downloads (WEB-04).** Por padrão a página manda o código do editor a `server.py`, que chama `analyze`, `compile_program`, `execute` e `get_artifact` de `src/service.py` (Eixo A, `CORE-08`) e devolve o resultado sem alterar nada. Tokens, AST, escopos, símbolos, TAC, C++, a saída do g++ e a saída do programa vêm do compilador e do binário no momento do pedido; nenhum resultado de fase ou de execução é lido de arquivo. As fixtures só fornecem o código (e a entrada) dos exemplos. O modo mock do WEB-01 continua disponível com `?fonte=mock`.

Passo a passo ilustrado para o relatório (WEB-05): [docs/relatorio/WEB-05_INTERFACE_WEB_DIDATICA.md](../docs/relatorio/WEB-05_INTERFACE_WEB_DIDATICA.md), com as capturas de `docs/evidencias/WEB-05/`.

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

e abrir `http://127.0.0.1:5001/static/index.html?fonte=mock`. Sem `?fonte=mock`, esse servidor de arquivos não tem as rotas `/api/v1/…` e a página avisa que a análise falhou; ela nunca troca para o mock sozinha.

Compilar exige o g++ acessível (no `PATH` ou em `CXX`), como no restante do projeto (`docs/10_GUIA_SETUP_REPOSITORIO.md`). Sem ele, a fase `gpp` termina com `GPP_NOT_FOUND` e a página mostra o erro.

## Servidor (`server.py`)

Camada fina do §1.1: valida a requisição, chama `src/service.py` e serializa o `dict` devolvido. Não reimplementa fase nem lê stdout/stderr do compilador. B não edita `src/`.

| Rota | Resposta |
|---|---|
| `POST /api/v1/analyze` com `{"source": "..."}` | HTTP 200 com o envelope de `service.analyze`, inclusive quando o programa tem erro (`ok: false`) |
| `POST /api/v1/compile` com `{"source": "..."}` | HTTP 200 com o envelope de `service.compile_program` (as seis fases, g++ incluído), inclusive com erro de compilação ou do g++ |
| `POST /api/v1/execute` com `{"artifact_id": "...", "stdin": "...", "timeout_sec": 10}` | HTTP 200 com o resultado `minipar.execute.v1` de `service.execute`. `stdin` é opcional (padrão `""`) e `timeout_sec` também (padrão 10) |
| `GET /api/v1/artifacts/<id>/<kind>` | o arquivo `cpp`, `tac` ou `binary` daquela compilação, como anexo com o nome do §1.7 (`minipar_<8 do id>.cpp`, `.tac`, `.exe`) e o `media_type` do serviço |
| `GET /` | redireciona para `/static/index.html` |
| `GET /static/…` | arquivos da interface |
| `GET /fixtures/<nome>.json` | fixtures (código dos exemplos e modo mock); outros arquivos dão 404 |
| `GET /exemplos/t11.json` | exemplo do Teste 11: o código de `tests/2026_2/test11/minicompilador.minipar` (só leitura) e a entrada do caso 1 |

- **HTTP 400** `{"error": {"code": "BAD_REQUEST", "message": ...}}`: corpo que não é JSON (ou sem `Content-Type: application/json`), JSON que não é objeto, `source` ausente ou que não é texto, texto que não é UTF-8 válido, código acima de 200 000 bytes em UTF-8. Corpo acima de 1,6 MB nem é lido e também dá 400. Em `execute`: `artifact_id` ausente ou que não é texto, `stdin` que não é texto, `timeout_sec` que não é inteiro de 1 a 30 (`"10"`, `10.0` e `true` também dão 400). Em `artifacts`: id fora do formato ou `kind` fora de `cpp`/`tac`/`binary` (o serviço responde `INVALID_ARGUMENT`).
- **HTTP 404** em `artifacts` quando o artefato não existe nesta compilação (ex.: `binary` quando o g++ falhou) ou não está mais registrado: `{"error": {"code": "ARTIFACT_NOT_FOUND", ...}}`.
- **Execução sempre com HTTP 200 quando a requisição é válida.** Tempo esgotado (`timed_out: true`, `exit_code: null`), código de saída diferente de 0 e id inexistente ou fora do formato (`error.code` `ARTIFACT_NOT_FOUND` ou `INVALID_ARGUMENT`) vêm dentro do envelope `minipar.execute.v1`, como o §1.6 define; o servidor não confere o formato do id, só repassa.
- O download usa o caminho que `service.get_artifact` registrou para aquele id; o servidor não monta caminho nenhum. Respostas de download saem com `Cache-Control: no-store` e `X-Content-Type-Options: nosniff`.
- **HTTP 500** `{"error": {"code": "INTERNAL_ERROR", ...}}` só para falha do próprio servidor, sem stack trace na resposta (vai para o log). Erro interno do compilador já chega como `INTERNAL_ERROR` dentro do envelope, com HTTP 200.
- As chaves do envelope saem na ordem do serviço (`sort_keys` desligado), então as fases ficam na ordem do §1.3.

## Fluxo da análise no navegador

- Ao escolher um exemplo, o código dele vai para o editor e é analisado na hora pelo serviço. O botão **Analisar** (ou Ctrl+Enter no editor) envia o código atual. A linha abaixo dos botões mostra o andamento, a duração informada pelo serviço e a quantidade de erros.
- **Descarte por `source_hash` (§1.3):** quando a resposta chega, a página calcula o SHA-256 do código que está no editor naquele momento. Se não for o `source_hash` da resposta, ela é descartada inteira e a página avisa (teste: editar o código durante uma análise lenta). Uma resposta de uma análise anterior ou de outro exemplo também é ignorada. Editar depois de uma análise marca as fases como desatualizadas até a próxima análise.
- **Fase com erro sem resultado:** se uma fase termina com `error` sem o campo que o painel desenha (ex.: `cpp` sem `text`), o painel diz que a fase falhou e mostra os diagnósticos dela e os internos. Sem diagnóstico, mostra só a falha genérica, sem inventar mensagem (orientação do handoff do `CORE-08`).
- **Códigos fora do catálogo v1:** o serviço local já emite códigos propostos na `docs/CR-CORE08-DIAGNOSTICOS.md` (ex.: `CPP_UNSUPPORTED_FEATURE`, `SEM_FJ_07`), ainda sem ratificação A+B. A Web mostra esses diagnósticos com a mensagem do compilador e o texto genérico de código sem explicação; não há explicação própria para eles até a CR ser aprovada.
- Falha de rede, HTTP 400/500 ou resposta que não é envelope aparecem na linha de andamento, com a instrução para iniciar `server.py` ou usar `?fonte=mock`.

## Compilar, executar e baixar (WEB-04)

- **Entrada e tempo limite.** Abaixo dos botões ficam a **Entrada (stdin)**, entregue inteira antes da execução (cada `input()` lê uma linha, §1.6), e o **Tempo limite** em segundos. A página confere o tempo limite (inteiro de 1 a 30) antes de enviar; o servidor confere de novo.
- **Compilar e executar** manda o código do editor para `POST /api/v1/compile`. A resposta passa pelo mesmo descarte por `source_hash` da análise: se o código mudou enquanto compilava, a compilação é descartada e nada é executado. Se alguma fase falhar, a página abre a fase com erro e avisa que nada foi executado. Com `ok: true` e `binary_id`, a página chama `POST /api/v1/execute` com esse `binary_id`, a entrada e o tempo limite, e abre a fase **Compilar e executar**.
- **Painel da fase.** Mostra o g++ (status, comando, código de retorno, duração, id da compilação e do binário, stdout e stderr do g++, aviso de truncamento em 64 KB e os diagnósticos `GPP_*`) e a execução: entrada usada, tempo limite, código de saída, tempo esgotado, duração, stdout e stderr (aviso de truncamento em 1 MB). O resultado é conferido com os campos que o definem (§1.6): sucesso só com `exit_code` 0 e sem `timed_out`. Tempo esgotado, código de saída diferente de 0, binário inexistente (`ARTIFACT_NOT_FOUND`) e envelope incoerente (`ok` que não bate com `exit_code`/`timed_out`) aparecem em caixas de erro próprias.
- **Executar de novo com a entrada atual** roda outra vez o mesmo binário, sem recompilar (útil para os três casos do Teste 11).
- **Downloads** `.cpp`, `.tac` e binário pedem `GET /api/v1/artifacts/<id>/<kind>` com os ids de `artifacts` **da compilação exibida nesta aba**. Uma compilação feita em outra aba (ou por outro cliente) tem outro id e não muda o que esta aba executa ou baixa. O botão do binário fica desabilitado quando o g++ não gerou binário. Artefato que não existe mais (HTTP 404) aparece na linha de andamento.
- Analisar depois de compilar troca o envelope pelo de `analyze`, em que `gpp` é sempre `not_requested`; a execução anterior deixa de ser exibida.

### Teste 11 e o `.arm`

- O exemplo **T11** traz o MiniCompilador em MiniPar (`tests/2026_2/test11/minicompilador.minipar`, lido por `GET /exemplos/t11.json`) com a entrada do caso 1. Os botões **caso 1/2/3** ao lado do tempo limite trocam a entrada pelas expressões de C-T11-v1 §3.1.
- Depois da execução, **Baixar .arm** recorta o Assembly do stdout no próprio navegador (`static/js/arm.js`), pelas regras de C-WEB-v1 §1.7 e C-T11-v1 §3.6 item 2, as mesmas de `tests/2026_2/test11/extrair_arm.py`: remove o `\r` do fim de cada linha, copia literalmente as linhas entre o título terminado em `Assembly ARMv7 (CPUlator):` e a primeira linha vazia e grava `t11_<8 do artifact_id>.arm` em UTF-8 com `\n` e uma linha em branco no fim. Título ausente ou repetido, bloco vazio, bloco que não começa com `.global _start`, bloco sem a linha vazia que o fecha e stdout truncado viram mensagem de erro, sem arquivo. A seção aparece no exemplo T11 e em qualquer execução cujo stdout tenha o título.
- A página `static/testes/arm.html` (`http://127.0.0.1:5001/static/testes/arm.html`) roda `arm.js` sobre as seis saídas de teste do §1.10 e compara byte a byte com o resultado do script, gravado em `static/testes/arm_casos.json` por `tools/gerar_casos_arm.py`.

## O que a tela mostra

- **Editor** com o código do exemplo e numeração de linhas. Ao editar, a análise exibida fica desatualizada porque o `source_hash` deixa de bater (regra do §1.3); no modo real, Analisar reanalisa o código atual. O botão Restaurar volta ao código do exemplo (no modo real aparece sempre que o editor difere do exemplo; no mock, quando a resposta foi descartada).
- **Diagnósticos legíveis (WEB-02)**: cada erro aparece como um cartão com a fase, a linha e a coluna, o trecho do código com um `^` na coluna (quando a fase informa coluna), uma explicação em português e a mensagem original do compilador com o código do catálogo. Os 24 códigos do §1.5 do contrato têm explicação; um código novo mostra um texto genérico. Clicar no cabeçalho abre a fase e destaca a linha no editor. O painel da fase com erro repete o cartão e destaca a linha ao abrir.
- **Trilha de fases** Tokens → AST → Semântico → TAC → C++ → Compilar e executar, com o status de cada uma (`ok`, `error`, `skipped`). Cada fase tem âncora própria (`#tokens`, `#ast`, `#semantico`, `#tac`, `#cpp`, `#executar`), e as setas do teclado trocam de fase.
- **Painéis**: tabela de tokens; AST recolhível (detalhes abaixo); escopos aninhados com os símbolos de cada um; TAC e C++ com numeração; resultado do g++ e da execução, downloads e `.arm` (seção acima; no mock, o resultado gravado do exemplo EXEC-01, com downloads desabilitados).
- **Programas grandes (WEB-02)**: tokens, símbolos e linhas de TAC, C++ e saída são desenhados em blocos de 500, com o botão "Mostrar mais" para o bloco seguinte. Passar o mouse ou clicar num token destaca a linha dele no editor; clicar num símbolo também. Os símbolos têm um filtro por nome (sem diferenciar maiúsculas) que mostra só os escopos com resultados.
- **AST recolhível (WEB-02)**: abre com três níveis; a seta ao lado de cada nó abre ou fecha, e um nó fechado mostra quantos descendentes esconde (`+N`). Há botões para expandir tudo, recolher tudo e voltar aos primeiros níveis. Os filhos de um nó só são desenhados quando ele é aberto, e nós com muitos filhos mostram 200 por vez com o item "Mostrar mais". O marcador `Truncated` do contrato fica sempre visível no fim. Com a árvore em foco: setas para cima e para baixo, direita abre ou desce ao primeiro filho, esquerda fecha ou sobe ao pai, Home/End, Enter ou espaço abre e fecha.
- **Nó selecionado (WEB-02)**: ao lado da árvore aparecem tipo, papel no pai, linha, nível, filhos, atributos e o caminho até a raiz (cada ancestral é clicável). A linha do nó fica destacada no editor, que rola até ela. Blocos `seq`/`par` não destacam linha: o parser atual grava sempre 1 neles, e o painel avisa. No marcador `Truncated`, o painel explica o limite do contrato e quantos nós ficaram de fora. Clicar num diagnóstico também destaca a linha dele.
- Fase `skipped` explica o motivo (`previous_phase_failed` ou `not_requested`) em vez de ficar vazia.

## Organização

- `static/index.html`, `static/css/app.css`, `static/js/app.js`: interface.
- `static/js/arvore_ast.js`: árvore da AST com renderização sob demanda e teclado no padrão de árvore do WAI-ARIA.
- `static/js/erros.js`: catálogo de explicações por código de diagnóstico e cartão de erro com trecho e marcador. As explicações são textos da Web; a mensagem do compilador não é alterada.
- `static/js/arm.js`: recorte do `.arm` do Teste 11 a partir do stdout (seção acima). Não analisa nem reescreve o Assembly.
- `static/js/fonte_real.js` (padrão) e `static/js/fonte_mock.js` (`?fonte=mock`): as únicas partes que sabem de onde vêm os dados. As duas devolvem o mesmo formato; só a real tem `analisar()`, `compilar()`, `executar()` e `urlArtefato()`, que usam as rotas `/api/v1/…`.
- `static/testes/arm.html` e `static/testes/arm_casos.json`: teste do recorte do `.arm` no navegador.
- `server.py`: servidor Flask da Web didática (seção acima).
- `tests/`: testes do servidor com o cliente de teste do Flask e o serviço real, sem abrir porta. `test_server.py` cobre a análise (WEB-03); `test_compilar_executar.py` cobre compilação com o g++ de verdade, execução com stdin, código de saída ≠ 0 e timeout (conferindo no `tasklist` que o binário não ficou vivo), downloads byte a byte, isolamento entre compilações, falhas do g++ (`GPP_NOT_FOUND`, `GPP_FAILED`), validação das rotas, os três casos do Teste 11 com `.arm` igual ao de `tests/2026_2/test11/arm/` e a atualidade de `arm_casos.json`. Na raiz: `.venv\Scripts\python.exe -B -m unittest discover -s web_didatica/tests -v` (cerca de 40 s, porque compila de verdade).
- `fixtures/`: respostas mock no formato do contrato. Ver [fixtures/README.md](fixtures/README.md).
- `tools/`: `gerar_fixtures.py` gera as fixtures a partir das fases reais de `src/` (só leitura) e `validar_fixtures.py` as confere contra o contrato; `gerar_casos_arm.py` grava `static/testes/arm_casos.json` com o esperado calculado por `extrair_arm.py` (`--conferir` só confere); `capturar_telas.py` (WEB-05) abre a interface real num Chrome ou Edge headless pelo DevTools Protocol (só biblioteca padrão, porta em 127.0.0.1, perfil temporário), percorre 17 telas acionando os botões da página, confere o oráculo de cada passo (códigos das fixtures, stdout `5`, tempo esgotado, stdout e `.arm` do T11 iguais aos de `tests/2026_2/test11/arm/`, `arm.html` 7/7) e só então grava as capturas e o `manifesto.json` em `docs/evidencias/WEB-05/`; inicia o `server.py` se ele não estiver no ar (`.venv\Scripts\python.exe -B web_didatica/tools/capturar_telas.py`). A Web não usa esses scripts.
