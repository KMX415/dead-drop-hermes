import React from 'react';
import {host,useValue} from '@hermes/plugin-sdk';
const h=React.createElement;
function Panel({ctx}) {
  const profile=useValue(host.state.profile);
  const gateway=useValue(host.state.gateway);
  const connection=useValue(host.state.connectionId);
  const route=JSON.stringify([connection,profile,gateway]);
  // A route change owns a fresh cache, even when two gateways share a profile name.
  return h(Evidence,{ctx,route,key:route});
}
function Evidence({ctx,route}) {
  const [data,setData]=React.useState(null);
  const [error,setError]=React.useState(false);
  const [loading,setLoading]=React.useState(false);
  const active=React.useRef(false);
  const request=React.useRef(0);
  async function refresh(){
    const id=++request.current;
    const current=()=>active.current && id===request.current && route===JSON.stringify([host.state.connectionId.get(),host.state.profile.get(),host.state.gateway.get()]);
    setLoading(true);
    try{const next=await ctx.rest('/status');if(current()){setData(next);setError(false);}}
    catch{if(current())setError(true);}
    finally{if(current())setLoading(false);}
  }
  React.useEffect(()=>{active.current=true;refresh();return()=>{active.current=false;request.current++;};},[]);
  return h('section',{style:{padding:20,color:'var(--ui-text-primary)',overflowWrap:'anywhere'}},
    h('h2',null,'Dead Drop'),h('p',null,'Agents keep the work moving. This view is optional.'),
    h('button',{onClick:refresh,disabled:loading},loading?'Checking…':'Refresh status'),
    error?h('p',{role:'alert'},'Connection unavailable. Previous evidence may be stale.'):null,
    h('p',null,data?.state || (error?'Local evidence unavailable':'Loading local evidence...')),
    h('ul',null,...(data?.recent||[]).map(row=>h('li',{key:row.key,style:{padding:'8px 0'}},
      h('strong',null,row.completed?'Delivery confirmed':'Pending or unconfirmed'),
      h('div',null,`${row.tool} · ${row.attempts} attempt(s)`),
      h('code',null,row.key),row.error?h('p',null,row.error):null))),
    h('p',null,'Delivery does not prove peer execution, review, or owner approval. No message contents are shown here.'));
}
export default {id:'dead-drop-hermes',name:'Dead Drop',defaultEnabled:false,register(ctx){ctx.register({id:'exchanges',area:'panes',title:'Dead Drop',data:{placement:'right',width:'340px'},render:()=>h(Panel,{ctx})});}};
