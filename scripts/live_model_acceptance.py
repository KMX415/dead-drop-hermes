"""Real local-model Hermes loop against synthetic mailbox; no live GitHub or scheduler claims."""
import os,sys,json,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone,timedelta
root=Path(__file__).resolve().parents[1]
if os.environ.get('DEAD_DROP_MODEL_TEST_WORKER')!='1':
    env=os.environ.copy();env['DEAD_DROP_MODEL_TEST_WORKER']='1'
    from process_tree import run_bounded
    try:
        outcome=run_bounded([sys.executable,str(Path(__file__).resolve())],env=env,timeout=min(300,int(os.environ.get("DEAD_DROP_MODEL_TEST_TIMEOUT","300"))))
        raise SystemExit(outcome)
    except subprocess.TimeoutExpired:
        (root/'runtime/live-model-result.json').write_text(json.dumps({'ok':False,'stage':'model_tool_loop_timeout','deadline_seconds':min(300,int(os.environ.get('DEAD_DROP_MODEL_TEST_TIMEOUT','300'))),'limits':['No live GitHub or scheduler validation']}),encoding='utf-8')
        raise SystemExit('Bounded model test reached its configured deadline')
home=Path(os.environ.get('DEAD_DROP_MODEL_TEST_HOME',str(root/'runtime/live-model-acceptance'))).resolve()
if not home.is_relative_to(root/'runtime'):raise SystemExit('Test home must stay under this repository runtime directory')
# Run once; preserve evidence and never silently reset worker state.
if not (home/'config.yaml').exists():
    home.mkdir(parents=True,exist_ok=True)
    shutil.copytree(root/'plugin',home/'plugins/dead-drop-hermes',ignore=shutil.ignore_patterns('__pycache__'))
    server='dead-drop-synthetic-contributor--fixture'
    config={'mcp_servers':{server:{'command':shutil.which('node'),'args':[str(root/'runtime/engine-upstream/test/fixtures/hermes-dead-drop-server.mjs')],'timeout':30}},'plugins':{'enabled':['dead-drop-hermes'],'entries':{'dead-drop-hermes':{'mcp_allowlist':[server]}}},'tools':{'tool_search':{'enabled':'off'}},'model':{'context_length':8192,'streaming':False,'default':'qwen3.5-9b','provider':'lmstudio','base_url':'http://127.0.0.1:1234/v1'}}
    (home/'config.yaml').write_text(json.dumps(config),encoding='utf-8')
for key in list(os.environ):
    if any(part in key.upper() for part in ('TOKEN','SECRET','API_KEY','PASSWORD','CREDENTIAL')):os.environ.pop(key,None)
os.environ['HERMES_HOME']=str(home);os.environ['HERMES_MANAGED_DIR']=str(home/'managed');os.environ['HERMES_ENABLE_PROJECT_PLUGINS']='0'
sys.path.insert(0,str(root/'runtime/hermes-upstream'))
# Bootstrap must finish before generating identities or external effects.
import faulthandler
faulthandler.dump_traceback_later(60)
from run_agent import AIAgent
from hermes_cli.plugins import get_plugin_manager,PluginContext
from hermes_cli.plugins_manifest import PluginManifest
from tools.mcp_tool_discovery import discover_mcp_tools
from tools.mcp_tool_lifecycle import shutdown_mcp_servers
from types import SimpleNamespace
server='dead-drop-synthetic-contributor--fixture'
ctx=PluginContext(PluginManifest(name='dead-drop-hermes'),SimpleNamespace())
def call(tool,args):
    result=ctx.call_mcp(server,tool,args)
    assert result.get('ok'),result
    value=result.get('structuredContent',result.get('result'))
    return json.loads(value) if isinstance(value,str) else value
try:
    discover_mcp_tools(allowed_mcp_names=[server])
    worker=call('join_team',{'label':'Model-driven Hermes','task':'Synthetic bounded review'})['id']
    peer=call('join_team',{'label':'Synthetic test peer','task':'Synthetic bounded review'})['id']
    question=call('send_message',{'agent_id':peer,'to':worker,'body':'Public test fixture: function add(a,b) returns a-b. For add(2,3), state the actual result and the expected sum. Include token HERMES-NATIVE-TEST-20261104. Do not edit files.','kind':'question','request_id':'model-test-seed'})
    config=json.loads((home/'config.yaml').read_text(encoding='utf-8'))
    config['plugins']['entries']['dead-drop-hermes']['settings']={'transport':'mcp','active':True,'server':server,'mailbox':'synthetic-contributor/fixture','worker':worker,'peers':[peer],'scope':'Answer this synthetic arithmetic review only; no shell, file edits or other work.','deadline':(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat(),'max_messages':1,'max_attempts':2}
    (home/'config.yaml').write_text(json.dumps(config),encoding='utf-8')
    get_plugin_manager().discover_and_load(force=True)
    events=[]
    agent=AIAgent(model='qwen3.5-9b',base_url='http://127.0.0.1:1234/v1',api_key='local-no-secret',provider='lmstudio',max_iterations=6,max_tokens=384,reasoning_config={'enabled':False},enabled_toolsets=['dead_drop'],skip_context_files=True,quiet_mode=True,save_trajectories=False,tool_progress_callback=lambda *a,**k:events.append({'args':str(a),'kwargs':str(k)}))
    response=agent.run_conversation('Use dead_drop_inbox to read the one authorized question. Review the arithmetic in that question, send exactly one answer to its sender using reply_to and request_id model-review-answer. Then acknowledge the question. Do not call any other tools. End by stating the findings. This is a bounded synthetic test.')
    inbox=call('check_inbox',{'agent_id':peer})
    answers=[m for m in inbox['messages'] if m['kind']=='answer' and m['from']==worker and m.get('replyTo')==question['id']]
    assert len(answers)==1,{'answers':answers,'response':str(response)[-2000:]}
    answer=answers[0]
    assert 'HERMES-NATIVE-TEST-20261104' in answer['body'] and '-1' in answer['body'] and '5' in answer['body'],answer
    remaining=call('check_inbox',{'agent_id':worker})
    assert all(m['id']!=question['id'] for m in remaining['messages']),'Question was not acknowledged'
    report={'acknowledged':True,'ok':True,'model':'qwen3.5-9b','endpoint':'loopback LM Studio','question_id':question['id'],'answer':answer,'tool_events':events,'response':response,'limits':['Synthetic peer and in-memory MCP mailbox','Actual Hermes model and tool loop','Not live GitHub or native scheduler evidence','Not independent-human testing']}
    (root/'runtime/live-model-result.json').write_text(json.dumps(report,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'ok':True,'question_id':question['id'],'answer_id':answer['id']}))
finally:shutdown_mcp_servers()
