# Evidências do WEB-05 — telas da Web didática

Card `WEB-05` (Eixo B). Usadas em `docs/relatorio/WEB-05_INTERFACE_WEB_DIDATICA.md`.

As 17 capturas PNG desta pasta e o `manifesto.json` são gerados por
`web_didatica/tools/capturar_telas.py`, que abre a interface real (`server.py` + `src/service.py`)
num Chrome headless, aciona os botões da página e só grava cada captura depois de conferir o
oráculo do passo. O manifesto registra, para cada captura, o SHA-256 da imagem, o que foi
conferido e os valores lidos da tela, além do ambiente (sistema, Python, navegador, g++).

Para regenerar, na raiz do repositório:

```bash
.venv\Scripts\python.exe -B web_didatica/tools/capturar_telas.py
```

| Captura | Conteúdo | Oráculo conferido antes da captura |
|---|---|---|
| `01_tokens.png` | FIX-01, tabela de tokens | análise sem erros; 12 tokens |
| `02_ast.png` | FIX-01, AST com `VarDecl(x)` selecionado | nó presente e selecionado |
| `03_semantico.png` | FIX-01, escopos e símbolos | — (tela) |
| `04_tac.png` | FIX-01, TAC | — (texto do TAC no manifesto) |
| `05_cpp.png` | FIX-01, C++ gerado | C++ contém `int main` |
| `06_compilar_executar.png` | FIX-01 compilado e executado | g++ retorno 0; execução código 0; stdout `5` (ACE-02) |
| `07_saida_e_downloads.png` | stdout e downloads da mesma execução | idem |
| `08_erro_lexico.png` | FIX-02 | `LEX_UNKNOWN_CHAR`, igual à fixture gerada pelo compilador |
| `09_erro_sintatico.png` | FIX-03 | `SYN_EXPECTED_EXPRESSION`, igual à fixture |
| `10_erro_semantico.png` | FIX-04 | `SEM_UNDECLARED_VARIABLE`, igual à fixture |
| `11_ast_programa_maior.png` | PROG-01 (Teste 6), AST | análise sem erros |
| `12_tempo_esgotado.png` | laço infinito, limite 2 s | caixa "Tempo esgotado"; `timed_out` sim (ACE-07) |
| `13_t11_caso1.png` | T11 caso 1 | stdout idêntico a `tests/2026_2/test11/arm/caso1.stdout.txt` (22) |
| `14_t11_caso2_executar_de_novo.png` | T11 caso 2, mesmo binário | stdout idêntico a `caso2.stdout.txt` (−84); binário igual ao do caso 1 |
| `15_t11_baixar_arm.png` | `.arm` do caso 2 | SHA-256 do arquivo baixado igual ao de `tests/2026_2/test11/arm/caso2.arm` |
| `16_teste_arm_html.png` | `static/testes/arm.html` | 7/7 PASS |
| `17_modo_mock.png` | `?fonte=mock`, EXEC-01 | faixa MOCK visível |

Ids, durações e caminhos variam a cada geração; o conteúdo conferido não. As capturas foram
geradas pelo agente (Claude Code) com o script acima; pela seção "Uso de IA" do `AGENTS.md`, um
responsável humano deve repetir o passo a passo uma vez antes do aceite final.
