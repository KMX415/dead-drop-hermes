"""Actual Hermes call_mcp and Dead Drop fixture. No live GitHub, inference, or schedules."""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
root=Path(__file__).resolve().parents[1]
pins=json.loads((root/"COMPATIBILITY.json").read_text())
for folder,key in (("hermes-upstream","hermes_source"),("engine-upstream","dead_drop_source")):
    path=root/"runtime"/folder
    actual=subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"],text=True).strip()
    if actual!=pins[key]:raise SystemExit("Unexpected source revision: "+folder)
    subprocess.run(["git","-C",str(path),"diff","--quiet","HEAD"],check=True)
if os.environ.get("HERMES_SAFE_MODE","").lower() in ("1","true","yes","on"):raise SystemExit("Safe mode active")
for key in list(os.environ):
    if any(part in key.upper() for part in ("TOKEN","SECRET","API_KEY","PASSWORD","CREDENTIAL")):os.environ.pop(key,None)
with tempfile.TemporaryDirectory(dir=root/"runtime") as home:
    os.environ["HERMES_HOME"]=home;os.environ["HERMES_MANAGED_DIR"]=str(Path(home)/"managed")
    sys.path.insert(0,str(root/"runtime/hermes-upstream"));sys.path.insert(0,str(root))
    server="dead-drop-synthetic-contributor--fixture"
    config={"mcp_servers":{server:{"command":shutil.which("node"),"args":[str(root/"runtime/engine-upstream/test/fixtures/hermes-dead-drop-server.mjs")],"timeout":30}},"plugins":{"entries":{"dead-drop-hermes":{"mcp_allowlist":[server]}}}}
    Path(home,"config.yaml").write_text(json.dumps(config),encoding="utf-8")
    from tools.mcp_tool_discovery import discover_mcp_tools
    from tools.mcp_tool_lifecycle import shutdown_mcp_servers
    from hermes_cli.plugins import PluginContext
    from hermes_cli.plugins_manifest import PluginManifest
    from plugin.runtime import Workflow, Blocked
    ctx=PluginContext(PluginManifest(name="dead-drop-hermes"),SimpleNamespace())
    def call(tool,args):
        r=ctx.call_mcp(server,tool,args)
        if not r.get("ok"):raise RuntimeError(r)
        result=r.get("structuredContent",r.get("result"))
        return json.loads(result) if isinstance(result,str) else result
    try:
        discovered=discover_mcp_tools(allowed_mcp_names=[server])
        a=call("join_team",{"label":"Synthetic Hermes","task":"Component acceptance"})["id"]
        b=call("join_team",{"label":"Synthetic peer","task":"Component acceptance"})["id"]
        settings=dict(transport="mcp",active=True,server=server,mailbox="synthetic-contributor/fixture",worker=a,peers=[b],scope="Synthetic public review",deadline="2099-01-01T00:00:00Z",max_messages=3,max_attempts=2)
        w=Workflow(Path(home)/"plugin-data/dead-drop-hermes",settings,ctx.call_mcp)
        question=w.send(b,"Review the public example","component-question")
        assert w.send(b,"Review the public example","component-question")["id"]==question["id"]
        answer=call("send_message",dict(agent_id=b,to=a,kind="answer",body="Fixture review evidence",reply_to=question["id"],request_id="component-answer"))
        assert w.inbox()["messages"][0]["id"]==answer["id"]
        try:w.send(b,"loop","loop",reply_to=answer["id"])
        except Blocked:pass
        else:raise AssertionError("Reply loop allowed")
        w.ack(answer["id"])
        assert w.inbox()["messages"]==[]
        report={"ok":True,"pins":pins,"tools_discovered":len(discovered),"question_id":question["id"],"answer_id":answer["id"],"deduplicated":True,"acknowledged":True,"reply_loop_blocked":True,"limits":["Synthetic in-memory peers","Actual Hermes MCP path; no model inference","No real scheduler, independent humans, or live GitHub mailbox"]}
        (root/"runtime/component-acceptance.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(report,indent=2))
    finally:shutdown_mcp_servers()
