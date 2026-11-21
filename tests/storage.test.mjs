import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {GitHubStore,emptyState} from '../plugin/engine/github.mjs';
import {execute} from '../plugin/bridge.mjs';
import {Mailbox} from '../plugin/engine/mailbox.mjs';
import {encodeSnapshot,decodeSnapshot,segmentPath} from '../plugin/engine/segmented-storage.mjs';
const sha=text=>createHash('sha1').update(text).digest('hex');
const conflict=()=>Object.assign(new Error('Conflict'),{status:409});
class GitFixture {
  constructor(state=emptyState()) {
    this.blobs=new Map();this.trees=new Map();this.commits=new Map();this.calls=[];this.private=true;
    const blob=this.blob(JSON.stringify(state)),tree=this.tree(new Map([['mailbox.json',blob]]));
    this.head=this.commit(tree,[]);this.failBefore=false;this.failAfter=false;
  }
  blob(text){const id=sha(text);this.blobs.set(id,text);return id;}
  tree(files){const id=sha(JSON.stringify([...files]));this.trees.set(id,files);return id;}
  commit(tree,parents){const id=sha(JSON.stringify({tree,parents}));this.commits.set(id,{tree:{sha:tree},parents});return id;}
  files(head=this.head){return this.trees.get(this.commits.get(head).tree.sha);}
  store(){const store=new GitHubStore('fixture/mailbox');store.api=this.api.bind(this);return store;}
  async api(path,method='GET',body) {
    this.calls.push({path,method,body});
    if(path==='user')return {login:'alice'};
    path=path.replace('repos/fixture/mailbox','');
    if(path==='')return {private:this.private,permissions:{push:true}};
    if(path==='/git/ref/heads/dev-agent-mailbox')return {object:{sha:this.head}};
    if(path.startsWith('/contents/')&&method==='GET') {
      const [file,ref]=path.slice(10).split('?ref=');const head=ref==='dev-agent-mailbox'?this.head:ref;
      const id=this.files(head)?.get(file);if(!id)throw Object.assign(new Error('Not found'),{status:404});
      const text=this.blobs.get(id);return {sha:id,size:Buffer.byteLength(text),encoding:'base64',content:Buffer.from(text).toString('base64')};
    }
    if(path==='/contents/mailbox.json'&&method==='PUT') {
      if(body.sha!==this.files().get('mailbox.json'))throw conflict();
      const files=new Map(this.files());files.set('mailbox.json',this.blob(Buffer.from(body.content,'base64').toString()));
      this.head=this.commit(this.tree(files),[this.head]);return {};
    }
    if(path.startsWith('/git/commits/')&&method==='GET')return this.commits.get(path.split('/').at(-1));
    if(path==='/git/blobs'&&method==='POST')return {sha:this.blob(body.content)};
    if(path==='/git/trees'&&method==='POST') {
      const files=new Map(this.trees.get(body.base_tree));
      for(const entry of body.tree)files.set(entry.path,entry.sha??this.blob(entry.content));
      return {sha:this.tree(files)};
    }
    if(path==='/git/commits'&&method==='POST')return {sha:this.commit(body.tree,body.parents)};
    if(path==='/git/refs/heads/dev-agent-mailbox'&&method==='PATCH') {
      assert.equal(body.force,false);
      if(this.failBefore){this.failBefore=false;throw new Error('Connection lost before publication');}
      if(this.commits.get(body.sha).parents[0]!==this.head)throw conflict();
      this.head=body.sha;
      if(this.failAfter){this.failAfter=false;throw new Error('Connection lost after publication');}
      return {};
    }
    throw new Error(`Unexpected ${method} ${path}`);
  }
  async migrate(store=this.store()) {return store.migrateStorage({apply:true,expected_head:this.head,all_clients_upgraded:true});}
}


for (const version of [1,2]) test(`Hermes bridge and toolkit peer exchange on v${version}`,async()=>{
 const git=new GitFixture(),store=git.store();
 const peer=new Mailbox(store,'alice');
 const b=await peer.join({label:'Toolkit peer',task:'Synthetic review'});
 const invoke=(tool,args)=>execute({repo:'fixture/mailbox',token:'synthetic',tool,args},()=>git.store());
 const a=await invoke('connect',{label:'Hermes',task:'Synthetic review'});
 if(version===2) {
  const snapshot=await store.read(); snapshot.state.padding='x'.repeat(900000);
  const files=new Map(git.files());
  // Seed a large segmented fixture without bypassing the legacy migration size guard.
  const {manifest,nodes}=encodeSnapshot({...snapshot.state,version:2});
  for(const [digest,text] of nodes)files.set(segmentPath(digest),git.blob(text));
  files.set('mailbox.json',git.blob(JSON.stringify(manifest)));git.head=git.commit(git.tree(files),[git.head]);
 }
 const payload={agent_id:a.id,to:b.id,kind:'question',body:'Review this synthetic change',request_id:'upgrade-question'};
 const q=await invoke('send_message',payload);
 assert.equal((await invoke('send_message',payload)).id,q.id);
 assert.equal((await peer.inbox({agent_id:b.id})).messages[0].id,q.id);
 const answer=await peer.send({agent_id:b.id,to:a.id,kind:'answer',reply_to:q.id,body:'Reviewed',request_id:'upgrade-answer'});
 assert.equal((await invoke('check_inbox',{agent_id:a.id})).messages[0].id,answer.id);
 await invoke('acknowledge_message',{agent_id:a.id,message_id:answer.id});
 assert.equal((await invoke('check_inbox',{agent_id:a.id})).messages.length,0);
 if(version===2)assert.equal((await git.store().read()).state.padding.length,900000);
 await assert.rejects(invoke('migrateStorage',{}),/not exposed/);
});
test('atomic publication retains old snapshot on failure and rejects competing writers',async()=>{
  const git=new GitFixture();await git.migrate();
  const a=git.store(),b=git.store(),s1=await a.read(),s2=await b.read(),before=git.head;
  s1.state.messages.push({id:'a'});git.failBefore=true;
  await assert.rejects(a.write(s1.state,s1.sha),/before publication/);
  assert.equal(git.head,before);assert.deepEqual((await b.read()).state.messages,[]);
  await a.write(s1.state,s1.sha);
  s2.state.messages.push({id:'b'});await assert.rejects(b.write(s2.state,s2.sha),{status:409});
  assert.deepEqual((await b.read()).state.messages,[{id:'a'}]);
  assert.deepEqual((await a.segmented.read(before)).state.messages,[]);
});

test('lost publication response followed by identical retry sends exactly once',async()=>{
  const git=new GitFixture(),store=git.store(),box=new Mailbox(store,'alice');
  const agent=(await box.join({label:'a',task:'test'})).id;await git.migrate(store);
  const payload={agent_id:agent,to:agent,body:'hello',kind:'question',request_id:'stable'};
  git.failAfter=true;await assert.rejects(box.send(payload),/after publication/);
  const head=git.head;const sent=await box.send(payload);
  assert.equal(git.head,head);assert.equal((await store.read()).state.messages.length,1);
  assert.equal(sent.requestId,'stable');
  await assert.rejects(box.send({...payload,body:'different'}),/different content/);
});

test('public repositories and corrupt or missing segments fail closed',async()=>{
  const git=new GitFixture();await git.migrate();const store=git.store();
  git.private=false;await assert.rejects(store.read(),/no longer private/);
  git.private=true;
  const manifest=JSON.parse(git.blobs.get(git.files().get('mailbox.json')));
  const blob=git.files().get(segmentPath(manifest.root));git.blobs.set(blob,'{}');
  await assert.rejects(store.read(),/integrity/);
  git.files().delete(segmentPath(manifest.root));await assert.rejects(store.read(),/Not found/);
});

test('simultaneous publications retry against the winning head without losing messages',async()=>{
  const git=new GitFixture(),setup=git.store(),box=new Mailbox(setup,'alice');
  const agent=(await box.join({label:'a',task:'test'})).id;await git.migrate(setup);
  // Hold the first ref update until both writers have built sibling commits.
  const original=git.api.bind(git);let count=0,release;
  const barrier=new Promise(resolve=>{release=resolve;});
  git.api=async(path,method,body)=>{
    if(method==='PATCH' && ++count<=2){if(count===2)release();await barrier;}
    return original(path,method,body);
  };
  const a=new Mailbox(git.store(),'alice'),b=new Mailbox(git.store(),'alice');
  await Promise.all([
    a.send({agent_id:agent,to:agent,body:'first',kind:'question',request_id:'a'}),
    b.send({agent_id:agent,to:agent,body:'second',kind:'question',request_id:'b'}),
  ]);
  const messages=(await git.store().read()).state.messages;
  assert.equal(messages.length,2);assert.deepEqual(messages.map(m=>m.sequence),[1,2]);
  assert.deepEqual(new Set(messages.map(m=>m.requestId)),new Set(['a','b']));
  assert.ok(count>=3);
});


test('HTTPS adapter fixes origin, rejects redirects and keeps credentials out of errors',async()=>{
 const original=globalThis.fetch;const calls=[];
 globalThis.fetch=async(url,options)=>{calls.push({url,options});return {ok:true,text:async()=>JSON.stringify({private:true})};};
 try {
  const store=new GitHubStore('fixture/mailbox');store.token='synthetic-secret';
  await store.api('repos/fixture/mailbox');
  assert.equal(calls[0].url,'https://api.github.com/repos/fixture/mailbox');
  assert.equal(calls[0].options.redirect,'error');
  await assert.rejects(store.api('https://other.example/'),/Invalid API path/);
  globalThis.fetch=async()=>({ok:false,status:403,text:async()=>'synthetic-secret'});
  await assert.rejects(store.api('user'),e=>e.status===403&&!e.message.includes('synthetic-secret'));
 } finally {globalThis.fetch=original;}
});
