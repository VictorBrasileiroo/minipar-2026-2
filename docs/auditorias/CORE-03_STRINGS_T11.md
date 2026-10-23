# HANDOFF — CORE-03: primitivas de strings para T11

**Responsável:** Eixo A / coordenador + Codex. **Data:** 23/10/2026.
**Branch:** `eixo-a/CORE-03-strings-t11`. **Base:** `origin/dev`, commit
`77d1eb308d7ecc44d9f7d87da9af07a4e09ffc50`. **Destino do PR:** `dev`, sem merge.
**Contrato usado:** C-T11-v1, revisão 2, §3.2–3.5 e §3.8.

## Autorização e preparação

Git foi conferido antes das alterações: branch local `dev`, sem alterações rastreadas
e com `docs.zip` não rastreado, preservado. Após `fetch origin`, a branch CORE-03
foi criada diretamente de `origin/dev`; nenhuma branch de outro eixo foi integrada.

O JSON de planejamento ainda contém `CORE-03.ready=false`, `CON-03.ready=false` e
escopo antigo de listas textuais; o cabeçalho de C-T11-v1 ainda diz proposta e a
aprovação de A está pendente na tabela. A solicitação explícita do coordenador
nesta execução autoriza implementar PRIM-01 a 06 conforme revisão 2, atualizar
BNF e testes próprios, deixar listas de strings completas para outro card e
direcionar o PR a `dev`. Essa instrução rege esta entrega. Não alteramos status,
aprovações, assinaturas ou escopo normativo do backlog/contrato por inferência.

Foram lidos `AGENTS.md`, `MEMORY.md`, planejamento, backlog, validação, contrato,
documento mestre e os módulos atuais `semantic`, `codegen`, `cpp_template`,
`parser`, `ast_nodes`, `tac` e `main.py`.

## Implementado

- **PRIM-01:** todo literal produz `std::string`; armazenamento em variável e
  atributo, reatribuição, retorno literal ou calculado em funções/métodos e UTF-8.
  Declaração local `string s;` inicia vazia, inclusive no inicializador de `for`.
- **PRIM-02:** `len` usa helper com retorno `std::ptrdiff_t`; subtrações podem
  produzir negativos, em strings e listas numéricas. Matrizes seguem aceitas.
- **PRIM-03:** `substr(s, inicio, tamanho)` retorna cópia; verifica aridade e tipos,
  inteireza, valores finitos e limites antes de converter os índices. Aceita índices
  inteiros guardados como `double`; rejeita frações, NaN, infinito e excesso de tamanho
  sem truncar. Erros descarregam stdout, diagnosticam `substr/inicio/tamanho/len` no
  stderr e terminam com saída 1.
- **PRIM-04:** `to_string` formata inteiros sem casas decimais, inclusive `double`
  e negativos, sem conversão para inteiro de faixa menor. Zero negativo vira `0`.
  Frações usam stream com `max_digits10` e locale clássico (formato documentado na BNF).
- **PRIM-05/06:** operações C++ sobre `std::string` fornecem concatenação e os seis
  comparadores por conteúdo/ordem lexicográfica. Mistura com número é rejeitada;
  tipos conhecidos no semântico, demais instanciações no G++.
- Tipos dos atributos inicializados são registrados para validar operações com strings.
  Listas textuais conhecidas são rejeitadas no semântico, como proteção temporária
  exigida por §3.4; não há implementação de listas de strings neste card.

## Arquivos alterados

- `src/codegen.py`: literais, chamadas nativas e inicialização de string declarada.
- `src/cpp_template.py`: helpers de comprimento, recorte e formatação.
- `src/semantic.py`: tipos/assinaturas das primitivas, atributos e diagnósticos.
- `BNF-grammar.md`: regras de tipos, assinaturas, erros e tradução para C++.
- `tests/2026_2/core03/verify_core03.py`: executor de provas e regressões próprias.
- Este handoff e `CORE-03_RESULTADOS.json`: evidência desta entrega.

## Como reproduzir e validar

Python da venv: **3.12.4**. G++ usado: **16.2.0 Rev6 MSYS2 UCRT64**.
Não foi usado o MinGW 6.3.0 encontrado inicialmente no PATH. Não houve instalação
de dependências, alteração persistente de PATH, portas ou serviços de rede.

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
& .\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
```

Para repetir um caso: adicionar `--case PROVA-09` (opção repetível). O executor cria
uma rodada exclusiva em `output/core03/run-*/`, copia literalmente os programas de
§3.5 e chama `main.py` em subprocesso por caso. Cada programa aceito percorre
Lexer → Parser → semântico → TAC e C++ → G++ (`-std=c++20 -O3 -pthread -lws2_32`)
→ executável atual, com stdout/stderr/exit comparados aos oráculos.
O backend continua consumindo AST, independentemente do TAC.

Compilação tem timeout interno de 120 s e externo de 150 s; execução, 10 s.
O executor não aceita só existência do C++ ou retorno 0: exige binário novo,
saída exata, stderr e código de saída corretos. Normaliza apenas CRLF para LF,
conforme contrato; preserva espaços, acentos e emojis. Negativos exigem diagnóstico,
retorno 1 do compilador e ausência de binário. Detalhes completos ficam em
`result.json` por caso e `summary.json` por rodada; os artefatos ignorados por Git
podem ser regenerados pelo comando acima.

## Resultados e regressão

Resultados finais e hashes estão em [`CORE-03_RESULTADOS.json`](CORE-03_RESULTADOS.json).
A rodada final `output/core03/run-zllwq0wb/` registrou **43 PASS, 1 KNOWN_FAIL
(defeito herdado), 0 falhas inesperadas**, com saída 0 do executor.
`py_compile` dos três módulos alterados e do executor, e `git diff --check`, também
passaram. A primeira rodada ficou preservada em `output/core03/run-gfe5lp3k/`.

| Grupo | Resultado e oráculo |
|---|---|
| PROVA-01 a 09 | PASS, stdout exato de §3.5, stderr vazio, saída 0 |
| PROVA-INT | PASS, 13 tokens e linha completa de tokens do contrato, saída 0 |
| ERR-01 a 07 | PASS, stdout `antes\n`, stderr com os quatro termos, saída 1 |
| NEG-01 a 03 | PASS, rejeição semântica com mensagem e sem executável |
| REG-LISTA | PASS, lista retornada de função, `range`/append/pop/índice/atribuição/len; `2 7 2\n-1\n` |
| REG-RECURSAO | PASS, `fat(6)` = `720` |
| REG-CLASSE | PASS, estado em listas/atributos numéricos, métodos numérico e textual recursivos, objeto alterado em função; `6 6 3:2:1:fim` |
| EXTRA-STRINGS | PASS, atributos/retornos/UTF-8/escapes/string vazia/ordenação e curto-circuito `\|\|` |
| EXTRA-NUMEROS | PASS, valores de lista e `double`, negativos, zero negativo, inteiro `1e20`, fração e índices `double` |
| EXTRA-ENTRADA | PASS, entrada adicional `(7+8)*3` processada dinamicamente |
| EXTRA-ERR-* | PASS, tamanho fracionário, NaN, infinito e índice enorme; saída 1 e diagnóstico |
| EXTRA-NEG-* | PASS, tipos/aridades, listas textuais, atributo/função/parâmetro misturado com número e índice booleano via parâmetro genérico |
| HERDADO-RETORNO-NUMERICO | **FAIL herdado confirmado**, registrado pelo executor como `KNOWN_FAIL`; dedução de retorno `int`/`double` inconsistente no G++ |

O teste próprio de classe da primeira rodada expôs a mistura `return 0`/retorno de
elemento de lista (`double`). Um programa reduzido **idêntico** foi compilado com
o compilador da base `77d1eb3`, extraído via `git show` para
`output/core03/baseline-77d1eb3/`, e com o compilador alterado. Ambos falham no G++
com `inconsistent deduction for auto return type: 'int' and then 'double'`, saída 1.
Essa falha já existia. O teste de classe compatível usa `return 0.0`, preservando os
tipos numéricos consistentes; o programa reduzido continua no executor como defeito
conhecido, sem correção fora do card. Nenhum programa de referência foi alterado.

## Pendências e limites de aceite

- **Nenhum defeito novo identificado** nos testes executados. `KNOWN_FAIL` não
  significa PASS funcional: é a reprodução esperada de um defeito herdado.
- **Regressão integral T01–T07: UNTESTED nesta entrega**, por recorte solicitado.
  A regressão pequena acima não substitui CORE-01/CORE-10 nem demonstra ausência
  universal de regressões. O card não está homologado integralmente nem marcado DONE.
- Globais em funções e passagem de lista por cópia continuam limitações herdadas de
  §3.4; não foram ampliadas nem corrigidas. Listas de strings completas continuam
  para PEND-T11-03/card próprio; as formas conhecidas agora falham com mensagem.
- `len`/`substr` contam bytes; recortes de caracteres Unicode não são oferecidos.
- **T11 completo/ARM/CPUlator: UNTESTED e responsabilidade de B.** A integração aqui
  comprovada é PROVA-INT e os moldes de uso das primitivas, não o MiniCompilador final.
- Revisão do consumidor e aprovação de outro integrante antes do merge permanecem
  pendentes. Nenhum merge realizado; backlog/contrato não foram marcados DONE/FROZEN.

## Verificação documental — MANDATORY

- Atualizados `BNF-grammar.md`, este handoff e os resultados executados. A BNF descreve
  assinaturas, tipos, unidade em bytes, erros, formatação e helpers reais, sem novos
  tokens/produções. A nota de coleções explicita a limitação do backend.
- Verificados `README.md`, `AGENTS.md`, `MEMORY.md`, `docs/00_DOCUMENTO_MESTRE_INICIAL.md`,
  `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md`, `docs/04_BACKLOG.md`,
  `docs/05_VALIDACAO_E_ACEITE.md` e `docs/templates/TEMPLATE_HANDOFF.md`.
- `AGENTS.md` **não precisa mudar**: ownership, convenções, arquitetura e fluxo de
  desenvolvimento permanecem os mesmos. `MEMORY.md` conserva a política documental.
- `README.md`/planos não detalham estas assinaturas e não precisam de mudança para
  CORE-03; estados históricos não foram reescritos. O contrato já contém exatamente
  a semântica implementada e os oráculos, então não exige CR ou alteração de interface.
- Parser/AST/lexer e TAC não mudam; diagramas/pseudocódigos dessas fases não ganham
  nós nem produções. Nenhum documento sem impacto foi alterado.

## Próximo consumidor — Eixo B

`T11-01`, `T11-02`, `T11-03` podem usar `substr(string, number, number) -> string`,
`to_string(number) -> string`, `len(string|list) -> number`, concatenação e comparações
de strings conforme revisão 2. Usar listas numéricas paralelas para posições,
tamanhos/tipos e objetos para estado, conforme PROVA-INT. Proteger leitura adiante
com curto-circuito e manter retornos numéricos consistentes em funções recursivas.

Exemplo realmente executado: PROVA-09 retorna literais e recortes, concatena o
mnemônico `SUB` e preserva os símbolos UTF-8. PROVA-INT usa índices `double`
vindos de atributos lista para recuperar lexemas. Cabe a B revisar o PR e executar
o MiniCompilador em MiniPar e os `.arm` no CPUlator; isso ainda não foi demonstrado.

**Declaração:** não alterei outro eixo nem `legacy/`; BNF e testes próprios estão
na extensão explicitamente autorizada do CORE-03. Sem funcionalidades de CORE-02,
CORE-04 ou CORE-05 e sem hardcode de entrada/saída no compilador.
