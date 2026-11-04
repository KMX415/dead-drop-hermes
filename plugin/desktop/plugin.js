import React from 'react';
const h=React.createElement;
function Panel({ctx}) {
  const [data,setData]=React.useState(null);
  const [error,setError]=React.useState(false);
  const [loading,setLoading]=React.useState(false);
  async function refresh(){setLoading(true);try{setData(await ctx.rest('/status'));setError(false);}catch{setError(true);}finally{setLoading(false);}}
  React.useEffect(()=>{refresh();},[]);
  return h('section',{style:{padding:20,color:'var(--ui-text-primary)'}},
    h('h2',null,'Dead Drop'),h('p',null,'Agents keep the work moving. This view is optional.'),
    h('button',{onClick:refresh,disabled:loading},loading?'Checking…':'Refresh status'),
    error?h('p',{role:'alert'},'Connection unavailable. Previous evidence may be stale.'):null,
    h('p',null,data?.state || 'Loading local evidence…'),
    h('ul',null,...(data?.recent||[]).map(row=>h('li',{key:row.key,style:{padding:'8px 0'}},
      h('strong',null,row.completed?'Delivery confirmed':'Pending or unconfirmed'),
      h('div',null,`${row.tool} · ${row.attempts} attempt(s)`),
      h('code',null,row.key),row.error?h('p',null,row.error):null))),
    h('p',null,'Delivery does not prove peer execution, review, or owner approval. No message contents are shown here.'));
}
export default {id:'dead-drop-hermes',name:'Dead Drop',defaultEnabled:false,register(ctx){ctx.register({id:'exchanges',area:'panes',title:'Dead Drop',data:{placement:'right',width:'340px'},render:()=>h(Panel,{ctx})});}};
