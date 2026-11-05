// Fixed-operation bridge to the bundled engine. No shell, MCP daemon, or credential lookup.
import { Mailbox } from './engine/mailbox.mjs';
import { GitHubStore } from './engine/github.mjs';
import { pathToFileURL } from 'node:url';
export async function execute(input, storeFactory = repo => new GitHubStore(repo)) {
  const methods = {check_inbox:'inbox',send_message:'send',acknowledge_message:'acknowledge',connect:'join',initialize:'join'};
  if (!Object.hasOwn(methods,input.tool)) throw new Error('Tool not exposed by Hermes bundle');
  if(typeof input.token!=='string'||!input.token.trim())throw new Error('Hermes credential required');
  const store=storeFactory(input.repo);store.token=input.token;
  const login=await store.verify();
  // Existing private mailbox only. Creating repositories/branches is separate owner work.
  if(input.tool==='initialize')await store.initialize();
  await store.read();
  const mailbox=new Mailbox(store,login);
  return await mailbox[methods[input.tool]](input.args);
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    if(Number(process.versions.node.split('.')[0])<22)throw new Error('Node 22+ required');
    let input='';for await(const chunk of process.stdin){input+=chunk;if(input.length>100000)throw new Error('Input too large');}
    const result=await execute(JSON.parse(input));
    process.stdout.write(JSON.stringify({ok:true,result}));
  } catch {
    // Never emit the request, credentials, response bodies, or raw provider errors.
    process.stdout.write(JSON.stringify({ok:false,error:'Bundled engine operation failed; outcome may be uncertain'}));
    process.exitCode=1;
  }
}
