# Comece por aqui — MiniPar 2026.2

**Este é o pacote inicial de planejamento e estrutura, não o compilador 2026.2 pronto.**

**Atualização SET-01 — 16/10/2026:** a base 2026.1 já está presente na raiz ativa e em `legacy/minipar-2026.1/`; Git e histórico já existem. Comparação SHA-256: 36 arquivos históricos, 34 idênticos, apenas `README.md`/`.gitignore` divergentes e nenhum ausente. Consulte `docs/auditorias/SET-01_VALIDACAO_ESTRUTURAL.md`. Não repetir importação ou `git init` neste workspace. Funcionamento do compilador ainda não validado neste card.

## Três decisões já tomadas

- Repositório novo do trio (preferencialmente **privado**, ao menos até verificar atribuição/licenças).
- Versão anterior preservada em `legacy/minipar-2026.1/`; desenvolvimento ativo ocorre na raiz, com uma cópia separada do código anterior.
- Eixo A = coordenador, dono do núcleo. Eixos B (Web + Teste 11) e C (runtime + Testes 8–10) aguardam nomeação; com suporte documental/QA redistribuído para caber no limite de 3h/dia do A.

## Primeiros passos, em ordem

1. Leia `README.md` e **`docs/01_PLANEJAMENTO_GERAL.md`**. Este último é a base principal de **como agir**.
2. Leia `docs/02_CONTRATOS_TECNICOS.md` e `AGENTS.md` **antes de iniciar qualquer Codex**.
3. Abra `docs/10_GUIA_SETUP_REPOSITORIO.md` e confira o estado local antes de seguir comandos de criação.
4. Neste workspace, revise a auditoria SET-01 e prepare o handoff para SET-02. Somente numa estrutura nova sem base importada cabe obter a fonte e simular a importação; conflitos devem ser inspecionados, sem forçar sobrescrita.
5. Execute `python scripts/validar_planejamento.py`, confirme 43 cards sem erro.
6. O remoto já está configurado e a **branch padrão é `dev`**: crie branches de card a partir dela e abra PRs contra ela, com pelo menos um revisor que não seja o autor. A revisão de acesso e proteção pertence ao SET-03; a visibilidade e as permissões não foram verificadas no SET-01.
7. Faça o kickoff para definir B/C, capacidade, ambiente de execução e aprovar os contratos **C-FJ, C-WEB e C-T11**.
8. Revise `docs/04_BACKLOG.md`/`planning/cards.json`. **Só na próxima etapa** criaremos as Issues e o board.

## Conteúdo de referência já incluído

- Enunciado 2026.2 atualizado (`docs/fontes/Enunciado_MiniPar_2026_2_Atualizado.pdf`).
- BNF de referência 2026.1, material de UML/componentes, relatório antigo e script Python do Teste 10, todos em `docs/fontes/`.
- Resultados **resumidos** das duas auditorias do Codex em `docs/08_ESTADO_DA_BASE_2026_1.md`.

## Itens que ainda precisam ser importados ou anexados

- **Proveniência complementar da base já copiada:** commit original e autorização de redistribuição não comprovados. Fonte informada: <https://github.com/luizwhirl/minipar-improvement>; créditos preservados no README histórico e no README da raiz.
- Código Java integral do Teste 11 e fontes Python dos Testes 8/9, se a equipe tiver os arquivos originais.
- Protótipos e logs originais das auditorias no PC que executou Codex, se forem reutilizados.
- Vídeo do professor: não incluído por tamanho; análise de seu conteúdo ainda está pendente.

Não confunda exemplos, mocks, relatórios e protótipos com funcionalidades integradas. Critérios de aceite reais em `docs/05_VALIDACAO_E_ACEITE.md`.
