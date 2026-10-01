'use strict';
// Standalone offline Playwright regression suite. Every network response is fulfilled locally.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {NOW,KEYS,DATES,MALICIOUS,APPROVED_DISCLAIMER,fixture,privateFixture} = require('./fixtures.cjs');
const TARGET = process.env.PROOF_HTML || path.join(__dirname,'..','index.html');
const ASSETS = path.join(path.dirname(TARGET),'..','assets');
const ARTIFACTS = path.join(__dirname,'artifacts');
const ORIGIN = 'https://synthetic-proof.test';
const API = 'https://ftb-live.cmrealestate808.workers.dev';
const normalize = text => text.replace(/\s+/g,' ').trim();
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
const results = [];
let browser;
async function test(name, fn) {
  const started=Date.now();
  try { await fn(); results.push({name,status:'passed',ms:Date.now()-started}); console.log('PASS '+name); }
  catch(error) { results.push({name,status:'failed',ms:Date.now()-started,error:error.stack}); console.error('FAIL '+name+'\n'+error.message); }
}
function deferred() { let resolve; const promise=new Promise(r=>resolve=r); return {promise,resolve}; }
async function harness(options={}) {
  const context=await browser.newContext({viewport:options.viewport||{width:1400,height:1000},colorScheme:'dark',timezoneId:'UTC',locale:'en-US',serviceWorkers:'block'});
  const page=await context.newPage(); page.setDefaultTimeout(5000);
  const state={public:fixture(),private:privateFixture(),publicStatus:200,privateStatus:200,loginStatus:200,publicCalls:0,privateCalls:0,loginCalls:0,requests:[],unexpected:[],errors:[],policy:[],...options.state};
  page.on('pageerror',e=>state.errors.push(e.message));
  page.on('console',msg=>{if(msg.type()==='error' && /Content Security Policy|Refused to|violates.*directive/i.test(msg.text())) state.policy.push(msg.text());});
  await page.addInitScript(()=>{ window.__SYNTHETIC_XSS__=false; window.__CSP_VIOLATIONS__=[]; document.addEventListener('securitypolicyviolation',e=>window.__CSP_VIOLATIONS__.push({directive:e.violatedDirective,blocked:e.blockedURI})); });
  await page.clock.install({time:NOW});
  await context.route('**/*', async route=>{
    const request=route.request(), url=new URL(request.url()); state.requests.push({url:request.url(),method:request.method(),headers:request.headers()});
    const json=(body,status=200)=>route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Content-Type,Authorization','Access-Control-Allow-Methods':'GET,POST,OPTIONS'},body:JSON.stringify(body)});
    if (url.origin===API) {
      if(request.method()==='OPTIONS') return json({},204);
      if(url.pathname==='/api/public') { state.publicCalls++; if(state.publicGate) await state.publicGate.promise; return json(state.public,state.publicStatus); }
      if(url.pathname==='/api/private') { state.privateCalls++; if(state.privateGate) await state.privateGate.promise; return json(state.private,state.privateStatus); }
      if(url.pathname==='/api/login') { state.loginCalls++; if(state.loginGate) await state.loginGate.promise; return json({token:'SYNTHETIC_MEMORY_ONLY_SESSION'},state.loginStatus); }
    }
    if(url.origin===ORIGIN && url.pathname.endsWith('/mock.json')) return json(state.public,state.publicStatus);
    if(url.origin===ORIGIN && url.pathname==='/proof-of-concept/') return route.fulfill({status:200,contentType:'text/html',body:fs.readFileSync(TARGET,'utf8')});
    if(url.hostname==='fonts.googleapis.com') return route.fulfill({status:200,contentType:'text/css',body:'/* SYNTHETIC OFFLINE: external fonts excluded */'});
    if(url.origin===ORIGIN && url.pathname.startsWith('/assets/')) { const file=path.join(ASSETS,path.basename(url.pathname)); if(fs.existsSync(file)) return route.fulfill({status:200,contentType:file.endsWith('.css')?'text/css':file.endsWith('.png')?'image/png':'image/svg+xml',body:fs.readFileSync(file)}); }
    if(url.origin===ORIGIN && /\.(png|svg)$/.test(url.pathname)) return route.fulfill({status:200,contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="150" height="40"><rect width="150" height="40" fill="#11262b"/><text x="7" y="25" fill="#e9f2ee" font-size="12">SYNTHETIC TEST</text></svg>'});
    state.unexpected.push(request.url()); return route.abort('blockedbyclient');
  });
  await page.goto(ORIGIN+'/proof-of-concept/'+(options.url||'#accounts'),{waitUntil:'domcontentloaded'});
  async function ready() { await page.waitForFunction(()=>document.querySelectorAll('#accounts tr:not(.group-row) .feed-dot').length===4); }
  async function poll() { const before=state.publicCalls; await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange'))); await page.waitForFunction(()=>true); for(let i=0;i<100&&state.publicCalls===before;i++) await delay(10); assert.ok(state.publicCalls>before,'poll should request the public feed'); await delay(40); }
  async function login() { await page.locator('#auth-toggle').click(); await page.locator('#password').fill('SYNTHETIC OFFLINE TEST INPUT'); await page.locator('#auth button[type="submit"]').click(); await page.waitForFunction(()=>document.body.classList.contains('authed') && document.querySelectorAll('#accounts .feed-dot').length===5); }
  async function clean() { assert.deepEqual(state.unexpected,[],'no unhandled or real network requests'); assert.deepEqual(state.errors,[],'no uncaught browser errors'); assert.deepEqual(state.policy,[],'no console CSP errors'); assert.deepEqual(await page.evaluate(()=>window.__CSP_VIOLATIONS__),[],'no CSP violations'); }
  return {context,page,state,ready,poll,login,clean,close:()=>context.close()};
}
async function withPage(options, fn) { const h=await harness(options); try { await fn(h); await h.clean(); } finally { await h.close(); } }
async function rows(page) { return page.locator('#accounts tr').evaluateAll(rows=>rows.filter(row=>row.querySelector('td[data-label="Account"]')).map(row=>Object.fromEntries([...row.querySelectorAll('td')].map(td=>[td.dataset.label,td.textContent.trim()])))); }
async function assertPrivateCleared(page) {
  assert.equal(await page.locator('#positions').textContent(),''); assert.equal(await page.locator('#private-accounts').textContent(),''); assert.equal(await page.locator('#fills').textContent(),'');
  assert.equal(await page.locator('body').evaluate(e=>e.classList.contains('authed')),false);
  assert.doesNotMatch(await page.locator('body').textContent(),/SYNTHETIC_PRIVATE_POSITION|SYNTHETIC_PRIVATE_ORDER|SYNTHETIC_PRIVATE_FILL/);
}
async function activateTab(page, tab) {
  await page.locator('#tab-link-'+tab).click();
  await page.locator('#tab-'+tab).waitFor({state:'visible'});
  await page.locator('#tab-'+(tab==='accounts'?'automation':'accounts')).waitFor({state:'hidden'});
}
async function screenshot(page,name) {
  await page.evaluate(()=>{if(!document.querySelector('#synthetic-test-label')){const b=document.createElement('div');b.id='synthetic-test-label';b.className='disclaimer';b.textContent='SYNTHETIC OFFLINE TEST FIXTURE — no real accounts, credentials, or results';document.body.prepend(b);}});
  await page.evaluate(()=>window.scrollTo(0,0)); await page.screenshot({path:path.join(ARTIFACTS,name+'.png'),fullPage:true});
}

async function launchBrowser() {
  const requested = process.env.CHROMIUM_PATH;
  if(requested && !fs.existsSync(requested)) throw new Error('CHROMIUM_PATH does not exist: '+requested);
  const candidates = [
    requested,
    chromium.executablePath(),
    '/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    process.env.PROGRAMFILES && path.join(process.env.PROGRAMFILES,'Google','Chrome','Application','chrome.exe'),
    process.env['PROGRAMFILES(X86)'] && path.join(process.env['PROGRAMFILES(X86)'],'Google','Chrome','Application','chrome.exe'),
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA,'Google','Chrome','Application','chrome.exe'),
    process.env['PROGRAMFILES(X86)'] && path.join(process.env['PROGRAMFILES(X86)'],'Microsoft','Edge','Application','msedge.exe')
  ].filter(Boolean);
  const executablePath=candidates.find(file=>fs.existsSync(file));
  if(!executablePath) throw new Error('No Chromium browser found. Run npx playwright install chromium, or set CHROMIUM_PATH to Chrome/Chromium/Edge.');
  console.log('Browser: '+executablePath);
  return chromium.launch({executablePath,headless:true});
}
function writeReport() {
  const report={generatedAt:new Date().toISOString(),target:TARGET,sourceSha256:fs.existsSync(TARGET)?crypto.createHash('sha256').update(fs.readFileSync(TARGET)).digest('hex'):null,fixtureLabel:'SYNTHETIC OFFLINE ONLY',passed:results.filter(r=>r.status==='passed').length,failed:results.filter(r=>r.status==='failed').length,blocked:results.filter(r=>r.status==='blocked').length,results};
  fs.writeFileSync(path.join(ARTIFACTS,'results.json'),JSON.stringify(report,null,2));
  console.log('\n'+report.passed+' passed, '+report.failed+' failed, '+report.blocked+' blocked. Report: '+path.join(ARTIFACTS,'results.json'));
  process.exitCode=report.failed||report.blocked?1:0;
}

const {START,END,projection,unavailable}=require('./session-fixtures.cjs');
(async()=>{
  fs.mkdirSync(ARTIFACTS,{recursive:true});browser=await launchBrowser();
  await test('Exact CSP hashes and fixed API origin',async()=>{const html=fs.readFileSync(TARGET,'utf8');const csp=html.match(/Content-Security-Policy" content="([^"]+)/)[1];for(const tag of ['style','script']){const body=html.match(new RegExp('<'+tag+'>([\\s\\S]*?)</'+tag+'>'))[1];assert.ok(csp.includes("'sha256-"+crypto.createHash('sha256').update(body).digest('base64')+"'"));}assert.doesNotMatch(csp,/unsafe-inline|unsafe-eval/);assert.equal((html.match(/<script>/g)||[]).length,1);assert.doesNotMatch(html,/style=/);});
  await test('One compact results table and all requested columns',()=>withPage({},async h=>{await h.ready();assert.equal(await h.page.locator('#tab-accounts table').count(),1);assert.equal(await h.page.locator('#tab-accounts .card').count(),1);assert.equal(await h.page.locator('#open-trades,#positions,#calendar,#report,#health').count(),0);assert.deepEqual(await h.page.locator('#account-headings th').allTextContents(),['Account','Account Balance','Current Open P&L','Contract Size',"Today's Profit","Yesterday's Profit",'Tester vs. Account P&L divergence','Missed tester trades','Feed']);assert.equal((await rows(h.page)).length,4);assert.deepEqual(await h.page.locator('.group-heading strong').allTextContents(),['Continuum','Midas','Slipstream']);}));
  await test('Daily and comparison values cannot relabel UTC totals or fabricate zero',()=>withPage({},async h=>{await h.ready();for(const row of await rows(h.page))for(const key of ["Today's Profit","Yesterday's Profit",'Tester vs. Account P&L divergence','Missed tester trades'])assert.equal(row[key],'Unavailable');}));
  await test('Verified account valuation and contract size; no equity fallback',()=>withPage({},async h=>{await h.ready();const records=await rows(h.page);assert.equal(records[1]['Account Balance'],'$50,125.00');assert.equal(records[1]['Current Open P&L'],'$5.00');assert.equal(records[0]['Account Balance'],'Unavailable');assert.equal(records[0]['Current Open P&L'],'Unavailable');assert.equal(records[3]['Contract Size'],'3');assert.equal(records[1]['Contract Size'],'Unavailable');}));
  await test('Stale/future/malformed financial source is unavailable for current open P&L',()=>withPage({state:{public:(()=>{const d=fixture();d.accounts[0].balanceAsOfTs=NOW-120001;d.accounts[1].balanceAsOfTs=NOW+60000;d.accounts[2].currentBalance='0';d.accounts[3].configuredContracts=999;return d;})()}},async h=>{await h.ready();for(const r of await rows(h.page))assert.equal(r['Current Open P&L'],'Unavailable');assert.equal((await rows(h.page))[3]['Contract Size'],'Unavailable');}));
  await test('Per-account green/red accessible dots use fresh heartbeat and link',()=>withPage({},async h=>{await h.ready();assert.equal(await h.page.locator('.feed-dot.online').count(),3);assert.equal(await h.page.locator('.feed-dot[aria-label="Offline"]').count(),1);assert.equal(await h.page.locator('#accounts tr:not(.group-row) td:last-child .feed-dot').count(),4);}));
  await test('Elapsed stale heartbeat turns all dots red without changing financial availability',()=>withPage({},async h=>{await h.ready();h.state.public.uptime.lastUpdateAgeS=130;await h.page.clock.fastForward(121000);assert.equal(await h.page.locator('.feed-dot.online').count(),0);}));
  await test('Unknown links and watcher down remain red',()=>withPage({state:{public:(()=>{const d=fixture();d.health.watcherUp=false;return d;})()}},async h=>{await h.ready();assert.equal(await h.page.locator('.feed-dot.online').count(),0);}));
  await test('Filter, sorting, grouping and hash survive tab switches',()=>withPage({},async h=>{await h.ready();await h.page.locator('#strategy-chips').getByRole('button',{name:'Midas',exact:true}).click();assert.equal((await rows(h.page)).length,2);await h.page.selectOption('#sort-by','account');await h.page.locator('#sort-direction').click();await activateTab(h.page,'automation');await activateTab(h.page,'accounts');assert.equal((await rows(h.page)).length,2);assert.equal(await h.page.locator('.group-heading strong').textContent(),'Midas');assert.match(h.page.url(),/strategy=Midas/);}));
  await test('Six Automation panels and approved content gates preserved',()=>withPage({},async h=>{await h.ready();await activateTab(h.page,'automation');assert.equal(await h.page.locator('.automation-grid > .card').count(),6);assert.doesNotMatch(await h.page.locator('#tab-automation').textContent(),/UNAPPROVED/);assert.match(await h.page.locator('#tab-automation').textContent(),/SYNTHETIC approved protection/);}));
  await test('Approved disclaimer and public privacy preserved',()=>withPage({},async h=>{await h.ready();assert.ok(normalize(await h.page.locator('#tab-accounts .disclaimer').textContent()).includes(normalize(APPROVED_DISCLAIMER)));assert.doesNotMatch(await h.page.locator('body').textContent(),/RAW-ACCOUNT|PRIVATE MUST NOT APPEAR|INVALID KEY/);assert.equal(await h.page.evaluate(()=>window.__SYNTHETIC_XSS__),false);assert.equal(await h.page.evaluate(()=>localStorage.length+sessionStorage.length),0);}));
  await test('Login/logout preserves authenticated boundaries and removes private account rows',()=>withPage({},async h=>{await h.ready();await h.login();assert.equal((await rows(h.page)).length,5);assert.doesNotMatch(await h.page.locator('body').textContent(),/SYNTHETIC_PRIVATE_POSITION|SYNTHETIC_PRIVATE_ORDER|SYNTHETIC_PRIVATE_FILL/);await h.page.locator('#auth-toggle').click();assert.equal((await rows(h.page)).length,4);assert.equal(await h.page.locator('#password').inputValue(),'');}));
  await test('Late authentication response cannot restore private rows after cancellation',()=>withPage({state:{loginGate:deferred()}},async h=>{await h.ready();await h.page.locator('#auth-toggle').click();await h.page.locator('#password').fill('SYNTHETIC');await h.page.locator('#auth button').click();for(let i=0;i<100&&!h.state.loginCalls;i++)await delay(10);await h.page.locator('#auth-toggle').click();h.state.loginGate.resolve();await delay(120);assert.equal(h.state.privateCalls,0);assert.equal((await rows(h.page)).length,4);}));
  await test('Failed refresh retains honest stale data without crashing',()=>withPage({},async h=>{await h.ready();h.state.publicStatus=503;await h.poll();assert.match(await h.page.locator('#status-note').textContent(),/failed/);assert.equal((await rows(h.page)).length,4);}));
  await test('Untrusted query cannot redirect authentication endpoint',()=>withPage({url:'?api=https://untrusted.invalid#accounts'},async h=>{await h.ready();await h.login();assert.ok(h.state.requests.filter(r=>/api\/(login|private)/.test(r.url)).every(r=>r.url.startsWith(API)));}));
  for(const viewport of [{width:1400,height:1000},{width:375,height:900}])await test('Table rows, scroll containment and screenshots '+viewport.width,()=>withPage({viewport},async h=>{await h.ready();assert.equal(await h.page.locator('#accounts tr:not(.group-row)').first().evaluate(x=>getComputedStyle(x).display),'table-row');for(const tab of ['accounts','automation']){await activateTab(h.page,tab);const w=await h.page.evaluate(()=>({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));assert.ok(w.scroll<=w.client+1,JSON.stringify(w));await screenshot(h.page,'compact-'+tab+'-'+viewport.width);}if(viewport.width===375){await activateTab(h.page,'accounts');const x=await h.page.locator('.account-table-wrap').evaluate(x=>({width:x.clientWidth,scroll:x.scrollWidth}));assert.ok(x.scroll>x.width);}}));
  const contractFixture=()=>{const d=fixture();d.accounts[0].linkOk=true;d.accounts[0].sessionMetrics=projection(NOW);return d;};
  const contractCells=page=>page.locator('tr[data-account-key="'+KEYS[0]+'"]').evaluate(row=>Object.fromEntries([...row.querySelectorAll('td')].map(td=>[td.dataset.label,td.textContent.trim()])));
  await test('New verified contract binds exact session values to opaque row only',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'$40.00');assert.equal(r["Yesterday's Profit"],'$90.00');assert.equal(r['Missed tester trades'],'1');assert.match(r['Tester vs. Account P&L divergence'],/10\.00/);const others=await h.page.locator('tr[data-account-key="'+KEYS[1]+'"] td[data-label="Today\'s Profit"]').textContent();assert.equal(others,'Unavailable');}));
  await test('Partial coverage/generation or quantity mismatch never becomes a zero count',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();for(const reason of ['incomplete_coverage','generation_mismatch','quantity_mismatch','pending_entries']){const a=h.state.public.accounts[0];a.sessionMetrics.today=unavailable(a.sessionMetrics.today,false,reason);a.sessionMetrics.comparison=unavailable(a.sessionMetrics.comparison,true,reason);await h.poll();const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'Unavailable');assert.equal(r["Yesterday's Profit"],'$90.00');assert.equal(r['Missed tester trades'],'Unavailable');assert.equal(r['Tester vs. Account P&L divergence'],'Unavailable');}}));
  await test('New-schema captured values expire despite new API receipt; closed yesterday survives',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();await h.page.clock.setSystemTime(new Date(NOW+120001));await h.poll();const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'Unavailable');assert.equal(r["Yesterday's Profit"],'$90.00');assert.equal(r['Missed tester trades'],'Unavailable');}));
  await test('Malformed future/UTC projection never renders numeric session values',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();for(const mutate of [m=>m.timezone='UTC',m=>m.today.asOfTs=NOW+60000,m=>m.today.startTs++,m=>m.today.profit='0',m=>m.today.proof={sourceComplete:true}]){h.state.public=contractFixture();mutate(h.state.public.accounts[0].sessionMetrics);await h.poll();assert.equal((await contractCells(h.page))["Today's Profit"],'Unavailable');}}));
  await test('Measured zero stays visible while unavailable comparison stays unknown',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();const m=h.state.public.accounts[0].sessionMetrics;m.today.profit=0;m.comparison.pnlDivergence=0;m.comparison.missedTesterTrades=0;await h.poll();let r=await contractCells(h.page);assert.equal(r["Today's Profit"],'$0.00');assert.equal(r['Missed tester trades'],'0');m.comparison=unavailable(m.comparison,true);await h.poll();r=await contractCells(h.page);assert.equal(r['Missed tester trades'],'Unavailable');}));
  await test('Complete close visible in break and becomes Yesterday at18NY',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();h.state.public.accounts[0].sessionMetrics=projection(END);await h.page.clock.setSystemTime(new Date(END+1800000));await h.poll();assert.equal((await contractCells(h.page))["Today's Profit"],'$40.00');assert.match(await h.page.locator('#session-note').textContent(),/Between trading sessions/);await h.page.clock.setSystemTime(new Date(END+3600000));await h.poll();const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'Unavailable');assert.equal(r["Yesterday's Profit"],'$40.00');assert.equal(r['Missed tester trades'],'Unavailable');}));
  await test('Spring/fall DST contracts use exact NY windows in rendered cells',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();for(const [date,start,end] of [['2026-03-08','2026-03-07T23:00:00Z','2026-03-08T21:00:00Z'],['2026-11-01','2026-10-31T22:00:00Z','2026-11-01T22:00:00Z']]){const now=Date.parse(date+'T12:00:00Z');h.state.public=contractFixture();const m=h.state.public.accounts[0].sessionMetrics;m.today={...m.today,date,startTs:Date.parse(start),endTs:Date.parse(end),asOfTs:now};await h.page.clock.setSystemTime(new Date(now));await h.poll();assert.equal((await contractCells(h.page))["Today's Profit"],'$40.00');m.today.endTs=m.today.startTs+23*3600000;await h.poll();assert.equal((await contractCells(h.page))["Today's Profit"],'Unavailable');}}));
  await test('Financial verification cannot turn watcher-down dot green',()=>withPage({state:{public:(()=>{const d=contractFixture();d.health.watcherUp=false;return d;})()}},async h=>{await h.ready();assert.equal((await contractCells(h.page))["Today's Profit"],'$40.00');assert.equal(await h.page.locator('.feed-dot.online').count(),0);}));
  for(const viewport of [{width:1400,height:1000},{width:375,height:900}])await test('Verified contract compact table and accessible dots '+viewport.width,()=>withPage({viewport,state:{public:contractFixture()}},async h=>{await h.ready();assert.equal((await contractCells(h.page))["Today's Profit"],'$40.00');assert.equal(await h.page.locator('.feed-dot.online').count(),3);assert.equal(await h.page.locator('tr[data-account-key="'+KEYS[0]+'"]').evaluate(x=>getComputedStyle(x).display),'table-row');const w=await h.page.evaluate(()=>({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));assert.ok(w.scroll<=w.client+1);await screenshot(h.page,'verified-session-accounts-'+viewport.width);}));

  await test('Pending response cannot keep expired session values or health dots visible',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();const gate=deferred();h.state.publicGate=gate;try{await h.page.clock.fastForward(121000);const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'Unavailable');assert.equal(r["Yesterday's Profit"],'$90.00');assert.equal(r['Missed tester trades'],'Unavailable');assert.equal(await h.page.locator('.feed-dot.online').count(),0);}finally{gate.resolve();}}));
  await test('Pending response cannot delay NY day rollover of cached complete close',()=>withPage({state:{public:contractFixture()}},async h=>{await h.ready();h.state.public.accounts[0].sessionMetrics=projection(END);await h.page.clock.setSystemTime(new Date(END+1800000));await h.poll();const gate=deferred();h.state.publicGate=gate;try{await h.page.clock.setSystemTime(new Date(END+3600000));await h.page.clock.fastForward(15000);const r=await contractCells(h.page);assert.equal(r["Today's Profit"],'Unavailable');assert.equal(r["Yesterday's Profit"],'$40.00');assert.equal(r['Missed tester trades'],'Unavailable');assert.match(await h.page.locator('#session-note').textContent(),/2026-10-02/);}finally{gate.resolve();}}));
  await test('Today sorting uses verified values and leaves unknown rows last',()=>withPage({state:{public:(()=>{const d=contractFixture();d.accounts[1].linkOk=true;d.accounts[1].sessionMetrics=projection(NOW);d.accounts[1].sessionMetrics.today.profit=5;return d;})()}},async h=>{await h.ready();await h.page.selectOption('#sort-by','today');assert.deepEqual(await h.page.locator('#accounts tr[data-account-key]').evaluateAll(rows=>rows.map(row=>row.dataset.accountKey)),[KEYS[1],KEYS[0],KEYS[2],KEYS[3]]);await h.page.locator('#sort-direction').click();assert.deepEqual(await h.page.locator('#accounts tr[data-account-key]').evaluateAll(rows=>rows.map(row=>row.dataset.accountKey)),[KEYS[0],KEYS[1],KEYS[2],KEYS[3]]);}));

  await browser.close();writeReport();
})().catch(async e=>{console.error(e);if(browser)await browser.close();process.exitCode=1;});
