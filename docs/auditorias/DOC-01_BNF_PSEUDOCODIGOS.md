# HANDOFF — DOC-01

**Responsável:** José Riquelme (Eixo B) | **Branch/PR:** `eixo-b/DOC-01-bnf-pseudocodigos` → `dev` | **Data:** 05/11/2026 | **Contrato usado:** C-FJ-v1 §2.2 (FROZEN), C-WEB-v1 §1.5, C-T11-v1 §3.3–3.4, CR-CORE05-FJ-DECISOES e CR-CORE08-DIAGNOSTICOS (propostas, não ratificadas)

Base: `origin/dev` em `f54c75e`. Dependência do card: `CORE-06` integrado (PR #17).

### Implementado

- [`docs/12_BNF_MINIPAR_2026_2.md`](../12_BNF_MINIPAR_2026_2.md): BNF consolidada **derivada do código**
  (`src/lexer.py`, `src/parser.py`), com léxico completo, gramática sintática em bloco único,
  precedência, Fork/Join (sintaxe, FJ-SEM-01…08 com origem e estado de ratificação,
  resumo da tradução TAC/C++), restrições de contexto do semântico, rastreabilidade
  produção → método → sonda e a lista de divergências da `BNF-grammar.md` da raiz.
- [`docs/13_PSEUDOCODIGOS_NUCLEO.md`](../13_PSEUDOCODIGOS_NUCLEO.md): pseudocódigos do pipeline,
  Lexer, Parser (descida recursiva e erro), tabela de símbolos, analisador semântico e
  tratamento de erros, regras de Fork/Join (incluindo especialização e isolamento
  transitivo) e tradução TAC de `fork`/`join`/`par`, cada bloco ligado à função real.
- [`DOC-01_sondas_bnf.py`](DOC-01_sondas_bnf.py): 114 sondas executáveis que confrontam o
  documento com o código (léxico, sintaxe, precedência, semântico, Fork/Join, tabela de
  símbolos e os 16 programas `.minipar` do repositório).
- [`DOC-01_RESULTADOS.json`](DOC-01_RESULTADOS.json): saída registrada das sondas.

Nenhuma produção nova foi inventada; nenhum arquivo de `src/` foi alterado.

### Arquivos alterados

- `docs/12_BNF_MINIPAR_2026_2.md` (novo)
- `docs/13_PSEUDOCODIGOS_NUCLEO.md` (novo)
- `docs/auditorias/DOC-01_BNF_PSEUDOCODIGOS.md` (novo, este handoff)
- `docs/auditorias/DOC-01_sondas_bnf.py` (novo)
- `docs/auditorias/DOC-01_RESULTADOS.json` (novo)

Todos dentro de `docs/`, único caminho autorizado pelo card.

### Verificação documental — MANDATORY

- **Documentos verificados e impacto identificado:**
  - `BNF-grammar.md` (raiz, Eixo A): impactado — 7 divergências com o código (DIV-01 a DIV-07,
    seção 8 da BNF nova). **Não editado** por estar fora de `docs/` e pertencer ao A; fica
    como pedido de correção ao A neste PR.
  - `docs/02_CONTRATOS_TECNICOS.md` §2.2 (C-FJ-v1): conferido contra o semântico; regras
    01–06 conferem. Sem alteração (arquivo compartilhado, contrato congelado).
  - `docs/CR-CORE05-FJ-DECISOES.md` e `docs/CR-CORE08-DIAGNOSTICOS.md`: usados para
    marcar FJ-SEM-07/08 e os códigos `SEM_FJ_*`, `SEM_RESERVED_NAME`,
    `SEM_INHERITANCE_CYCLE`, `SEM_UNSUPPORTED_FEATURE` como **propostos**. Sem alteração.
  - `docs/auditorias/CORE-06_TAC_FORK_JOIN.md` e `CORE-07_BACKEND_RUNTIME.md`: referenciados
    para a tradução; sem alteração.
  - `docs/11_CHECKLIST_DE_ENTREGA.md` (itens BNF e pseudocódigos): **não marcados**; só
    devem ser marcados após a aprovação de exatidão do A.
  - `README.md`: não lista documentos além de 00–06; um link para 12/13 é útil, mas o
    arquivo é compartilhado (coordenador autoriza). Deixado como sugestão.
  - `planning/cards.json` e `docs/04_BACKLOG.md`: estado do card não alterado (arquivo
    compartilhado; atualização de backlog é do C via `DOC-03`).
- **Documentos atualizados nesta mesma entrega/PR:** os cinco arquivos novos acima.
- **`AGENTS.md`:** revisado; **não precisa mudar**. O card não altera regras,
  convenções, arquitetura nem fluxo; só acrescenta documentação de referência.

### Interface exposta ao consumidor

Sem interface de código. Consumidores documentais:
- `DOC-04` (relatório): seções "Gramática" e "Pseudocódigos" podem citar 12 e 13.
- Eixo A: lista DIV-01…07 para corrigir a `BNF-grammar.md`.

### Como reproduzir e validar

Comandos (raiz do repositório, Python 3.14.7, Windows 11):

```bash
python docs/auditorias/DOC-01_sondas_bnf.py
python docs/auditorias/DOC-01_sondas_bnf.py --json docs/auditorias/DOC-01_RESULTADOS.json
```

Entradas: os trechos MiniPar embutidos nas listas `LEX_CASES`, `SYN_CASES`,
`PREC_CASES`, `SEM_CASES`, `SYMTAB_CASES` do script e os 16 arquivos `tests/**/*.minipar`.

Saídas observadas:

```text
DOC-01 sondas: 114/114 PASS
```

| Grupo | Casos | O que confere |
|---|---|---|
| lexer | 14 | Tokens e códigos `LEX_*` exatos (palavras FJ, `TYPE`, `1.`, `.5`, escapes, Unicode, `&`/`\|` isolados) |
| parser | 40 | Aceita/rejeita cada produção e o código `SYN_*` esperado |
| precedence | 7 | Forma parentizada da AST (inclui `on` consumindo `d + 1`) |
| semantic | 36 | 20 regras comuns + 16 de Fork/Join: resultado e presença do código (`FJ-SEM-01`…`08`) |
| symbols | 1 | `kind`, `type` e kind do escopo publicados para classe, atributo, método, parâmetro, função, variável e iterador |
| corpus | 16 | Todos os programas reais do repositório passam pelo Lexer/Parser |

**Controle negativo** (prova que as sondas podem falhar): alterando em memória quatro
expectativas — SYN-08 com `;` obrigatório (como diz a BNF da raiz), LEX-13 com letra
só ASCII (idem), PREC-03 com associatividade errada e FJ-15 exigindo FJ-SEM-08 — o script
relatou `110/114 PASS`, quatro `FAIL` e exit 1. Versão mínima reproduzível, só com a
mutação de SYN-08 (saída observada: `FAIL SYN-08`, `113/114 PASS`, retorno 1):

```bash
python -c "import importlib.util as u; s=u.spec_from_file_location('s','docs/auditorias/DOC-01_sondas_bnf.py'); m=u.module_from_spec(s); s.loader.exec_module(m); m.SYN_CASES=[c if c[0]!='SYN-08' else (*c[:3],'reject','SYN_EXPECTED_TOKEN') for c in m.SYN_CASES]; print(m.main(['x']))"
```

Oráculo: comportamento observado de `Lexer`, `Parser` e `SemanticAnalyzer` em `f54c75e`;
cada caso declara a expectativa escrita nos documentos 12/13.

**Status:** `PARTIAL`. A consistência documento ↔ implementação foi demonstrada
(114/114, com controle negativo), mas o critério de aceite do card exige que o **Eixo A
aprove a exatidão**; essa aprovação ainda não existe. As sondas cobrem amostras das
produções e regras, não uma prova exaustiva da gramática.

### Regressões executadas

- Nenhum código de produção mudou; não há regressão funcional a executar.
- Os 16 programas `.minipar` do repositório continuam aceitos pelo Lexer/Parser (grupo corpus).

### Pendências, riscos e limitações

- **Aprovação de exatidão pelo A** (critério de aceite) — pendente.
- **DIV-01…07** na `BNF-grammar.md` da raiz — correção cabe ao A; todas são de
  documentação, nenhuma muda o que o compilador aceita.
- FJ-SEM-07/08 e os códigos `SEM_FJ_*` continuam **propostos** (CR-CORE05/CR-CORE08);
  se a ratificação mudar nomes ou regras, atualizar as seções 5.2/6 da BNF e a seção 5
  dos pseudocódigos.
- Os pseudocódigos simplificam o cache de especialização e as assinaturas provisórias
  do semântico; a regra observável (quando há erro e qual) foi mantida.
- Os documentos refletem `f54c75e`. Mudanças posteriores em `src/lexer.py`,
  `src/parser.py` ou `src/semantic.py` exigem reexecutar as sondas.

### Próxima pessoa/card dependente

- Eixo A: revisar 12/13, aprovar exatidão e decidir sobre DIV-01…07.
- `DOC-04` (B): usar 12/13 nas seções de gramática e pseudocódigos do relatório.
- Coordenação: autorizar (ou não) o link para 12/13 no `README.md`.

**Declaração:** não alterei outro eixo nem `legacy/` sem autorização de CR.
