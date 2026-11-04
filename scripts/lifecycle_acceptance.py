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
cmd_install(root.as_uri()+"#plugin",ref=head,enable=False,no_deps=True)
data=plugin_data_dir("dead-drop-hermes")/"history-fixture.json"
data.write_text('{"fixture":"preserve across uninstall"}',encoding="utf-8")
expected=hashlib.sha256(data.read_bytes()).hexdigest()
cmd_enable("dead-drop-hermes",allow_tool_override=False)
cmd_disable("dead-drop-hermes")
cmd_remove("dead-drop-hermes")
assert data.is_file() and hashlib.sha256(data.read_bytes()).hexdigest()==expected
cmd_install(root.as_uri()+"#plugin",ref=head,enable=False,no_deps=True)
assert hashlib.sha256(data.read_bytes()).hexdigest()==expected
report={"ok":True,"commit":head,"installed":True,"enabled":True,"disabled":True,"removed":True,"reinstalled":True,"data_preserved":True,"scope":"Disposable profile only; no production installation or model"}
(root/"runtime/lifecycle-acceptance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report,indent=2))
