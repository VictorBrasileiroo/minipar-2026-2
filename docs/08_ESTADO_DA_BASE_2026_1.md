# Estado observado da base 2026.1 — síntese das auditorias Codex 15/10/2026

**Natureza:** evidência trazida pelo usuário do Codex. Os logs/scripts originais **não foram embutidos** neste repositório inicial. NÃO declarar essas provas como executadas aqui. Rodadas ocorreram em diretórios externos `_triagem_2026-10-15/` e `_rodada2_2026-10-15/` no computador local.

## 1. Pipeline real identificado

```text
MiniPar → Lexer → Parser/AST → semântico
                            ├─ AST → TAC
                            └─ AST → C++ → G++ → executável
```

TAC e código C++ são produzidos em **ramos independentes**; o gerador C++ não consome TAC.

## 2. Auditoria 1

- Sete programas foram aceitos pelo Lexer/Parser e analisador semântico.
- Todos falharam no `g++ -std=c++20`, porque toolchain local era GCC 6.3.0.
- Sem executáveis, não havia prova de correção de T01–T07 nessa rodada.
- `src/tac.py` retorna `EXPECTED_QUICKSORT_TAC` somente ao ver nome `quicksort_iterativo`, independentemente do corpo (reproduzido por mutação em memória).
- `par` cria threads com captura por referência; no TAC seq e par se linearizam de modo semelhante.
- `MiniParChannel` usa socket simples sem framing/leituras completas; test_orchestrator usa JSON local e loopback, sem comprovar máquinas distintas.
- Web Flask tem editor/TAC/C++/execução, mas não fornece API didática por fase. `app.py` depende de `python` resolvido no PATH, Flask ausente no ambiente de teste, e tem inconsistências de binário por OS.
- Strings/listas heterogêneas, `substr`, `to_string` têm problemas; Teste 11 requer correção.

## 3. Auditoria 2 — provas práticas em CÓPIA ISOLADA

- Os sete testes **compilaram e iniciaram** com uma adaptação experimental para C++14 (não homologação do projeto C++20 intacto).
- **6/7** terminaram normalmente ao menos uma vez; T07 teve erro de acesso à memória (índice fora de vetor), reproduzido com `_GLIBCXX_DEBUG`.
- T01: entrada `+`, `2`, `3` gerou resultado 5, mas houve timeout inicial; estabilidade não aprovada.
- T02: fatorial de 5→120 e Fibonacci `0,1,1,2,3,5,8,13` coerentes.
- T03: convergência do neurônio observada (iteração 51; pesos/saída próximos ao esperado).
- T04: XOR classificou corretamente, porém números divergiram do arquivo esperado (maior diferença ≈0.01507); tolerância oficial não estabelecida.
- T05: 12 produtos coincidiram para histórico usado; arquivo esperado não especificava entrada, então não há aprovação geral.
- T06: ordenação de `10 -3 -40 80 70 -100` resultou em `[-100,-40,-3,10,70,80]`.
- T07: falha de acesso ao vetor; aumentar pilha na cópia experimental permitiu ordenar `[5,12,33,61,98]`; TAC hardcoded segue pendente.
- Strings: correções pontuais em `codegen.py` e `semantic.py` permitiram tipos string, `.substr`, `to_string` e listas homogêneas textuais na cópia de teste. Tipagem geral não resolvida.
- Teste 11: programa **MiniPar real** processou `2+4*7` e 10 casos, produziu tokens/AST em vetores, TAC/ARM textuais e resultado 30; **ARM não foi executado no CPUlator**. Ainda faltam Teste 11 completo, símbolos/ARM diversos etc.
- Worker e coordenador C++ em processos separados fizeram framing e tarefas identificadas somente em `localhost`. **Não comprova integração Fork/Join de MiniPar nem dois computadores.**
- Nenhum dos 36 arquivos originais foi modificado na prova do Codex, conforme SHA-256 relatado.
- Estimativa revisada por Codex: **184–320 horas humanas com IA**, incerteza elevada; nenhuma garantia de escopo solo com 3h/dia.

## 4. Implicação para o novo projeto

A cópia experimental demonstrou **potencial**, não funcionalidades já disponíveis no novo repositório. Após importar a base, reexecutar a baseline real com toolchain atualizada e reaplicar **seletivamente** patches revisados da auditoria, sem copiar código experimental cegamente.

Os protótipos de T11 e protocolo da rodada 2 devem ser recuperados do computador original por quem os produziu e revisados por responsáveis B/C, respectivamente. Não estão contidos neste ZIP.

## 5. Limitadores atuais

Enunciado completo e código Java T11 não estavam no workspace do Codex na auditoria. Eles foram vistos na conversa de planejamento; o trio deve disponibilizar arquivos autorizados aos desenvolvedores antes de finalizar exigências ARM/distribuído. O plano registra decisões condicionais, não substitui o PDF oficial.

## 6. Referência

Repositório 2026.1 consultado: https://github.com/luizwhirl/minipar-improvement, branch main em 15/10/2026. Fonte pública sem licença declarada na consulta. Preservar créditos e checar direitos de redistribuição.
