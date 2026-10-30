"""T10-01: harness do Teste 10 (160 avaliacoes + Mandelbrot + Sierpinski).

Executar da raiz do repositorio:
    python tests/2026_2/test10/run_t10.py [--carga 2000000] [--port-base 7400]

O que faz:
  1. compila tests/2026_2/test10/teste10_dois_fractais.minipar pela CLI
     (python main.py ... teste10 -> output/teste10.exe);
  2. roda os cenarios seq, par local e par remoto (6 processos worker no
     loopback, portas port-base+1..+6, --bind 127.0.0.1);
  3. confere a saida contra um oraculo Python independente (notas por forma
     fechada da LCG, Mandelbrot e Sierpinski recalculados em Python);
  4. renderiza o Sierpinski IMPRESSO pelo programa em output/test10/sierpinski.svg
     e salva o Mandelbrot impresso em output/test10/mandelbrot.txt (so renderizacao);
  5. grava output/test10/results.json. Saida 0 somente se todas as checagens
     derem PASS; 2 = BLOCKED (backend Fork/Join ausente); 1 = alguma FAIL.

Os tempos sao medidos aqui (o MiniPar nao tem relogio) e sao apenas informativos:
outros processos podem estar disputando a CPU.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE_REL = 'tests/2026_2/test10/teste10_dois_fractais.minipar'
EXE_NAME = 'teste10'
EXE = ROOT / 'output' / f'{EXE_NAME}.exe'
OUT = ROOT / 'output' / 'test10'

NOMES = ['Professor', 'Monitor 1', 'Monitor 2', 'Monitor 3']
PALETA = ' .:-=+#%@'
PORT_MIN, PORT_MAX = 7400, 7419
RUN_TIMEOUT = 600
WORKER_FUNCS = ['avaliar_lote'] * 4 + ['mandelbrot', 'sierpinski']

PARAM_SETS = {
    'A': {'largura': 50, 'altura': 20, 'max_iter': 100, 'grau': 3},  # parecido com a referencia
    'B': {'largura': 30, 'altura': 12, 'max_iter': 60, 'grau': 2},
}

CHECKS: list[dict] = []


def check(cid: str, ok: bool, detail='') -> bool:
    CHECKS.append({'id': cid, 'status': 'PASS' if ok else 'FAIL', 'detail': detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {cid}" + (f' -- {detail}' if detail and not ok else ''))
    return ok


# ---------------------------------------------------------------- oraculo ----
A_LCG, C_LCG, M_LCG = 75, 74, 65537  # M primo => (a-1) inversivel


def lcg(s: int) -> int:
    return (s * A_LCG + C_LCG) % M_LCG


def nota_ingenua(i: int, carga: int) -> int:
    s = lcg(i + 1)
    for _ in range(carga + s % carga):
        s = lcg(s)
    return s % 101


def nota_fechada(i: int, carga: int) -> int:
    """s_n = a^n*s0 + c*(a^n - 1)/(a - 1)  (mod m), sem iterar n vezes."""
    s0 = lcg(i + 1)
    n = carga + s0 % carga
    an = pow(A_LCG, n, M_LCG)
    s = (an * s0 + C_LCG * (an - 1) * pow(A_LCG - 1, -1, M_LCG)) % M_LCG
    return s % 101


def mandelbrot_py(largura: int, altura: int, max_iter: int) -> tuple[list[str], int]:
    """Mesma conta da referencia Python. Indice da paleta por piso inteiro exato;
    devolve tambem quantas celulas divergiriam com a formula float da referencia."""
    linhas, diverg = [], 0
    for y in range(altura):
        cy = (y / altura) * 2.4 - 1.2
        linha = ''
        for x in range(largura):
            cx = (x / largura) * 3.0 - 2.0
            zx, zy, it = 0.0, 0.0, 0
            while zx * zx + zy * zy <= 4.0 and it < max_iter:
                tmp = zx * zx - zy * zy + cx
                zy = 2.0 * zx * zy + cy
                zx = tmp
                it += 1
            k = (it * (len(PALETA) - 1)) // max_iter
            if k != int((it / max_iter) * (len(PALETA) - 1)):
                diverg += 1
            linha += PALETA[k]
        linhas.append(linha)
    return linhas, diverg


def sierpinski_regra(grau: int) -> list[str]:
    n = 3 ** grau
    def vazio(i, j):
        while i or j:
            if i % 3 == 1 and j % 3 == 1:
                return True
            i, j = i // 3, j // 3
        return False
    return [''.join(' ' if vazio(i, j) else '#' for j in range(n)) for i in range(n)]


def sierpinski_recursivo(grau: int) -> list[str]:
    """Construcao independente (preenche 8 subquadrados recursivamente)."""
    n = 3 ** grau
    tela = [[' '] * n for _ in range(n)]
    def preencher(l, c, t):
        if t == 1:
            tela[l][c] = '#'
            return
        t3 = t // 3
        for a in range(3):
            for b in range(3):
                if not (a == 1 and b == 1):
                    preencher(l + a * t3, c + b * t3, t3)
    preencher(0, 0, n)
    return [''.join(r) for r in tela]


# ------------------------------------------------------------- execucao ----
def run_cmd(cmd, stdin: bytes | None = None, timeout=RUN_TIMEOUT):
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, input=stdin, capture_output=True, timeout=timeout)
    wall = time.perf_counter() - t0
    return proc.returncode, proc.stdout.decode('utf-8', 'replace').replace('\r\n', '\n'), \
        proc.stderr.decode('utf-8', 'replace').replace('\r\n', '\n'), wall


def stdin_for(modo: str, carga: int, p: dict, dests: list[str]) -> bytes:
    linhas = [modo, str(carga), str(p['largura']), str(p['altura']), str(p['max_iter']), str(p['grau'])] + dests
    return ('\n'.join(linhas) + '\n').encode('utf-8')


def parse_output(stdout: str) -> dict:
    lines = stdout.split('\n')
    res: dict = {'avaliadores': [], 'erros': []}
    try:
        res['cabecalho'] = lines[0]
        i = 1
        m = re.fullmatch(r'MODO (\S+)', lines[i]); res['modo'] = m.group(1); i += 1
        while lines[i].startswith('AVALIADOR '):
            m = re.fullmatch(r'AVALIADOR (\d+) (.+) (\d+)', lines[i])
            res['avaliadores'].append((int(m.group(1)), m.group(2), int(m.group(3)))); i += 1
        for chave in ('TOTAL', 'UNICOS', 'DUPLICADOS', 'PERDIDOS', 'SOMA_NOTAS'):
            m = re.fullmatch(chave + r' (-?\d+)', lines[i]); res[chave] = int(m.group(1)); i += 1
        m = re.fullmatch(r'=== MANDELBROT (\d+)x(\d+) max_iter=(\d+) ===', lines[i]); i += 1
        res['mandelbrot_hdr'] = tuple(int(g) for g in m.groups())
        fim = lines.index('=== FIM MANDELBROT ===', i)
        res['mandelbrot'] = lines[i:fim]; i = fim + 1
        m = re.fullmatch(r'=== SIERPINSKI grau=(\d+) ===', lines[i]); i += 1
        res['sierpinski_grau'] = int(m.group(1))
        fim = lines.index('=== FIM SIERPINSKI ===', i)
        res['sierpinski'] = lines[i:fim]; i = fim + 1
        res['resto'] = lines[i:]
    except Exception as exc:  # saida fora do contrato
        res['erros'].append(f'saida fora do contrato: {exc!r}')
    return res


def port_free(port: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


class Worker:
    def __init__(self, idx: int, port: int, log_dir: Path):
        self.idx, self.port = idx, port
        self.lines: list[tuple[float, str]] = []
        self.stdout_path = log_dir / f'worker{idx}.stdout.log'
        self._out = open(self.stdout_path, 'wb')
        self.proc = subprocess.Popen([str(EXE), '--minipar-worker', str(port), '--bind', '127.0.0.1'],
                                     cwd=ROOT, stdin=subprocess.DEVNULL, stdout=self._out,
                                     stderr=subprocess.PIPE)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for raw in self.proc.stderr:
            self.lines.append((time.monotonic(), raw.decode('utf-8', 'replace').rstrip('\r\n')))

    def wait_ready(self, limit=10.0) -> bool:
        t_end = time.monotonic() + limit
        while time.monotonic() < t_end:
            if self.proc.poll() is not None:
                return False
            with socket.socket() as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', self.port)) == 0:
                    return True
            time.sleep(0.05)
        return False

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()  # somente o PID que este harness criou
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)
        self.reader.join(timeout=5)
        self._out.close()


LOG_RE = re.compile(r'\[minipar_worker (\S+):(\d+)\] (TASK|RESULT) (\S+) fn=(\S+) (.*)')


# --------------------------------------------------------------- checagens ----
def check_scenario(name: str, stdout: str, rc: int, modo: str, p: dict, carga: int, expected: dict) -> dict:
    out = parse_output(stdout)
    check(f'{name}: exit 0', rc == 0, f'exit={rc}')
    check(f'{name}: saida no contrato', not out['erros'], '; '.join(out['erros']))
    if out['erros']:
        return out
    check(f'{name}: cabecalho', out['cabecalho'] == '=== TESTE 10: 160 avaliacoes + Mandelbrot + Sierpinski ===', out['cabecalho'])
    check(f'{name}: MODO {modo}', out['modo'] == modo, out['modo'])
    esperado_av = [(k, NOMES[k], 40) for k in range(4)]
    check(f'{name}: 4 avaliadores x 40', out['avaliadores'] == esperado_av, repr(out['avaliadores']))
    for chave, valor in (('TOTAL', 160), ('UNICOS', 160), ('DUPLICADOS', 0), ('PERDIDOS', 0),
                         ('SOMA_NOTAS', expected['soma'])):
        check(f'{name}: {chave} = {valor}', out[chave] == valor, f'obtido {out[chave]}')
    check(f'{name}: cabecalho Mandelbrot', out['mandelbrot_hdr'] == (p['largura'], p['altura'], p['max_iter']),
          repr(out['mandelbrot_hdr']))
    check(f'{name}: Mandelbrot == Python', out['mandelbrot'] == expected['mandelbrot'],
          f"{sum(a != b for a, b in zip(out['mandelbrot'], expected['mandelbrot']))} linhas diferentes")
    n = 3 ** p['grau']
    s = out['sierpinski']
    check(f'{name}: Sierpinski grau', out['sierpinski_grau'] == p['grau'], str(out['sierpinski_grau']))
    check(f'{name}: Sierpinski {n}x{n}', len(s) == n and all(len(r) == n for r in s),
          f'{len(s)} linhas, larguras {sorted({len(r) for r in s})}')
    cheias = sum(r.count('#') for r in s)
    check(f'{name}: Sierpinski com 8^grau celulas cheias (fracao (8/9)^grau)', cheias == 8 ** p['grau'],
          f'{cheias}/{n * n} cheias, esperado {8 ** p["grau"]}')
    check(f'{name}: Sierpinski == Python', s == expected['sierpinski'])
    check(f'{name}: nada depois do FIM', out['resto'] in ([], ['']), repr(out['resto'][:3]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--carga', type=int, default=2_000_000)
    ap.add_argument('--port-base', type=int, default=7400)
    args = ap.parse_args()
    if args.carga < 1:
        ap.error('--carga deve ser >= 1')
    ports = [args.port_base + i for i in range(1, 7)]
    if ports[0] < PORT_MIN or ports[-1] > PORT_MAX:
        ap.error(f'portas {ports[0]}..{ports[-1]} fora da faixa permitida {PORT_MIN}..{PORT_MAX}')
    OUT.mkdir(parents=True, exist_ok=True)

    report: dict = {
        'card': 'T10-01', 'data': datetime.now().isoformat(timespec='seconds'),
        'carga': args.carga, 'portas': ports, 'ambiente': ambiente(), 'cenarios': {},
    }

    def finish(code: int, status: str) -> int:
        report['checks'] = CHECKS
        report['status'] = status
        (OUT / 'results.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        npass = sum(c['status'] == 'PASS' for c in CHECKS)
        print(f'\n{status}: {npass}/{len(CHECKS)} checagens PASS -> {OUT / "results.json"}')
        return code

    # ---- 0. backend Fork/Join presente? ----
    codegen = (ROOT / 'src' / 'codegen.py').read_text(encoding='utf-8', errors='replace')
    if 'minipar_rt::start' not in codegen or not (ROOT / 'runtime/include/minipar_rt/minipar_rt.hpp').exists():
        print('BLOCKED: backend CORE-07 ausente')
        report['bloqueio'] = 'backend CORE-07 ausente (src/codegen.py sem minipar_rt::start ou runtime ausente)'
        return finish(2, 'BLOCKED')

    # ---- 1. compilacao pela CLI ----
    rc, so, se, wall = run_cmd([sys.executable, 'main.py', SOURCE_REL, EXE_NAME], timeout=300)
    report['compilacao'] = {'comando': f'python main.py {SOURCE_REL} {EXE_NAME}', 'exit': rc,
                            'segundos': round(wall, 2), 'stdout': so, 'stderr': se}
    if rc != 0 and ('CORE-07' in se and 'pendente' in se):
        print('BLOCKED: backend CORE-07 ausente')
        report['bloqueio'] = se.strip()
        return finish(2, 'BLOCKED')
    if not check('compilacao CLI gera output/teste10.exe', rc == 0 and EXE.exists(), se.strip()[-400:]):
        return finish(1, 'FAIL')

    # ---- 2. oraculo ----
    for carga_teste in (1, 2, 7, 50, 300):
        ok = all(nota_fechada(i, carga_teste) == nota_ingenua(i, carga_teste) for i in range(160))
        check(f'oraculo: forma fechada == laco ingenuo (carga={carga_teste})', ok)
    notas = [nota_fechada(i, args.carga) for i in range(160)]
    soma = sum(notas)
    for g in (1, 2, 3, 4):
        check(f'oraculo: Sierpinski regra == recursivo (grau={g})', sierpinski_regra(g) == sierpinski_recursivo(g))
    expected = {}
    for nome, p in PARAM_SETS.items():
        linhas, diverg = mandelbrot_py(p['largura'], p['altura'], p['max_iter'])
        expected[nome] = {'soma': soma, 'mandelbrot': linhas, 'sierpinski': sierpinski_regra(p['grau']),
                          'mandelbrot_divergencias_formula_float': diverg}
    check('oraculo: Mandelbrot A != B (fractal depende dos parametros)',
          expected['A']['mandelbrot'] != expected['B']['mandelbrot'])
    report['oraculo'] = {'soma_notas': soma, 'notas': notas,
                         'mandelbrot_divergencias_formula_float': {k: v['mandelbrot_divergencias_formula_float']
                                                                   for k, v in expected.items()}}

    # ---- 3. cenarios ----
    outs = {}
    plano = [('A', 'seq', 'seq'), ('A', 'par', 'par-local'), ('A', 'par', 'par-remoto'),
             ('B', 'seq', 'seq'), ('B', 'par', 'par-local')]
    for pset, modo, tipo in plano:
        name = f'{pset}/{tipo}'
        p = PARAM_SETS[pset]
        cen: dict = {'parametros': p, 'modo': modo, 'tipo': tipo}
        report['cenarios'][name] = cen
        if tipo == 'par-remoto':
            outs[name] = run_remote(name, p, args.carga, ports, expected[pset], cen)
            continue
        stdin = stdin_for(modo, args.carga, p, ['local'] * 6)
        try:
            rc, so, se, wall = run_cmd([str(EXE)], stdin)
        except subprocess.TimeoutExpired:
            check(f'{name}: termina antes de {RUN_TIMEOUT}s', False)
            continue
        cen.update({'exit': rc, 'segundos': round(wall, 3), 'stderr': se,
                    'stdin': stdin.decode()})
        (OUT / f"stdout_{pset}_{tipo}.txt").write_text(so, encoding='utf-8')
        print(f'--- {name}: exit={rc} tempo={wall:.3f}s')
        outs[name] = check_scenario(name, so, rc, modo, p, args.carga, expected[pset])

    # ---- 4. mesmo agregado entre cenarios ----
    def agregado(o):
        return None if o is None or o.get('erros') else (o['avaliadores'], [o[k] for k in
               ('TOTAL', 'UNICOS', 'DUPLICADOS', 'PERDIDOS', 'SOMA_NOTAS')], o['mandelbrot'], o['sierpinski'])
    for pset in PARAM_SETS:
        ags = [agregado(o) for n, o in outs.items() if n.startswith(pset + '/')]
        check(f'{pset}: mesmo agregado em todos os cenarios ({len(ags)})',
              len(ags) >= 2 and None not in ags and all(a == ags[0] for a in ags))

    # ---- 5. tempos (informativo) ----
    tempos = {n: c.get('segundos') for n, c in report['cenarios'].items()}
    info = {'tempos_s': tempos, 'aviso': 'tempo de parede medido pelo harness; ruido de outros processos; '
                                         'seq e par executam a mesma carga'}
    for alvo in ('A/par-local', 'A/par-remoto'):
        if tempos.get('A/seq') and tempos.get(alvo):
            info[f'speedup {alvo}'] = round(tempos['A/seq'] / tempos[alvo], 3)
    report['benchmark'] = info
    print('tempos (s):', json.dumps(tempos))

    # ---- 6. renderizacao (a partir do texto IMPRESSO pelo programa) ----
    fonte = next((n for n in ('A/par-remoto', 'A/par-local', 'A/seq') if outs.get(n) and not outs[n].get('erros')), None)
    if fonte:
        o = outs[fonte]
        (OUT / 'mandelbrot.txt').write_text('\n'.join(o['mandelbrot']) + '\n', encoding='utf-8')
        (OUT / 'sierpinski.svg').write_text(svg_de(o['sierpinski']), encoding='utf-8')
        report['visual'] = {'fonte': fonte, 'svg': 'output/test10/sierpinski.svg',
                            'mandelbrot': 'output/test10/mandelbrot.txt'}
        print(f'visual gerado a partir da saida de {fonte}: output/test10/sierpinski.svg, mandelbrot.txt')

    ok = all(c['status'] == 'PASS' for c in CHECKS)
    return finish(0 if ok else 1, 'PASS' if ok else 'FAIL')


def run_remote(name, p, carga, ports, expected, cen):
    livres = [port for port in ports if port_free(port)]
    if not check(f'{name}: portas {ports[0]}..{ports[-1]} livres', len(livres) == len(ports),
                 f'ocupadas: {sorted(set(ports) - set(livres))}'):
        return None
    log_dir = OUT / 'workers'
    log_dir.mkdir(exist_ok=True)
    workers: list[Worker] = []
    try:
        for i, port in enumerate(ports, 1):
            workers.append(Worker(i, port, log_dir))
        if not check(f'{name}: 6 workers prontos', all(w.wait_ready() for w in workers)):
            return None
        dests = [f'127.0.0.1:{port}' for port in ports]
        stdin = stdin_for('par', carga, p, dests)
        try:
            rc, so, se, wall = run_cmd([str(EXE)], stdin)
        except subprocess.TimeoutExpired:
            check(f'{name}: termina antes de {RUN_TIMEOUT}s', False)
            return None
        time.sleep(0.3)  # deixa as threads leitoras pegarem as ultimas linhas
    finally:
        for w in workers:
            w.stop()
    cen.update({'exit': rc, 'segundos': round(wall, 3), 'stderr': se, 'stdin': stdin.decode()})
    (OUT / 'stdout_A_par-remoto.txt').write_text(so, encoding='utf-8')
    print(f'--- {name}: exit={rc} tempo={wall:.3f}s')
    out = check_scenario(name, so, rc, 'par', p, carga, expected)

    # ---- provas do lado worker ----
    eventos, pids = [], {}
    for w, fn_esperada in zip(workers, WORKER_FUNCS):
        (log_dir / f'worker{w.idx}.stderr.log').write_text(
            '\n'.join(f'{t:.6f} {l}' for t, l in w.lines) + '\n', encoding='utf-8')
        parsed = [(t, LOG_RE.match(l)) for t, l in w.lines]
        parsed = [(t, m) for t, m in parsed if m]
        tasks = [(t, m) for t, m in parsed if m.group(3) == 'TASK']
        results = [(t, m) for t, m in parsed if m.group(3) == 'RESULT']
        pid_log = {int(m.group(2)) for _, m in parsed}
        pids[w.idx] = {'pid_popen': w.proc.pid, 'pid_log': sorted(pid_log)}
        check(f'{name}: worker{w.idx} (porta {w.port}) 1 TASK + 1 RESULT de fn={fn_esperada}',
              len(tasks) == 1 and len(results) == 1 and tasks[0][1].group(5) == fn_esperada
              and results[0][1].group(5) == fn_esperada and results[0][1].group(4) == tasks[0][1].group(4),
              f'{len(tasks)} TASK, {len(results)} RESULT, linhas={[l for _, l in w.lines][:6]}')
        check(f'{name}: worker{w.idx} RESULT ok', bool(results) and results[0][1].group(6).startswith('ok'),
              results[0][1].group(6) if results else 'sem RESULT')
        check(f'{name}: worker{w.idx} PID do log == PID do processo ({w.proc.pid})', pid_log == {w.proc.pid},
              repr(pid_log))
        main_no_worker = '=== TESTE 10' in w.stdout_path.read_text(encoding='utf-8', errors='replace')
        check(f'{name}: worker{w.idx} nao executou o fluxo principal', not main_no_worker)
        for t, m in tasks + results:
            eventos.append({'t': t, 'worker': w.idx, 'evento': m.group(3), 'task': m.group(4), 'fn': m.group(5),
                            'resto': m.group(6)})
    todos_pids = [pid for v in pids.values() for pid in v['pid_log']]
    check(f'{name}: 6 PIDs de worker distintos', len(set(todos_pids)) == 6 and len(todos_pids) == 6,
          repr(todos_pids))
    t_tasks = [e['t'] for e in eventos if e['evento'] == 'TASK']
    t_res_av = [e['t'] for e in eventos if e['evento'] == 'RESULT' and e['fn'] == 'avaliar_lote']
    conc = len(t_tasks) == 6 and bool(t_res_av) and max(t_tasks) < min(t_res_av)
    margem = (min(t_res_av) - max(t_tasks)) if (t_tasks and t_res_av) else None
    check(f'{name}: concorrencia: os 6 TASK antes do 1o RESULT de avaliar_lote', conc,
          f'ultimo TASK - primeiro RESULT avaliar_lote = {margem}')
    t0 = min(e['t'] for e in eventos) if eventos else 0
    for e in eventos:
        e['t_rel_ms'] = round((e['t'] - t0) * 1000, 1)
        del e['t']
    cen.update({'workers': pids, 'eventos': sorted(eventos, key=lambda e: e['t_rel_ms']),
                'margem_concorrencia_ms': round(margem * 1000, 1) if margem is not None else None})
    return out


def svg_de(grade: list[str], cel=6) -> str:
    n_l = len(grade)
    n_c = max((len(r) for r in grade), default=0)
    rects = [f'<rect x="{j * cel}" y="{i * cel}" width="{cel}" height="{cel}"/>'
             for i, r in enumerate(grade) for j, ch in enumerate(r) if ch == '#']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{n_c * cel}" height="{n_l * cel}" '
            f'viewBox="0 0 {n_c * cel} {n_l * cel}" shape-rendering="crispEdges">\n'
            f'<title>Tapete de Sierpinski (saida do teste10.exe)</title>\n'
            f'<rect width="100%" height="100%" fill="white"/>\n<g fill="navy">\n'
            + '\n'.join(rects) + '\n</g>\n</svg>\n')


def ambiente() -> dict:
    env = {'python': sys.version.split()[0], 'plataforma': platform.platform(), 'cpu_logicas': None}
    try:
        import os
        env['cpu_logicas'] = os.cpu_count()
    except Exception:
        pass
    for chave, cmd in (('gpp', ['g++', '--version']), ('git_head', ['git', 'rev-parse', '--short', 'HEAD']),
                       ('git_branch', ['git', 'rev-parse', '--abbrev-ref', 'HEAD'])):
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20)
            env[chave] = (r.stdout.splitlines() or [''])[0]
        except Exception as exc:
            env[chave] = f'indisponivel: {exc}'
    return env


if __name__ == '__main__':
    sys.exit(main())
