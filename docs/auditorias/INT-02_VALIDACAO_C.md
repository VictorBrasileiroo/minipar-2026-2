# INT-02 — validação C do recorte de runtime

**Data:** 09/11/2026 · **Revisor:** Eixo C (Erasmo), dono de `runtime/` e dos testes T08–T10 · **Relatório validado:** [INT-02](INT-02_REGRESSAO_INTEGRAL.md), integrado no #44 (`249afaa`, aprovado por A).
**Por quê:** o card INT-02 pede que "A e C validem respectivamente compilador e runtime". A aprovação de A está no #44; este documento é a parte de C. O próprio relatório pede ao Eixo C "conferir T08–T10 e o smoke INT-01" (§8).

**Veredito:** **PASS no recorte de runtime, em loopback.** Os resultados do INT-02 para T08, T09, T10 e o smoke INT-01 se repetem número a número numa segunda máquina. A rede real continua **BLOCKED**, como o próprio INT-02 registra. Esta validação não a substitui.

## 1. Como foi executado

- Mesmo orquestrador do INT-02, só com as etapas do runtime: `.venv/Scripts/python.exe -B scripts/regressao_int02.py --only T08,T09,T10,INT-01`.
- Base: `f6ffb72` (merge do `dev` `249afaa` na branch REL-PRE), árvore limpa no início. Entre `8d07433` (base medida pelo INT-02) e `f6ffb72`, o único código diferente em `src/`, `runtime/`, `tests/`, `scripts/`, `web_didatica/` e nas interfaces é o próprio `scripts/regressao_int02.py`. Portanto o código revalidado é o mesmo que o INT-02 mediu.
- Ambiente: Windows 11 (10.0.26300), 14 CPUs lógicas, G++ 16.2.0 UCRT64 (Rev3), Python 3.12.10 e Flask 3.0.0 numa `.venv` local criada pelo [guia de setup](../10_GUIA_SETUP_REPOSITORIO.md) (`requeriments.txt`). É outra máquina que não a do INT-02 (lá, G++ Rev6).
- Resultado compacto, sem nomes de host nem caminhos pessoais: [INT-02_VALIDACAO_C_RESULTADOS.json](INT-02_VALIDACAO_C_RESULTADOS.json). Logs brutos ficam em `output/int02/run-20261109-091416/` (ignorado pelo Git).

## 2. Resultados comparados

| Etapa | INT-02 (#44) | Validação C | Confere? |
|---|---|---|---|
| T08 — 160 avaliações, 4 trabalhos | PASS, 32 checagens + 1 INFO | PASS, 32 + 1 INFO, exit 0, 9,7 s | Sim |
| T09 — T08 + Mandelbrot, 5 trabalhos | PASS 54/54 | PASS 54/54, exit 0, 11,4 s | Sim |
| T10 — T09 + Sierpinski, 6 trabalhos | PASS 126/126 | PASS 126/126, exit 0, 12,4 s | Sim |
| Smoke INT-01 (A, B, C) | PASS A, B e C | PASS: A 8/8, B 8/8, C 9/9, exit 0, 26,2 s | Sim |

Os oráculos são os dos próprios verificadores (T08 `TOTAL/UNICOS 160`, `DUPLICADOS/PERDIDOS 0`, soma igual à do oráculo Python; Mandelbrot e Sierpinski recalculados em Python). Nenhum valor esperado foi digitado nesta validação.

## 3. Conferência das afirmações sobre o runtime no relatório INT-02

- **T08–T10 e INT-01 "só no loopback":** correto. Os cenários `par` remoto usam `127.0.0.1` e não provam execução entre computadores (doc 05 §4, ADR-017).
- **INT02-02 (rede real, severidade alta para o aceite):** correto e de responsabilidade conjunta B + C. O roteiro do §5 é o `runtime/README.md` §7, o mesmo da reprodução RUN-06. O cenário `par_rede` do RUN-05 já está implementado em `tests/2026_2/bench/run_bench.py` (`--destinos-rede`); falta só executar em dois computadores.
- **INT02-03 (formato gráfico do T10, ADR-014):** correto. O cálculo do Sierpinski passa; o formato ASCII + SVG depende da decisão do coordenador.
- **INT02-04 (CORE-10 e DEF-01/02 desatualizados em `dev`):** resolvido na branch REL-PRE (#43). Lá, o CORE-10 está `DONE` (#38) e os DEF-01/02 aparecem corrigidos e aprovados (#40/#41). Entra no `dev` com o merge do #43.
- **"Nenhum defeito novo de runtime":** confirmado nesta rodada.

## 4. Encaminhamento

- **Estado do INT-02:** integrado (#44) com aceite **PARTIAL**. Validação A (#44) e validação C (este documento) registradas; falta a rede real.
- **Pendências:** rede real do INT-02 com RUN-05 `par_rede` e reprodução RUN-06 (B + C, dois computadores na mesma rede local); T04-TOL e ADR-014 dependem de decisão do coordenador.
- **Impacto de interface:** nenhum. Nenhum código, contrato ou teste alterado.
