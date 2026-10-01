import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import vm from "node:vm";

const html = readFileSync(new URL("./index.html", import.meta.url), "utf8");
const fixture = JSON.parse(readFileSync(new URL("./mock.json", import.meta.url), "utf8"));
const css = html.match(/<style>([\s\S]*?)<\/style>/)?.[1];
const js = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert(css && js, "inline assets exist");
new vm.Script(js);
for (const content of [css, js]) {
  const hash = createHash("sha256").update(content).digest("base64");
  assert(html.includes("'sha256-" + hash + "'"), "CSP pins exact inline content");
}
assert(!html.includes("unsafe-inline") && !html.includes("unsafe-eval"));
assert(!/\sstyle\s*=/.test(html), "no inline styles");

const origin = "https://ftb-live.cmrealestate808.workers.dev";
assert(js.includes('const API_BASE = "' + origin + '";'), "reviewed API origin is pinned");
assert(html.includes("connect-src 'self' " + origin + ";"), "CSP permits only the reviewed API origin");
assert(js.includes('credentials:"omit"') && js.includes('cache:"no-store"'), "no cookie transport or browser caching");
assert(!/localStorage|sessionStorage|document\.cookie/.test(js), "no credential persistence");

for (const expected of ["#accounts", "#automation", "strategy=Midas", "Sort by", "strategy-chips", "data-sort", "writeHash", "parseHash"]) {
  assert(html.includes(expected) || js.includes(expected), "linkable strategy state includes " + expected);
}
for (const heading of ["How it works", "Current status", "Accuracy testing", "What has been implemented", "Testing programme", "Potential risks"]) {
  assert(html.includes(heading), "automation panel exists: " + heading);
}
assert(js.includes("item.approved === true"), "free text is approved-only");
assert(js.includes("not yet measured"), "null values render honestly");
assert(!/flatBy|16:09|flat-by/i.test(html + JSON.stringify(fixture)), "no schedule or flat-state disclosure");
for (const metric of ["Fills compared", "Worst ticks", "Worse fills", "Missed entries", "Protective stops", "Ordered closes", "Last approved incident"]) {
  assert(js.includes(metric), "automation includes " + metric);
}

const disclaimer = "The accounts on this page are trading live in a simulated environment.";
assert.equal(html.split(disclaimer).length - 1, 3, "approved disclaimer appears on both tabs and footer");
assert(html.includes("Because the environment is simulated, fills may differ in a live trading environment."));
assert(html.includes("Risk disclosure.") && html.includes("Hypothetical performance disclaimer."));

assert.equal(fixture.accounts.length, 4, "fixture has four strategy entries");
assert.deepEqual(new Set(fixture.accounts.map(a => a.product)), new Set(["Continuum", "Midas", "Slipstream", "Keystone"]));
assert.equal(fixture.accounts[0].accountKey, fixture.accounts[1].accountKey, "one account can have two strategies");
assert.equal(fixture.accounts[2].id, fixture.accounts[3].id, "masked aliases can collide");
assert.notEqual(fixture.accounts[2].accountKey, fixture.accounts[3].accountKey, "colliding aliases remain separate opaque accounts");
assert(fixture.accounts.every(a => /^···\d{3}$/.test(a.id) && /^PREVIEW-OPAQUE-KEY-[A-Z]$/.test(a.accountKey)));
assert(fixture.accounts.every(a => a.openTrades === null && a.netToday === null));
assert(fixture.daily.net === null && Object.keys(fixture.calendar).length === 0, "no mock performance result");
assert(fixture.automation.implemented.every(x => x.approved === false));
assert(fixture.automation.risks.every(x => x.approved === false));
assert(!/positions|fillsToday|workingOrders|price|balance|private/i.test(JSON.stringify(fixture)), "fixture contains no public execution detail");
assert(!html.includes("All performance figures are backtested or validation-run results"), "retired footer claim removed");

function sourceFunction(name) {
  const start = js.indexOf("function " + name + "(");
  assert(start >= 0, name + " exists");
  let depth = 0, opened = false;
  for (let index = start; index < js.length; index++) {
    if (js[index] === "{") { depth++; opened = true; }
    if (js[index] === "}" && opened && --depth === 0) return js.slice(start, index + 1);
  }
  throw new Error("could not extract " + name);
}
const modelContext = { knownNumber: value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)), selectedStrategy: "Midas" };
vm.runInNewContext(sourceFunction("groupToday") + sourceFunction("calendarValue") + sourceFunction("filteredReport") + "this.groupToday = groupToday; this.calendarValue = calendarValue; this.filteredReport = filteredReport;", modelContext);
assert.equal(modelContext.groupToday([{product:"Midas",netToday:4},{product:"Midas",netToday:6}], "Midas"), 10, "strategy heading totals verified values");
assert.equal(modelContext.groupToday([{product:"Midas",netToday:null}], "Midas"), null, "unknown group total stays unknown");
assert.equal(modelContext.calendarValue({total:100,byStrategy:{Midas:{total:20,byAccount:{opaque:5}}}}, ""), 20, "strategy filter narrows calendar total");
assert.equal(modelContext.calendarValue({total:100,byStrategy:{Midas:{total:20,byAccount:{opaque:5}}}}, "opaque"), 5, "strategy filter narrows calendar account");
assert.equal(JSON.stringify(modelContext.filteredReport({daily:{date:"x",trades:9,wins:8,losses:1,net:90,byProduct:[{product:"Midas",trades:2,net:20}]} })), JSON.stringify({date:"x",trades:2,wins:null,losses:null,net:20,byProduct:[{product:"Midas",trades:2,net:20}]}), "strategy filter narrows day report without inventing wins/losses");
console.log("PASS Q857 tabs, hash state, strict fixture privacy, approved-only automation, disclaimer, CSP");
