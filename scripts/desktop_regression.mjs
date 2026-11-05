// Component regressions use mocked public SDK atoms and deferred REST promises.
// This complements the native Desktop checks; it is not native host evidence.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..');
const deps=path.join(root,'runtime/ui-tests/node_modules');
const reactUrl=pathToFileURL(path.join(deps,'react/index.js')).href;
const React=(await import(reactUrl)).default;
const {default:Renderer}=await import(pathToFileURL(path.join(deps,'react-test-renderer/index.js')).href);
const {act}=React;globalThis.IS_REACT_ACT_ENVIRONMENT=true;
function atom(value){const listeners=new Set();return {get:()=>value,subscribe:fn=>{listeners.add(fn);return()=>listeners.delete(fn)},set:next=>{value=next;for(const fn of listeners)fn();}};}
const state={profile:atom('default'),gateway:atom('open'),connectionId:atom('test-local')};
const host={state};const useValue=a=>React.useSyncExternalStore(a.subscribe,a.get,a.get);
const sdkKey='__deadDropDesktopTestSdk';globalThis[sdkKey]={host,useValue};
const source=fs.readFileSync(path.join(root,'plugin/desktop/plugin.js'),'utf8').replace("from 'react'",`from '${reactUrl}'`).replace("import {host,useValue} from '@hermes/plugin-sdk';",`const {host,useValue}=globalThis.${sdkKey};`);
const plugin=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).default;
const pending=[];let registration;
plugin.register({register:value=>registration=value,rest:()=>new Promise((resolve,reject)=>pending.push({resolve,reject}))});
let view;await act(async()=>{view=Renderer.create(registration.render());});
const text=()=>JSON.stringify(view.toJSON());
const evidence=key=>({state:'Local delivery evidence',recent:[{key,tool:'send_message',attempts:1,completed:1}]});
await act(async()=>pending.shift().resolve(evidence('default-only')));
assert(text().includes('default-only'));
await act(async()=>{view.root.findByType('button').props.onClick();});const old=pending.shift();
await act(async()=>state.profile.set('peer'));assert(!text().includes('default-only'));
const peer=pending.shift();await act(async()=>peer.resolve(evidence('peer-only')));
await act(async()=>old.resolve(evidence('late-default')));
assert(text().includes('peer-only'));assert(!text().includes('late-default'));
await act(async()=>state.connectionId.set('other-source'));
assert(!text().includes('peer-only'));
await act(async()=>pending.shift().reject(new Error('synthetic offline')));
assert(text().includes('Connection unavailable'));assert(text().includes('Local evidence unavailable'));assert(!text().includes('Loading local evidence'));
await act(async()=>{view.root.findByType('button').props.onClick();});await act(async()=>pending.shift().resolve(evidence('recovered')));
assert(text().includes('recovered'));assert(!text().includes('Connection unavailable'));
await act(async()=>{view.root.findByType('button').props.onClick();});await act(async()=>pending.shift().reject(new Error('synthetic offline')));
assert(text().includes('Previous evidence may be stale'));assert(text().includes('recovered'));
await act(async()=>{view.root.findByType('button').props.onClick();});const unmounted=pending.shift();await act(async()=>view.unmount());await act(async()=>unmounted.resolve(evidence('after-unmount')));
delete globalThis[sdkKey];
const report={ok:true,checks:['profile clears previous evidence','late response cannot replace current evidence','same-profile different connection clears evidence','empty error state','refresh recovery','failed refresh labels retained evidence stale','unmounted response ignored'],limits:['Component test with mocked SDK, not host routing evidence']};
fs.writeFileSync(path.join(root,'runtime/desktop-regression-result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));

