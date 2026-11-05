import importlib.util,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path

@unittest.skipUnless(importlib.util.find_spec('psutil'),'Validation dependency psutil required')
class ProcessTreeTests(unittest.TestCase):
    def test_timeout_terminates_grandchild(self):
        import psutil
        from scripts.process_tree import run_bounded
        with tempfile.TemporaryDirectory() as folder:
            marker=Path(folder)/'child.json'
            program="import subprocess,sys,time,json,psutil; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid,'created':psutil.Process(p.pid).create_time()})); time.sleep(60)"
            with self.assertRaises(subprocess.TimeoutExpired):
                run_bounded([sys.executable,'-c',program,str(marker)],env=os.environ.copy(),timeout=3)
            self.assertTrue(marker.exists())
            import json
            record=json.loads(marker.read_text())
            try:child=psutil.Process(record['pid'])
            except psutil.NoSuchProcess:return
            self.assertNotEqual(child.create_time(),record['created'],'Test grandchild survived timeout')

    def test_success_exit_code(self):
        from scripts.process_tree import run_bounded
        self.assertEqual(run_bounded([sys.executable,'-c','pass'],env=os.environ.copy(),timeout=10),0)
