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
assert(!/\sstyle\s*=/.test(html), "no style attributes");
assert(js.includes('const API_BASE = "";'), "live endpoint fails closed until reviewed HTTPS origin is pinned");
assert(!/localStorage|sessionStorage|document\.cookie/.test(js), "no credential persistence");
assert(!/apiOrigin|apiUrl|apiBase/.test(js), "no query-controlled credential destination");
assert(js.includes("authEpoch") && js.includes("resetPrivate()"), "authorization race and reset guards present");
assert(js.includes('clear("private-accounts"); clear("fills")'), "private DOM cleared");
assert(js.includes('credentials:"omit"') && js.includes('cache:"no-store"'), "no cookie transport or browser caching");
assert(fixture.accounts.every(a => a.id.startsWith("PREVIEW-") && a.firm === "DEMO"));
assert(fixture.accounts.every(a => String(a.private?.label).startsWith("SYNTHETIC PREVIEW")));
assert(html.includes("SYNTHETIC DEMO / PREVIEW — NO LIVE ACCOUNTS OR RESULTS"));
assert(html.includes("Futures trading involves substantial risk of loss and is not suitable for all investors."));
console.log("PASS dashboard CSP, fail-closed API, memory-only auth, private reset, synthetic fixture");
