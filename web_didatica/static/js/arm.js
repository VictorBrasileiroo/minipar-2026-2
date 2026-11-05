// Recorte do .arm do Teste 11 no navegador (WEB-04), C-WEB-v1 §1.7 e C-T11-v1 §3.6 item 2.
// Mesmas regras de tests/2026_2/test11/extrair_arm.py: copia literalmente as linhas entre a linha
// de título terminada em "Assembly ARMv7 (CPUlator):" e a primeira linha vazia seguinte, depois de
// remover o \r do fim de cada linha. Não analisa, completa nem reescreve o Assembly.
export const SUFIXO_TITULO = "Assembly ARMv7 (CPUlator):";

export class ErroExtracao extends Error {}

export function extrairArm(stdout) {
  const linhas = stdout.split("\n").map((l) => (l.endsWith("\r") ? l.slice(0, -1) : l));
  const titulos = [];
  linhas.forEach((l, i) => { if (l.endsWith(SUFIXO_TITULO)) titulos.push(i); });
  if (!titulos.length) throw new ErroExtracao("título do Assembly ausente");
  if (titulos.length > 1) throw new ErroExtracao("título do Assembly repetido");
  const bloco = [];
  let fechado = false;
  for (const linha of linhas.slice(titulos[0] + 1)) {
    if (linha === "") { fechado = true; break; }
    bloco.push(linha);
  }
  if (!fechado) throw new ErroExtracao("bloco do Assembly sem a linha vazia que o fecha");
  if (!bloco.length) throw new ErroExtracao("bloco do Assembly vazio");
  if (bloco[0] !== ".global _start") throw new ErroExtracao("bloco do Assembly não começa com .global _start");
  // Como o arquivo de referência: uma instrução por linha e uma linha em branco no fim.
  return bloco.join("\n") + "\n\n";
}

// Recorta o .arm de uma execução (minipar.execute.v1). Recusa stdout truncado (§1.7 item 3).
export function armDaExecucao(execucao) {
  if (execucao.stdout_truncated) {
    throw new ErroExtracao("o stdout foi truncado no limite de 1 MB; o bloco pode estar incompleto");
  }
  return { texto: extrairArm(execucao.stdout), nome: `t11_${execucao.artifact_id.slice(0, 8)}.arm` };
}
