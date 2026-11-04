"""Run upstream admission checks with an isolated home, no model account."""
import json, os, sys, tempfile, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
upstream=root/"runtime/hermes-upstream"
pin=json.loads((root/"COMPATIBILITY.json").read_text())["hermes_source"]
assert subprocess.check_output(["git","-C",str(upstream),"rev-parse","HEAD"],text=True).strip()==pin
subprocess.run(["git","-C",str(upstream),"diff","--quiet","HEAD"],check=True)
if os.environ.get("HERMES_SAFE_MODE","").lower() in ("1","true","yes","on"):
    raise SystemExit("Safe mode active; use an approved isolated validation environment")
with tempfile.TemporaryDirectory(dir=root/"runtime") as home:
    os.environ["HERMES_HOME"]=home
    os.environ["HERMES_MANAGED_DIR"]=str(Path(home)/"managed")
    os.environ["PYTHONPATH"]=str(upstream)
    sys.path.insert(0,str(upstream))
    from hermes_cli.plugin_validate import validate_plugin_dir
    report=validate_plugin_dir(root/"plugin")
    (root/"runtime/catalog-validation.json").write_text(json.dumps(report.to_dict(),indent=2),encoding="utf-8")
    print(json.dumps(report.to_dict(),indent=2))
    if not report.ok:raise SystemExit(1)
    from hermes_cli.plugin_dev import doctor_plugin
    doctor=doctor_plugin(root/"plugin")
    print(doctor.format_text())
    if any(getattr(f,"level",None)=="error" for f in doctor.findings):raise SystemExit(1)
    # Test-only use of upstream Doctor machinery; never shipped in plugin/.
    from hermes_cli.plugin_dev import _doctor_runtime
    with _doctor_runtime(root/"plugin") as host:
        assert len(host.manager.list_automation_blueprints())==1
        assert len(host.registered_tools)==5
        host.manager.unload()
        assert not host.manager.list_automation_blueprints()
    print("Native blueprint registration and unload passed")
