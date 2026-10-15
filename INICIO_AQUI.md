# Comece por aqui — MiniPar 2026.2

**Este é o pacote inicial de planejamento e estrutura, não o compilador 2026.2 pronto.**

## Três decisões já tomadas

- Repositório novo do trio (preferencialmente **privado**, ao menos até verificar atribuição/licenças).
- Versão anterior preservada em `legacy/minipar-2026.1/`; desenvolvimento ativo ocorre na raiz, com uma cópia separada do código anterior.
- Eixo A = coordenador, dono do núcleo. Eixos B (Web + Teste 11) e C (runtime + Testes 8–10) aguardam nomeação; com suporte documental/QA redistribuído para caber no limite de 3h/dia do A.

## Primeiros passos, em ordem

1. Leia `README.md` e **`docs/01_PLANEJAMENTO_GERAL.md`**. Este último é a base principal de **como agir**.
2. Leia `docs/02_CONTRATOS_TECNICOS.md` e `AGENTS.md` **antes de iniciar qualquer Codex**.
3. Abra `docs/10_GUIA_SETUP_REPOSITORIO.md`. Baixe/clone o MiniPar 2026.1 no seu PC.
4. Na pasta do projeto recém-extraída, rode `python scripts/importar_base.py --source CAMINHO_DA_BASE` (simulação) e depois acrescente `--apply` (importação).
5. Execute `python scripts/validar_planejamento.py`, confirme 43 cards sem erro.
6. Crie um repositório vazio **privado** no GitHub, `git init`, `git add .`, commit e push de acordo com o guia.
7. Faça o kickoff para definir B/C, capacidade, ambiente de execução e aprovar os contratos **C-FJ, C-WEB e C-T11**.
8. Revise `docs/04_BACKLOG.md`/`planning/cards.json`. **Só na próxima etapa** criaremos as Issues e o board.

## Conteúdo de referência já incluído

- Enunciado 2026.2 atualizado (`docs/fontes/Enunciado_MiniPar_2026_2_Atualizado.pdf`).
- BNF de referência 2026.1, material de UML/componentes, relatório antigo e script Python do Teste 10, todos em `docs/fontes/`.
- Resultados **resumidos** das duas auditorias do Codex em `docs/08_ESTADO_DA_BASE_2026_1.md`.

## Itens que ainda precisam ser importados ou anexados

- **Código MiniPar 2026.1 completo** (este pacote tem importador, não o código antigo). Fonte: <https://github.com/luizwhirl/minipar-improvement>.
- Código Java integral do Teste 11 e fontes Python dos Testes 8/9, se a equipe tiver os arquivos originais.
- Protótipos e logs originais das auditorias no PC que executou Codex, se forem reutilizados.
- Vídeo do professor: não incluído por tamanho; análise de seu conteúdo ainda está pendente.

Não confunda exemplos, mocks, relatórios e protótipos com funcionalidades integradas. Critérios de aceite reais em `docs/05_VALIDACAO_E_ACEITE.md`.
