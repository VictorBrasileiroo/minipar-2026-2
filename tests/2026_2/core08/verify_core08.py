"""Repeatable CORE-08 validation, logs and machine-readable results."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/core08'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))


def main():
    import importlib.util
    spec=importlib.util.spec_from_file_location('core08_tests',Path(__file__).with_name('test_service.py'))
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    records=[]
    class Result(unittest.TextTestResult):
        def addSuccess(self,test):
            super().addSuccess(test); records.append(dict(test=test.id(),status='PASS'))
        def addFailure(self,test,error):
            super().addFailure(test,error); records.append(dict(test=test.id(),status='FAIL',detail=self._exc_info_to_string(error,test)))
        def addError(self,test,error):
            super().addError(test,error); records.append(dict(test=test.id(),status='FAIL',detail=self._exc_info_to_string(error,test)))
    with (OUT/'tests-final.log').open('w',encoding='utf-8') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),records=records,
        python=sys.version,compiler=os.environ.get('CXX','g++'),timestamp=time.strftime('%Y-%m-%dT%H:%M:%S'))
    (OUT/'tests-final.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='records'}))
    return not result.wasSuccessful()


if __name__=='__main__': raise SystemExit(main())
