# RUN-06 — Reprodução do deploy em dois computadores

**Card:** `RUN-06` · **Eixo:** C (Erasmo) · **Data desta versão:** 05/11/2026
**Critério de aceite:** outro integrante reproduz a execução em dois PCs **seguindo só as instruções**; logs sem dados pessoais.
**Instruções avaliadas:** [`runtime/README.md` §7](../../runtime/README.md#7-deploy-em-dois-computadores) (deploy), §4 (topologia), §5 (protocolo e erros) e §6 (testes).

## 1. Estado

| Item | Status | Observação |
|---|---|---|
| README do runtime com protocolo, topologia, deploy, testes e problemas comuns | **pronto para revisão** | `runtime/README.md` §4–§7 |
| Ferramenta para mascarar logs | **PASS** | `runtime/tools/mascarar_log.py`, conferida com um log sintético: IPs `192.168.x.N`, hostname trocado, pasta do usuário trocada por `<home>`; recusa sobrescrever a entrada |
| **Reprodução por outro integrante** | **PENDENTE** | Ninguém além do autor executou o roteiro até 05/11. Não há prova sem essa execução (AGENTS regra 6) |
| Logs dos dois lados anexados | **PENDENTE** | Fecha também a lacuna do `RUN-03`, que só anexou o log do worker |

O card fica `IN_PROGRESS` até a seção 3 estar preenchida com uma execução real.

## 2. Roteiro da reprodução

Quem reproduz **não é o autor do README** e opera a máquina A (coordenador). A máquina B (workers) pode ser de qualquer integrante.

1. Seguir o `runtime/README.md` §7.1 a §7.5 **sem ajuda verbal**. Cada passo que precisar de explicação fora do README é um defeito do README: registre na seção 4.
2. Rodar o §7.6 (queda de worker).
3. Opcional, com tempo: `run_bench.py --destinos-rede` (bench README §4), que preenche o cenário `par_rede` do `RUN-05`.
4. Mascarar os logs (§7.7) e anexar em `docs/evidencias/RUN-06/`.

## 3. Registro da execução

*A preencher por quem reproduziu. Não inventar valores: campo sem dado fica "não registrado".*

| Campo | Máquina A (coordenador) | Máquina B (workers) |
|---|---|---|
| Data/hora | | |
| Quem operou | | |
| Hostname (apelido) | `pc-A` | `pc-B` |
| IP mascarado (`192.168.x.N`) | | |
| SO e G++ | | |
| Commit (`git rev-parse --short HEAD`) | | |
| SHA-256 do `teste8.exe` (16 primeiros) | | |

| # | Verificação | Status | Evidência |
|---|---|---|---|
| 1 | Os 4 workers de B escutam no IP de B (`escutando em <IP-de-B>:720N`) | | log de B |
| 2 | Cada worker aceita conexão vinda do IP de A | | log de B (`conexao de <IP-de-A>:... aceita`) |
| 3 | Coordenador em A: `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0` | | `coordenador_A.txt` |
| 4 | `SOMA_NOTAS` do `par` remoto igual à do `seq` em A | | `coordenador_A.txt` e saída do `seq` |
| 5 | Cada worker registra 1 `TASK` e 1 `RESULT ok` de `avaliar_lote` | | log de B |
| 6 | Queda de um worker → `WORKER_LOST`, exit 1, sem travar | | `coordenador_A_queda.txt` |
| 7 | Logs anexados sem IP completo, hostname real ou pasta de usuário | | saída do `mascarar_log.py` (exit 0) |
| 8 | Regra de firewall removida no fim | | declaração de quem operou |

## 4. Ajustes no README apontados na reprodução

| Passo | Problema encontrado | Correção feita |
|---|---|---|
| | | |

## 5. Anexos

- `RUN-06/coordenador_A.txt` (pendente)
- `RUN-06/coordenador_A_queda.txt` (pendente)
- `RUN-06/worker_7201_B.log` … `worker_7204_B.log` (pendente)
