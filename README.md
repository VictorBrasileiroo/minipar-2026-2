# MiniPar 2026.2 — Compiladores / UFAL

> **Estado verificado em 16/10/2026 (SET-01):** base 2026.1 presente na raiz ativa e preservada em `legacy/`, junto ao planejamento 2026.2. A execução funcional ainda depende da validação de ambiente/baseline; não está homologada neste card.
> **Entrega da disciplina:** 11/11/2026. **Meta de congelamento funcional:** 03/11/2026.
> **Estudo e ensaios:** 04–10/11/2026.

## Objetivo

Evoluir o compilador MiniPar 2026.1, preservando Lexer, Parser/AST, análise semântica, tabela de símbolos, TAC, geração C++ e execução nativa; implementar Fork/Join local/distribuído, testes 8–11 e uma segunda Web didática; preservar terminal e Web anterior; produzir documentação/UML e evidências.

## Leia nesta ordem

1. [`docs/00_DOCUMENTO_MESTRE_INICIAL.md`](docs/00_DOCUMENTO_MESTRE_INICIAL.md) — o enunciado consolidado, **fonte de requisitos**.
2. [`docs/01_PLANEJAMENTO_GERAL.md`](docs/01_PLANEJAMENTO_GERAL.md) — **fonte principal para como agir**, prazos, gates, responsáveis, dependências, critérios de parada e contingência.
3. [`docs/02_CONTRATOS_TECNICOS.md`](docs/02_CONTRATOS_TECNICOS.md) — API e limites de propriedade, ainda com decisões **propostas**.
4. [`AGENTS.md`](AGENTS.md) e [`MEMORY.md`](MEMORY.md), quando existir — leitura obrigatória antes de iniciar qualquer tarefa; `AGENTS.md` rege pessoas e agentes antes de modificar qualquer arquivo.
5. [`docs/04_BACKLOG.md`](docs/04_BACKLOG.md) — cards internos com IDs. As GitHub Issues serão criadas **depois** de revisar os documentos.
6. [`docs/05_VALIDACAO_E_ACEITE.md`](docs/05_VALIDACAO_E_ACEITE.md) e [`docs/06_RISCOS_E_CONTINGENCIAS.md`](docs/06_RISCOS_E_CONTINGENCIAS.md).

**MANDATORY:** toda implementação, correção, refatoração ou alteração relevante exige verificar a documentação impactada e a necessidade de atualizar `AGENTS.md`, conforme a [regra 11](AGENTS.md). As atualizações necessárias integram a mesma entrega/PR; a dispensa de atualização deve ser justificada explicitamente no resumo final.

## Papéis

- **Eixo A — Núcleo:** responsável definido: coordenador do trio. Responsável por Lexer, Parser, AST, semântico, TAC, backend C++ e integração do núcleo com o runtime. Disponibilidade-alvo: **até 3h/dia**.
- **Eixo B — Web didática + Teste 11:** pessoa ainda a definir.
- **Eixo C — Runtime, comunicação distribuída + Testes 8–10:** pessoa ainda a definir.

O domínio de código é definido em [`AGENTS.md`](AGENTS.md). Mudanças nos contratos exigem aprovação antes da implementação.

## Organização do repositório

```text
MINIPAR_2026_2/
├── README.md
├── AGENTS.md
├── MEMORY.md
├── .gitignore
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── 00_DOCUMENTO_MESTRE_INICIAL.md
│   ├── 01_PLANEJAMENTO_GERAL.md
│   ├── 02_CONTRATOS_TECNICOS.md
│   ├── 03_DECISOES.md
│   ├── 04_BACKLOG.md
│   ├── 05_VALIDACAO_E_ACEITE.md
│   ├── 06_RISCOS_E_CONTINGENCIAS.md
│   ├── 07_GUIA_CODEX_E_GIT.md
│   ├── 08_ESTADO_DA_BASE_2026_1.md
│   ├── 09_ESTUDO_APRESENTACAO.md
│   ├── 10_GUIA_SETUP_REPOSITORIO.md
│   ├── 11_CHECKLIST_DE_ENTREGA.md
│   └── auditorias/, templates/, fontes/
├── planning/cards.json                # backlog estruturado; NÃO são GitHub Issues ainda
├── scripts/
│   ├── importar_base.py               # importa cópia local da base antiga
│   └── validar_planejamento.py
├── src/, main.py, app.py, menu.py     # compilador e interfaces herdados ativos
├── templates/, static/, tests/        # Web anterior, testes e resultados esperados
├── legacy/minipar-2026.1/             # referência imutável; 36 arquivos históricos
├── runtime/                           # código futuro, Eixo C
├── web_didatica/                      # código futuro, Eixo B
└── tests/2026_2/                      # subpastas por teste futuramente
```

Os arquivos ativos originais já estão na **raiz**. A comparação SHA-256 do SET-01 encontrou **34 dos 36 arquivos históricos idênticos**, diferenças esperadas em `README.md` e `.gitignore`, e nenhum correspondente ausente. Evidências e comandos reproduzíveis em [`docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md`](docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md). Não repetir a importação neste workspace.

## Como começar

1. Confira branch (a padrão é `dev`; PRs vão para `dev` e exigem ao menos um revisor que não seja o autor), `git status` e a auditoria SET-01: este workspace já tem Git inicializado e remoto configurado. Não reinicialize o repositório nem importe a base novamente.
2. Leia `docs/10_GUIA_SETUP_REPOSITORIO.md`. As instruções de criação/importação são para uma estrutura nova ainda sem a base; neste workspace o próximo consumidor é SET-02, após revisão/integração do SET-01.
3. Confira acesso dos colegas e permissões no card SET-03; não foram validados no SET-01.
4. Na reunião de kickoff, revise os **três contratos**. Não permita que os três agentes alterem `src/` em paralelo.
5. Execute os cards de preparação e gate G0; **depois** crie as GitHub Issues.

**Não declare testes aprovados nem código anterior importado até haver execução e evidências no novo repositório.**

## Validação local do CORE-02

O T07 ativo usa pilha dinâmica com `append`/`pop`. Seu TAC percorre a AST pelo gerador genérico, sem selecionar saída pelo nome da função. Implementação e evidências locais de 23/10/2026: [`CORE-02_TAC_QUICKSORT.md`](docs/auditorias/CORE-02_TAC_QUICKSORT.md). A entrega aguarda revisão humana; não altera o estado do card.

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T07
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T06
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
```

Os validadores nativos usam `CXX`, o G++ UCRT64 local ou `--cxx CAMINHO_GPP`, sem alterar o PATH do sistema. Os artefatos e logs ficam em `output/`, ignorado pelo Git. O `.expected.tac` do T07 permanece como referência histórica; igualdade textual não é o critério de aceite.

## Proveniência e direitos

Base anterior informada no README e na BNF históricos: <https://github.com/luizwhirl/minipar-improvement>. Créditos preservados: Emanuele Vitória de Jesus Lima ([Manu-Vii](https://github.com/Manu-Vii)), José Lucas de Oliveira Quintela ([lucasqtl](https://github.com/lucasqtl)) e Luiz Miguel de Melo Bomfim ([luizwhirl](https://github.com/luizwhirl)).

O código herdado está incluído neste workspace. O **commit de origem não foi comprovado**: não há manifesto `ORIGEM_SNAPSHOT.json` nem histórico Git próprio no snapshot. O HEAD auditado do repositório **2026.2** é `a37c168cd60c13ab083782877f6c56b0c588bd1b`, não o commit original. Não foram encontrados arquivo de licença ou autorização de redistribuição local; a consulta anterior de 15/10 relatava ausência de licença declarada. A verificação online desta execução não obteve a página. Preservar autoria e confirmar autorização antes de publicação pública; a situação de direitos continua pendente.

## Documentos não incluídos

O PDF oficial do projeto, a BNF anterior, o exemplo Python do Teste 10 e materiais anteriores de modelagem foram incluídos em `docs/fontes/`, para consulta interna. O **código Java integral do Teste 11 e os códigos completos dos testes 8 e 9 não estão incluídos** neste pacote; também não incluí o vídeo grande. Para publicação pública, confirme antes direitos de compartilhamento das referências.
