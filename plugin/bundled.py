"""Native plugin transport; secrets come only from Hermes's public profile scope."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from .runtime import Blocked

class BundledTransport:
    def __init__(self, repo, secret_reader=None):
        self.repo=repo
        self.secret_reader=secret_reader

    def preflight(self):
        if self.secret_reader is None:
            from agent.secret_scope import get_secret
            token=get_secret('DEAD_DROP_GITHUB_TOKEN')
        else:
            token=self.secret_reader('DEAD_DROP_GITHUB_TOKEN')
        if not token:
            raise Blocked('Set the GitHub token in Hermes plugin secret settings before connecting')
        node=shutil.which('node')
        if not node:raise Blocked('Node.js 22+ is required for the bundled engine')
        # Validate locally before connect records a potentially uncertain write.
        # Keep injected Node flags and unrelated credentials out of this probe too.
        env={k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP'}}
        try:
            version=subprocess.run([node,'--version'],capture_output=True,text=True,
                timeout=5,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            match=re.fullmatch(r'v(\d+)\.\d+\.\d+\s*',version.stdout)
            if version.returncode or not match or int(match[1])<22:
                raise Blocked('Node.js 22+ is required; upgrade Node on PATH and restart Hermes before connecting')
        except (OSError,subprocess.TimeoutExpired):
            raise Blocked('Could not verify Node.js; check Node on PATH and restart Hermes before connecting') from None
        return token,node

    def __call__(self, server, tool, args, timeout=30):
        if server != 'dead-drop-'+self.repo.lower().replace('/','--'):
            raise Blocked('Connection name does not match the mailbox')
        if tool not in {'check_inbox','send_message','acknowledge_message','connect','initialize'}:
            raise Blocked('Operation is not exposed by the bundled transport')
        token,node=self.preflight()
        # Do not inherit provider credentials, NODE_OPTIONS, or another profile's environment.
        allowed={'PATH','SYSTEMROOT','WINDIR','TEMP','TMP'}
        env={k:v for k,v in os.environ.items() if k.upper() in allowed}
        request={'repo':self.repo,'token':token,'tool':tool,'args':args}
        try:
            result=subprocess.run([node,str(Path(__file__).with_name('bridge.mjs'))],
                input=json.dumps(request),capture_output=True,text=True,encoding='utf-8',
                timeout=min(timeout,30),env=env,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or len(result.stdout)>3000000:return {'ok':False}
            return json.loads(result.stdout)
        except (OSError,subprocess.TimeoutExpired,ValueError):
            return {'ok':False}


def connect(directory, settings, transport, *, scheduled=False, initialize=False):
    if scheduled:raise Blocked('Connect requires an interactive owner command')
    repo=settings.get('mailbox','')
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):
        raise Blocked('Set the private mailbox in Hermes plugin settings first')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    identity=directory/'worker.json'
    if identity.exists():
        saved=json.loads(identity.read_text(encoding='utf-8'))
        if saved['repo']!=repo:raise Blocked('Saved identity belongs to another mailbox')
        return saved
    if isinstance(transport,BundledTransport):transport.preflight()
    pending=directory/'connect-pending.json'
    try:
        with pending.open('x',encoding='utf-8') as f:
            json.dump({'repo':repo,'operation':'connect','status':'unconfirmed'},f)
    except FileExistsError:
        raise Blocked('A prior connect is unconfirmed. Inspect mailbox workers before joining again') from None
    result=transport('dead-drop-'+repo.lower().replace('/','--'),'initialize' if initialize else 'connect',
                     {'label':'Hermes','task':'Owner-authorized collaboration'})
    from .runtime import ID
    worker=result.get('result',{}).get('id') if result.get('ok') else None
    if not isinstance(worker,str) or not ID.fullmatch(worker):
        raise Blocked('Connect unconfirmed. Do not retry blindly; inspect mailbox workers')
    saved={'repo':repo,'worker':worker}
    with identity.open('x',encoding='utf-8') as f:json.dump(saved,f)
    pending.unlink()
    return saved
