"""Exercise official installer/toggle/remove against a disposable profile only."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
if os.environ.get("HERMES_SAFE_MODE","").lower() in ("1","true","yes","on"):raise SystemExit("Safe mode active")
head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
if len(sys.argv)==1:
    with tempfile.TemporaryDirectory(dir=root/"runtime") as home:
        subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",home],check=True)
    print("Disposable installer profile cleaned after worker exit")
    raise SystemExit(0)
home=Path(sys.argv[2]).resolve()
if not home.is_relative_to((root/"runtime").resolve()) or home==(root/"runtime").resolve():
    raise SystemExit("Refusing non-test profile")
os.environ["HERMES_HOME"]=str(home)
os.environ["HERMES_MANAGED_DIR"]=str(Path(home)/"managed")
os.environ["HERMES_ENABLE_PROJECT_PLUGINS"]="0"
for key in list(os.environ):
    if any(part in key.upper() for part in ("TOKEN","SECRET","API_KEY","PASSWORD","CREDENTIAL")):os.environ.pop(key,None)
sys.path.insert(0,str(root/"runtime/hermes-upstream"))
from hermes_cli.plugins_cmd_install import cmd_install
from hermes_cli.plugins_cmd import cmd_enable,cmd_disable,cmd_remove
from plugins.plugin_storage import plugin_data_dir
cmd_install(root.as_uri()+"#plugin",ref="40c1551a9ed8b9d8fc15b481fdf2f4fc746487c6",enable=False,no_deps=True)
data=plugin_data_dir("dead-drop-hermes")/"history-fixture.json"
data.write_text('{"fixture":"preserve across uninstall"}',encoding="utf-8")
# Exercise retained identity and an actual uncertain write journal from the old code.
import importlib.util
spec=importlib.util.spec_from_file_location("old_workflow",home/"plugins/dead-drop-hermes/runtime.py")
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
worker="owner/11111111-1111-1111-1111-111111111111"
peer="peer/22222222-2222-2222-2222-222222222222"
settings=dict(active=True,server="dead-drop-owner--fixture",mailbox="owner/fixture",worker=worker,peers=[peer],scope="Synthetic upgrade check",deadline="2099-01-01T00:00:00Z",max_messages=5,max_attempts=3)
identity=data.parent/"worker.json"
identity.write_text(json.dumps({"repo":"owner/fixture","worker":worker}),encoding="utf-8")
workflow=old.Workflow(data.parent,settings,lambda *a,**k:{"ok":False})
try:workflow.send(peer,"Synthetic pending payload","upgrade-pending")
except old.Blocked:pass
retained={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in data.parent.iterdir() if p.is_file()}
expected=hashlib.sha256(data.read_bytes()).hexdigest()
cmd_install(root.as_uri()+"#plugin",ref=head,enable=False,no_deps=True,force=True)
assert hashlib.sha256(data.read_bytes()).hexdigest()==expected
assert all(hashlib.sha256((data.parent/name).read_bytes()).hexdigest()==digest for name,digest in retained.items())
assert "version: 0.3.0" in (home/"plugins/dead-drop-hermes/plugin.yaml").read_text()
installed_engine=home/"plugins/dead-drop-hermes/engine"
for name,digest in json.loads((installed_engine/"SOURCE.json").read_text())["files"].items():
    assert hashlib.sha256((installed_engine/name).read_bytes()).hexdigest()==digest,name
cmd_enable("dead-drop-hermes",allow_tool_override=False)
cmd_disable("dead-drop-hermes")
cmd_remove("dead-drop-hermes")
assert data.is_file() and hashlib.sha256(data.read_bytes()).hexdigest()==expected
cmd_install(root.as_uri()+"#plugin",ref=head,enable=False,no_deps=True)
assert hashlib.sha256(data.read_bytes()).hexdigest()==expected
report={"ok":True,"commit":head,"installed":True,"upgraded_from":"0.2.0","enabled":True,"disabled":True,"removed":True,"reinstalled":True,"data_preserved":True,"identity_and_pending_journal_preserved":True,"scope":"Disposable profile only; no production installation or model"}
(root/"runtime/lifecycle-acceptance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
