// Run against the explicitly isolated native Electron test shell only.
// Fixture profile setup and source staging are documented in docs/VALIDATION.md.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const root=path.resolve(import.meta.dirname,'..');
const {chromium}=await import(pathToFileURL(path.join(root,'runtime/ui-tests/node_modules/playwright-core/index.mjs')).href);
const port=fs.readFileSync(path.join(root,'runtime/desktop-user-data/DevToolsActivePort'),'utf8').split('\n')[0];
const browser=await chromium.connectOverCDP('http://127.0.0.1:'+port);
try{
 const packaged=process.argv.includes('--packaged');
 const expected=packaged?process.env.DEAD_DROP_DESKTOP_PACKAGED_RENDERER:pathToFileURL(path.join(root,'runtime/ui-tests/native-shell/dist/index.html')).href;
 assert(expected && expected.startsWith('file:///'),'Set the explicit packaged renderer file URL');
 const page=browser.contexts()[0].pages().find(p=>p.url().startsWith(expected));
 assert(page,'Refuse to test a non-isolated app window');
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.reload();page.setDefaultTimeout(30000);
 const pane=page.locator('section').filter({has:page.getByRole('heading',{name:'Dead Drop',exact:true})});
 await pane.getByText('desktop-confirmed',{exact:true}).waitFor();
 assert((await pane.innerText()).includes('Delivery confirmed'));
 assert((await pane.innerText()).includes('Pending or unconfirmed'));
 assert(!(await pane.innerText()).includes('PRIVATE_SYNTHETIC_BODY'));
 await pane.getByRole('button',{name:'Refresh status',exact:true}).click();
 await pane.getByRole('button',{name:'Refresh status',exact:true}).waitFor();
 await pane.screenshot({path:path.join(root,'runtime/ui-tests/pane-confirmed-final.png')});
 const geometry=await pane.evaluate(el=>({width:el.clientWidth,contentWidth:el.scrollWidth}));
 assert(geometry.contentWidth<=geometry.width,'Pane content overflows horizontally');
 await page.getByRole('button',{name:'desktop-peer',exact:true}).click();
 await pane.getByText('No exchanges yet',{exact:true}).waitFor();
 assert(!(await pane.innerText()).includes('desktop-confirmed'));
 assert(!(await pane.innerText()).includes('desktop-pending'));
 await pane.screenshot({path:path.join(root,'runtime/ui-tests/pane-peer-final.png')});
 await page.getByRole('button',{name:/^Switch to default/}).click();
 await pane.getByText('desktop-confirmed',{exact:true}).waitFor();
 assert.equal(errors.length,0,JSON.stringify(errors));
 const report={ok:true,host:packaged?'Packaged Hermes Desktop v0.22.7, build bf0203a794a0; isolated b200f5b backend':'Native Electron shell, copied Hermes build bf0203a794a0; isolated b200f5b backend',checks:['empty peer profile','confirmed and pending metadata','manual refresh','message-body exclusion','profile switch clears old evidence','switch back restores correct profile','no horizontal overflow at actual pane width','no renderer exceptions'],geometry,limits:['Synthetic local SQLite metadata','Updated pane staged in both disposable installed profiles',...(packaged?[]:['Not packaged executable end-to-end proof']),'No live GitHub, native scheduled execution or independent-human proof']};
 fs.writeFileSync(path.join(root,'runtime/desktop-native-result.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
