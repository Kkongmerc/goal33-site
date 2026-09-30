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
const ageHelpers = js.match(/  const ageText = [^\r\n]+\r?\n  const ageLabel = [\s\S]*?;\r?\n/)?.[0];
assert(ageHelpers, "source age formatter is testable");
const ageContext = {};
vm.runInNewContext(ageHelpers + "this.testAgeLabel = ageLabel;", ageContext);
assert.equal(ageContext.testAgeLabel(3, 3), "Updated 3 s ago");
assert.equal(ageContext.testAgeLabel(3, 903), "Feed updated 3 s ago · Account data 15 min ago (delayed)");
assert.equal(ageContext.testAgeLabel(Infinity, 903), "No verified update");
for (const content of [css, js]) {
  const hash = createHash("sha256").update(content).digest("base64");
  assert(html.includes("'sha256-" + hash + "'"), "CSP pins exact inline content");
}
assert(!html.includes("unsafe-inline") && !html.includes("unsafe-eval"));
assert(!/\sstyle\s*=/.test(html), "no style attributes");
const origin = "https://ftb-live.cmrealestate808.workers.dev";
assert(js.includes('const API_BASE = "' + origin + '";'), "reviewed API origin is pinned");
assert(html.includes("connect-src 'self' " + origin + ";"), "CSP permits only the reviewed API origin");
assert(js.includes('const validOrigin = API_BASE === "' + origin + '";'));
assert(!/localStorage|sessionStorage|document\.cookie/.test(js), "no credential persistence");
assert(!/apiOrigin|apiUrl|apiBase/.test(js), "no query-controlled credential destination");
assert(js.includes("authEpoch") && js.includes("resetPrivate()"), "authorization race and reset guards present");
assert(js.includes('clear("private-accounts"); clear("fills")'), "private DOM cleared");
assert(!js.includes("p.label || a.id"), "full private account labels are not rendered");
assert(js.includes("visibleKeys.has(x.accountKey)"), "health joins by opaque key, not colliding label");
assert(js.includes("o.value = a.accountKey"), "calendar joins by opaque key");
assert(html.includes("<th>Trading</th>") && html.includes("<th>Multiplier</th>"));
for (const label of ["Continuum (MNQ Book)", "Midas (MGC Book)", "Slipstream"])
  assert(js.includes(label));
assert(js.includes('credentials:"omit"') && js.includes('cache:"no-store"'), "no cookie transport or browser caching");
assert(fixture.accounts.every(a => a.id.startsWith("PREVIEW-") && a.firm === "DEMO"));
assert(fixture.accounts.every(a => a.accountKey.startsWith("PREVIEW-KEY-")));
assert(Object.keys(fixture.calendar["2026-09-30"].byAccount).every(key => key.startsWith("PREVIEW-KEY-")));
assert(fixture.accounts.some(a => a.multiplierStatus === "unverified" && a.configuredMultiplier === null));
assert(fixture.accounts.every(a => String(a.private?.label).startsWith("SYNTHETIC PREVIEW")));
assert(html.includes("SYNTHETIC DEMO / PREVIEW — NO LIVE ACCOUNTS OR RESULTS"));
assert(html.includes("Futures trading involves substantial risk of loss and is not suitable for all investors."));
console.log("PASS dashboard CSP, fixed API, opaque-key joins, multiplier gate, private reset, synthetic fixture");
