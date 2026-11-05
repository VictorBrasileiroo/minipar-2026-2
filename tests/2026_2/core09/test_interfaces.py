"""Real compiler/native regression; only terminal keystrokes are simulated."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import app as web
import main
import menu
import test_orchestrator as sessions

EVIDENCE = []


class Interfaces(unittest.TestCase):
    def setUp(self):
        self.previous = Path.cwd()
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'output')
        os.chdir(self.tmp.name)
        for folder in ('tests', 'output', 'temp_code'):
            Path(folder).mkdir()
        Path('tests/basic.minipar').write_text('print(6 * 7);', encoding='utf-8')
        self.client = web.app.test_client()

    def tearDown(self):
        os.chdir(self.previous)
        self.tmp.cleanup()

    def compile(self, code='print(6 * 7);', **kwargs):
        response = self.client.post('/api/compile', json=dict(code=code, filename='basic.minipar', **kwargs))
        self.assertEqual(response.status_code, 200, response.get_json())
        data = response.get_json()
        EVIDENCE.append(dict(source=code, inputs=kwargs.get('inputs', []), response={key:value for key,value in data.items() if key not in ('cpp','tac')}, artifacts={key:dict(sha256=hashlib.sha256(data[key].encode()).hexdigest(), length=len(data[key])) for key in ('cpp','tac')}))
        return data

    def test_web_real_success_then_invalid_no_stale(self):
        data = self.compile()
        self.assertTrue(data['success'], data)
        self.assertIn('\n42\n', data['stdout'])
        self.assertIn('6', data['tac'])
        self.assertIn('7', data['cpp'])
        for code in ('print("broken', 'print(;', 'print(missing);'):
            data = self.compile(code)
            self.assertFalse(data['success'], data)
            self.assertTrue(data['stderr'])
            self.assertEqual(data['cpp'], '')
            self.assertEqual(data['tac'], '')

    def test_web_runtime_failure(self):
        data = self.compile('print("before failure"); print(substr("abc", 9, 1));')
        self.assertFalse(data['success'], data)
        self.assertIn('ERRO', data['stderr'])
        self.assertIn('before failure', data['stderr'])
        self.assertTrue(data['cpp'])

    def test_web_launch_without_cwd_wrapper(self):
        self.assertFalse(Path('main.py').exists())
        # Python must come from sys.executable, even absent from PATH.
        with patch.dict(os.environ, {'PATH':str(Path(os.environ['CXX']).parent)}):
            data = self.compile('print(9876);')
        self.assertTrue(data['success'], data)
        self.assertIn('\n9876\n', data['stdout'])

    def test_concurrent_same_filename(self):
        def compile_number(number):
            with web.app.test_client() as client:
                return client.post('/api/compile', json=dict(filename='same.minipar', code=f'print({number});')).get_json()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(compile_number, (31415, 27182)))
        for number, data in zip((31415, 27182), results):
            self.assertTrue(data['success'], data)
            self.assertIn(f'\n{number}\n', data['stdout'])
            self.assertIn(str(number), data['tac'])
            self.assertIn(str(number), data['cpp'])

    def test_compile_request_errors_and_missing_toolchain(self):
        self.assertEqual(self.client.post('/api/compile', json=[]).status_code, 400)
        self.assertEqual(self.client.post('/api/compile', json=dict(code='print(1);', filename='../escape.minipar')).status_code, 400)
        with patch.dict(os.environ, {'CXX':str(Path('absent-g++.exe').absolute())}):
            data = self.compile()
        self.assertFalse(data['success'], data)
        self.assertIn('GPP_NOT_FOUND', data['stderr'])
        self.assertNotIn('--- Executando', data['stderr'])

    def test_terminal_runtime_failure_and_invalid_start(self):
        Path('bad.minipar').write_text('print(substr("abc", 9, 1));', encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(main.compile_file('bad.minipar', 'bad'))
            data = menu.executar_binario('bad')
        self.assertIn('[ERRO] Programa encerrou com codigo 1', data)
        with patch('builtins.input', return_value='invalid'), contextlib.redirect_stdout(io.StringIO()) as out:
            main.start_interactive()
        self.assertIn('Escolha inválida', out.getvalue())

    def test_web_input_and_changed_source(self):
        data = self.compile('var x = input(); print(x);', inputs=['core09'])
        self.assertTrue(data['success'], data)
        self.assertIn('core09\n', data['stdout'])
        data = self.compile('print(12345);')
        self.assertTrue(data['success'], data)
        self.assertIn('12345', data['tac'])
        self.assertIn('12345', data['cpp'])
        self.assertIn('\n12345\n', data['stdout'])

    def test_web_timeout_real(self):
        data = self.compile('print("before timeout"); while (true) {}')
        self.assertFalse(data['success'], data)
        self.assertIn('limite', data['stderr'])
        self.assertIn('before timeout', data['stderr'])

    def test_pages_listing_and_sessions(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        for path in ('/static/js/script.js', '/static/css/style.css'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            response.close()
        self.assertEqual(self.client.get('/api/tests').json['tests'], ['basic.minipar'])
        self.assertEqual(self.client.post('/api/get_test', json={'filename':'basic.minipar'}).json['code'], 'print(6 * 7);')
        self.assertEqual(self.client.post('/api/get_test', json={'filename':'absent.minipar'}).status_code, 404)
        self.assertFalse(self.client.get('/api/session').json['active'])
        self.assertEqual(self.client.post('/api/session/join').status_code, 404)
        # Session metadata uses the original program analyzer and file protocol.
        candidates = [p for p in (ROOT/'tests').glob('*.minipar') if sessions.get_program_spec(str(p)).get('multi_computer')]
        self.assertTrue(candidates)
        shutil.copy(candidates[0], Path('tests')/candidates[0].name)
        result = self.client.post('/api/session/create', json={'filename':candidates[0].name})
        self.assertTrue(result.json['success'], result.json)
        self.assertTrue(self.client.get('/api/session').json['active'])
        self.assertTrue(self.client.post('/api/session/join').json['success'])
        self.assertTrue(self.client.post('/api/session/ready').json['success'])
        self.assertTrue(self.client.post('/api/session/clear').json['success'])
        self.assertFalse(self.client.get('/api/session').json['active'])

    def test_terminal_menu_and_syntax_error(self):
        stream = io.StringIO()
        with patch('builtins.input', side_effect=['1','bad','2','abc','2','99','2','1','0']), contextlib.redirect_stdout(stream):
            main.start_interactive()
        output = stream.getvalue()
        self.assertIn('42', output)
        self.assertIn('Saindo', output)
        self.assertIn('basic.minipar', output)
        self.assertTrue(Path('output/basic.cpp').exists())
        self.assertTrue(Path('output/basic.tac').exists())
        Path('tests/basic.minipar').write_text('print(;', encoding='utf-8')
        with patch('builtins.input', side_effect=['2','1','0']), contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            menu.exibir_menu()
        self.assertIn('Saindo', out.getvalue())
        self.assertFalse(Path('output/basic.exe').exists())
        self.assertFalse(Path('output/basic.cpp').exists())
        self.assertFalse(Path('output/basic.tac').exists())

    def test_legacy_t07_both_interfaces(self):
        path = ROOT/'tests/teste7_quicksort_iterativo_tac.minipar'
        shutil.copy(path, Path('tests')/path.name)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            menu.rodar_teste(str(Path('tests')/path.name))
        self.assertIn('Array ordenado: [5, 12, 33, 61, 98]', out.getvalue())
        data = self.compile(path.read_text(encoding='utf-8'))
        self.assertTrue(data['success'], data)
        self.assertIn('Array ordenado: [5, 12, 33, 61, 98]', data['stdout'])
        self.assertIn('quicksort_iterativo', data['tac'])
        self.assertIn('quicksort_iterativo', data['cpp'])
        EVIDENCE.append(dict(kind='legacy T07 menu', stdout=out.getvalue(), oracle='Array ordenado: [5, 12, 33, 61, 98]'))

    def test_cli_interactive_process(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT/'main.py')], input='1\n0\n', capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Saindo', result.stdout)

    def test_cli_fork_join(self):
        source = 'func twice(x) { return x * 2; } var a = fork twice(21) on "local"; var b = fork twice(7) on "local"; print(join(b), join(a));'
        Path('fork.minipar').write_text(source, encoding='utf-8')
        result = subprocess.run([sys.executable, '-B', str(ROOT/'main.py'), 'fork.minipar', 'fork'], capture_output=True, text=True, encoding='utf-8', timeout=130)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([str(Path('output/fork.exe').absolute())], capture_output=True, text=True, timeout=10)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '14 42\n', ''))
        EVIDENCE.append(dict(kind='CLI Fork/Join', source=source, stdout=result.stdout, stderr=result.stderr, returncode=result.returncode))


if __name__ == '__main__':
    records = []
    class Result(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            records.append(dict(test=test.id(), status='PASS'))
        def addFailure(self, test, error):
            super().addFailure(test, error)
            records.append(dict(test=test.id(), status='FAIL', detail=self._exc_info_to_string(error, test)))
        def addError(self, test, error):
            super().addError(test, error)
            records.append(dict(test=test.id(), status='FAIL', detail=self._exc_info_to_string(error, test)))
    result = unittest.main(testRunner=unittest.TextTestRunner(verbosity=2, resultclass=Result), exit=False).result
    output = ROOT / 'output/core09'
    output.mkdir(exist_ok=True)
    (output/'interfaces.json').write_text(json.dumps(dict(timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'), python=sys.version, compiler=os.environ.get('CXX'), tests=result.testsRun, failures=len(result.failures), errors=len(result.errors), records=records, evidence=EVIDENCE), ensure_ascii=False, indent=2), encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
