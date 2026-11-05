import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from plugin.bundled import BundledTransport, connect
from plugin.runtime import Blocked

WORKER='owner/11111111-1111-1111-1111-111111111111'
class NativeBundleTests(unittest.TestCase):
    def test_missing_profile_secret_fails_before_subprocess(self):
        with patch('plugin.bundled.subprocess.run') as run:
            with self.assertRaises(Blocked):BundledTransport('owner/box',lambda name:None)('dead-drop-owner--box','check_inbox',{})
            run.assert_not_called()

    def test_token_only_in_stdin_and_inherited_credentials_removed(self):
        with patch.dict('os.environ',{'OTHER_API_KEY':'must-not-pass','NODE_OPTIONS':'--import bad'}), patch('plugin.bundled.shutil.which',return_value='node'), patch('plugin.bundled.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='{"ok":true,"result":{}}')) as run:
            transport=BundledTransport('owner/box',lambda name:'test-only-secret')
            self.assertTrue(transport('dead-drop-owner--box','check_inbox',{})['ok'])
            args,kw=run.call_args
            self.assertNotIn('test-only-secret',str(args))
            self.assertNotIn('OTHER_API_KEY',kw['env']);self.assertNotIn('NODE_OPTIONS',kw['env'])
            self.assertEqual(json.loads(kw['input'])['token'],'test-only-secret')
            self.assertFalse(kw.get('shell',False))

    def test_unexposed_operation_never_starts_engine(self):
        with self.assertRaises(Blocked):BundledTransport('owner/box',lambda name:'x')('dead-drop-owner--box','create_task',{})

    def test_connect_persists_and_reuses_identity(self):
        calls=[]
        def transport(*args):calls.append(args);return {'ok':True,'result':{'id':WORKER}}
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(2):self.assertEqual(connect(folder,{'mailbox':'owner/box'},transport)['worker'],WORKER)
            self.assertEqual(len(calls),1)
            with self.assertRaises(Blocked):connect(folder,{'mailbox':'owner/other'},transport)

    def test_uncertain_join_not_repeated(self):
        calls=[]
        def transport(*args):calls.append(args);return {'ok':False}
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(2):
                with self.assertRaises(Blocked):connect(folder,{'mailbox':'owner/box'},transport)
            self.assertEqual(len(calls),1)

    def test_cron_cannot_connect(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(Blocked):connect(folder,{'mailbox':'owner/box'},None,scheduled=True)
            self.assertEqual(list(Path(folder).iterdir()),[])
