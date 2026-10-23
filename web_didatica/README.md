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
- **Diagnósticos**: clicar num diagnóstico abre a fase dele e seleciona a linha no editor.
- **Trilha de fases** Tokens → AST → Semântico → TAC → C++ → Compilar e executar, com o status de cada uma (`ok`, `error`, `skipped`). Cada fase tem âncora própria (`#tokens`, `#ast`, `#semantico`, `#tac`, `#cpp`, `#executar`), e as setas do teclado trocam de fase.
- **Painéis**: tabela de tokens; AST desenhada da fixture (papel no pai, atributos e linha de cada nó, marcadores de truncamento); escopos aninhados com os símbolos de cada um; TAC e C++ com numeração; resultado do g++ e da execução (no exemplo EXEC-01).
- Fase `skipped` explica o motivo (`previous_phase_failed` ou `not_requested`) em vez de ficar vazia.

## Organização

- `static/index.html`, `static/css/app.css`, `static/js/app.js`: interface.
- `static/js/fonte_mock.js`: única parte que sabe de onde vêm os dados. Na integração, uma fonte que chama `/api/v1/…` substitui esta, devolvendo o mesmo formato.
- `fixtures/`: respostas mock no formato do contrato. Ver [fixtures/README.md](fixtures/README.md).
- `tools/`: `gerar_fixtures.py` gera as fixtures a partir das fases reais de `src/` (só leitura) e `validar_fixtures.py` as confere contra o contrato. A Web não usa esses scripts.
