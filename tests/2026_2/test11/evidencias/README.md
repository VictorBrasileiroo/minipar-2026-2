# Evidências do T11-03 — execução dos `.arm` no CPUlator

Contrato: C-T11-v1 §3.7. Card `T11-03` (Eixo B).

## Ambiente

| Item | Valor |
|---|---|
| Data | 03/11/2026 |
| Simulador | CPUlator, sistema **ARMv7 generic** (`https://cpulator.01xz.net/?sys=arm`), build `cpulator.min.js?v=849` |
| Montagem (mensagem do CPUlator) | `arm-eabi-as -mfloat-abi=softfp -march=armv7-a -mcpu=cortex-a9 -mfpu=neon-fp16 --gdwarf2` |
| Ligação (mensagem do CPUlator) | `arm-eabi-ld --script build_arm.ld -e _start -u _start` |
| Navegador | Chromium 152 (navegador embutido do Claude Code desktop), Windows 11 |
| Geração dos `.arm` | `python tests/2026_2/test11/extrair_arm.py --casos tests/2026_2/test11/arm` (commit do `T11-02`), g++ 16.2.0 MSYS2 UCRT64 |

## Procedimento

Para cada arquivo, numa página recém-carregada do CPUlator (registradores ainda
não inicializados):

1. carregar o conteúdo do `.arm` no editor e conferir, na própria página, que o
   SHA-256 do texto do editor é igual ao SHA-256 do arquivo do repositório;
2. *Compile and Load* → mensagem `Compile succeeded.`; depois da carga, todos os
   registradores `r0`–`r12` e o `pc` valem `0`;
3. *Continue*, aguardar cerca de 2 s e *Stop*: o `pc` para na instrução `b .`;
4. ler os registradores e capturar a tela.

O conteúdo foi colocado no editor pela API do CodeMirror da página, e os cliques
foram dados pelo agente (Claude Code) no navegador embutido. A execução é a do
próprio CPUlator, mas foi conduzida por IA: pela seção "Uso de IA" do
`AGENTS.md`, um responsável humano deve repetir os passos acima com
*File → Open* e conferir os valores antes do aceite final.

## Resultados

| Arquivo | SHA-256 do `.arm` | `pc` final | Registrador final | Conferência intermediária | Oráculo §3.7 | Captura |
|---|---|---|---|---|---|---|
| `arm/caso1.arm` | `40adc1e1bbef231259914a951dd7ee5ce57d7177c8bc2b38d083a6c6a82476c7` | `0x24` (`b .`) | `r8` = `0x00000016` = **22** | `r2` = 6, `r4` = 42 (`0x2a`), `r7` = 20 (`0x14`) | PASS | `caso1_cpulator.jpg` |
| `arm/caso2.arm` | `1a232e2b6b98906d4dde70f08992a82b1af0f206a3c723ce0821b4c16793445e` | `0x24` (`b .`) | `r8` = `0xFFFFFFAC` = **-84** | `r3` = 56 (`0x38`), `r4` = -46 (`0xFFFFFFD2`), `r6` = -42 (`0xFFFFFFD6`) | PASS | `caso2_cpulator.jpg` |
| `arm/caso3.arm` | `40adc1e1bbef231259914a951dd7ee5ce57d7177c8bc2b38d083a6c6a82476c7` | `0x24` (`b .`) | `r8` = `0x00000016` = **22** | igual ao caso 1 | PASS | `caso3_cpulator.jpg` |
| `evidencias/extra_ldr.arm` | `5cc2bf49d48c7214c103e1db2888917be3f97069500a573c4538c48fd4a24639` | `0x1c` (`b .`) | `r6` = `0xFFFF0BB6` = **-62538** | `r0` = 1000, `r2` = 3000, `r3` = 65536, `r5` = 65538 | igual ao resultado do MiniPar | `extra_ldr_cpulator.jpg` |

Registradores completos lidos depois do *Stop* (hexadecimal):

| Arquivo | r0 | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9–r12 | cpsr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `caso1.arm` | 00000002 | 00000004 | 00000006 | 00000007 | 0000002a | 00000005 | 00000004 | 00000014 | 00000016 | 00000000 | 000001d3 |
| `caso2.arm` | 0000000a | 00000008 | 00000007 | 00000038 | ffffffd2 | 00000004 | ffffffd6 | 00000002 | ffffffac | 00000000 | 000001d3 |
| `caso3.arm` | 00000002 | 00000004 | 00000006 | 00000007 | 0000002a | 00000005 | 00000004 | 00000014 | 00000016 | 00000000 | 000001d3 |
| `extra_ldr.arm` | 000003e8 | 00000003 | 00000bb8 | 00010000 | 00000002 | 00010002 | ffff0bb6 | 00000000 | 00000000 | 00000000 | 000001d3 |

O stdout completo da execução MiniPar que gerou cada arquivo está em
`arm/casoN.stdout.txt` e `evidencias/extra_ldr.stdout.txt` (entrada
`1000*3-(65536+2)`, que exercita o `LDR rN, =k` de C-T11-v1 §3.6 item 4). Nesse
caso extra o montador codificou `=1000` e `=65536` como imediatos, porque os
dois cabem num imediato rotacionado de 8 bits (8 instruções, 32 bytes, sem
literal pool); o resultado não muda.

## Capturas

SHA-256 das imagens (JPEG 800×600 do painel do navegador):

| Arquivo | SHA-256 | Visão |
|---|---|---|
| `caso1_cpulator.jpg` | `55beb0b23f8388133560095d86c0c1b929b910f1a26589acade7007cc8c6dc3b` | Disassembly com o código-fonte, linha `b 0x24` destacada no `pc`, registradores e mensagens |
| `caso2_cpulator.jpg` | `b3f65379563ca7c95f4c328ab62d253a8c540997b3f18ece69533073b59ad58f` | Editor com o `.arm`, registradores e mensagens |
| `caso3_cpulator.jpg` | `59505a93134e690f5f309ea1be186caae833a280700952e8e7632da60fc50931` | Editor com o `.arm`, registradores e mensagens |
| `extra_ldr_cpulator.jpg` | `15b9982af7b393d720712db612639403026470816e2489c2491b099b6d981200` | Editor com o `.arm`, registradores e mensagens |

## Pendências

- **PEND-T11-04 (C-T11-v1 §3.9):** a metade do CPUlator está feita: o `caso2.arm`
  dá `r8` = -84 e os intermediários de §3.7. Falta rodar o Java do professor uma
  vez no caso 2; não há JDK nesta máquina, e instalar um está fora da regra 9 do
  `AGENTS.md` sem autorização.
- Conferência humana da execução no CPUlator (ver Procedimento).
