# MiniPar 2026.2 — Compiladores / UFAL

> **Estado:** repositório inicial de planejamento e documentação. **Não é uma implementação executável pronta.**
> **Entrega da disciplina:** 11/11/2026. **Meta de congelamento funcional:** 03/11/2026.
> **Estudo e ensaios:** 04–10/11/2026.

## Objetivo

Evoluir o compilador MiniPar 2026.1, preservando Lexer, Parser/AST, análise semântica, tabela de símbolos, TAC, geração C++ e execução nativa; implementar Fork/Join local/distribuído, testes 8–11 e uma segunda Web didática; preservar terminal e Web anterior; produzir documentação/UML e evidências.

## Leia nesta ordem

1. [`docs/00_DOCUMENTO_MESTRE_INICIAL.md`](docs/00_DOCUMENTO_MESTRE_INICIAL.md) — o enunciado consolidado, **fonte de requisitos**.
2. [`docs/01_PLANEJAMENTO_GERAL.md`](docs/01_PLANEJAMENTO_GERAL.md) — **fonte principal para como agir**, prazos, gates, responsáveis, dependências, critérios de parada e contingência.
3. [`docs/02_CONTRATOS_TECNICOS.md`](docs/02_CONTRATOS_TECNICOS.md) — API e limites de propriedade, ainda com decisões **propostas**.
4. [`AGENTS.md`](AGENTS.md) — obrigatório para pessoas e agentes antes de modificar qualquer arquivo.
5. [`docs/04_BACKLOG.md`](docs/04_BACKLOG.md) — cards internos com IDs. As GitHub Issues serão criadas **depois** de revisar os documentos.
6. [`docs/05_VALIDACAO_E_ACEITE.md`](docs/05_VALIDACAO_E_ACEITE.md) e [`docs/06_RISCOS_E_CONTINGENCIAS.md`](docs/06_RISCOS_E_CONTINGENCIAS.md).

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
├── legacy/minipar-2026.1/             # referência imutável; código AINDA NÃO incluso
├── runtime/                           # código futuro, Eixo C
├── web_didatica/                      # código futuro, Eixo B
└── tests/2026_2/                      # subpastas por teste futuramente
```

**Após importar o projeto anterior**, os arquivos ativos originais (`src/`, `main.py`, `app.py`, `menu.py`, `tests/`, `templates/` etc.) aparecem na **raiz**; uma cópia permanece em `legacy/minipar-2026.1/` como referência.

## Como começar

1. Crie um **repositório privado vazio** no GitHub para o trio; não habilite README/licença/.gitignore na criação (o pacote já contém esses arquivos).
2. Descompacte este ZIP, leia `docs/10_GUIA_SETUP_REPOSITORIO.md`, importe a base 2026.1 local com o script e confira o `git status`.
3. Publique o projeto; conceda acesso aos dois colegas.
4. Na reunião de kickoff, revise os **três contratos**. Não permita que os três agentes alterem `src/` em paralelo.
5. Execute os cards de preparação e gate G0; **depois** crie as GitHub Issues.

**Não declare testes aprovados nem código anterior importado até haver execução e evidências no novo repositório.**

## Proveniência e direitos

Base anterior: https://github.com/luizwhirl/minipar-improvement (branch `main`, publicamente acessível, sem licença declarada na consulta de 15/10/2026). A visibilidade pública **não significa** licença irrestrita de redistribuição. A cópia deve preservar a autoria e o histórico pertinente; confirme permissão de reutilização/redistribuição antes de tornar o novo repositório público. Este pacote contém apenas a estrutura/documentação e o importador, **não inclui o código original**.

## Documentos não incluídos

O PDF oficial do projeto, a BNF anterior, o exemplo Python do Teste 10 e materiais anteriores de modelagem foram incluídos em `docs/fontes/`, para consulta interna. O **código Java integral do Teste 11 e os códigos completos dos testes 8 e 9 não estão incluídos** neste pacote; também não incluí o vídeo grande. Para publicação pública, confirme antes direitos de compartilhamento das referências.
