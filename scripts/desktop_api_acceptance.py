"""Read-only Desktop backend checks inside the isolated Hermes validation runtime."""
import sys,os,json,tempfile,sqlite3,importlib.util
from pathlib import Path
root=Path(__file__).resolve().parents[1]
home=root/'runtime/desktop-api-validation';home.mkdir(exist_ok=True)
os.environ['HERMES_HOME']=str(home);os.environ['HERMES_MANAGED_DIR']=str(home/'managed')
sys.path.insert(0,str(root/'runtime/hermes-upstream'))
spec=importlib.util.spec_from_file_location('desktop_api_under_test',root/'plugin/dashboard/plugin_api.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
from plugins.plugin_storage import plugin_data_dir
path=plugin_data_dir('dead-drop-hermes')/'exchanges.sqlite3'
assert not path.exists(),'Use a fresh test profile; do not erase evidence'
assert module.status()=={'state':'No exchanges yet','recent':[]}
with sqlite3.connect(path) as db:
    db.execute('CREATE TABLE writes (key TEXT, tool TEXT, attempts INTEGER, result TEXT, error TEXT, updated REAL, payload TEXT)')
    db.execute('INSERT INTO writes VALUES (?,?,?,?,?,?,?)',('fixture-send','send_message',1,'{}',None,1,'PRIVATE_BODY_NOT_FOR_UI'))
before=path.read_bytes();result=module.status()
assert result['recent'][0]['completed']==1
assert 'PRIVATE_BODY_NOT_FOR_UI' not in json.dumps(result)
assert path.read_bytes()==before,'Read-only route modified database'
report={'ok':True,'empty_state':True,'delivery_metadata':True,'no_message_bodies':True,'read_only':True,'limits':['Backend API checks only; not visual rendering or profile-switch proof']}
(root/'runtime/desktop-api-result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
