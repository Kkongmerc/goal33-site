import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const path = new URL("./index.html", import.meta.url);
const html = readFileSync(path, "utf8");
const inline = html.split("<script>")[1].split("</script>")[0];

function productionHelpers() {
  const start = inline.indexOf('  const mock =');
  const end = inline.indexOf('  function renderStatus()');
  assert.ok(start >= 0 && end > start, "account helpers must remain before rendering");
  const context = {
    URLSearchParams, Intl, Number, Date, Set, Array,
    API_BASE: "https://ftb-live.cmrealestate808.workers.dev",
    location: { search: "" },
    document: { body: { classList: { add() {} } }, getElementById() { return {}; } }
  };
  vm.runInNewContext(`(()=>{${inline.slice(start, end)}\nglobalThis.helpers={shownAccounts,strategyLabel,historyColumns,accountCells,accountAsOf};})()`, context);
  return context.helpers;
}

const row = (key, id, extra = {}) => ({ accountKey: key, id, product: "Continuum", ...extra });

test("account rows retain same-mask identities and show unknown money honestly", () => {
  const helpers = productionHelpers();
  const rows = helpers.shownAccounts({ accounts: [
    row("A".repeat(22), "···135"), row("B".repeat(22), "···135")
  ] });
  assert.equal(rows.length, 2);
  const columns = helpers.historyColumns(rows);
  const cells = helpers.accountCells(rows[0], columns);
  assert.equal(cells.find(([label]) => label === "Starting balance")[1], "not yet measured");
  assert.equal(cells.find(([label]) => label === "Current balance (equity)")[1], "not yet measured");
  assert.equal(cells.find(([label]) => label === "Today P&L")[1], "not yet measured");
  assert.equal(cells.some(([label]) => /multiplier/i.test(label)), false);
  const equity = helpers.accountCells({ ...rows[0], currentEquity: 1234.5 }, columns);
  assert.equal(equity.find(([label]) => label === "Current balance (equity)")[1], "$1,234.50");
  assert.match(helpers.accountAsOf({ ts: Date.parse("2026-09-30T12:00:00Z") }), /Sep 30, 2026/);
});

test("Slipstream contract label uses verified configuredContracts, never position or multiplier", () => {
  const helpers = productionHelpers();
  assert.equal(helpers.strategyLabel({ product: "Slipstream", configuredContracts: 3,
    configuredMultiplier: 99, positions: [{ qty: 99 }] }), "Slipstream (3)");
  assert.equal(helpers.strategyLabel({ product: "Slipstream", configuredContracts: 4,
    configuredMultiplier: 1, positions: [{ qty: 1 }] }), "Slipstream (4)");
  assert.equal(helpers.strategyLabel({ product: "Slipstream", configuredMultiplier: 4,
    positions: [{ qty: 4 }] }), "Slipstream");
});

test("history renders only up to five supplied trading dates and never fabricates weekdays", () => {
  const helpers = productionHelpers();
  assert.equal(helpers.historyColumns([row("A".repeat(22), "···135")]).length, 0);
  const dates = ["2026-09-29", "2026-09-28", "2026-09-25", "2026-09-24", "2026-09-23", "2026-09-22"];
  const days = dates.map((date, index) => ({ date, profit: index + 1 }));
  const columns = helpers.historyColumns([row("A".repeat(22), "···135", { previousTradingDays: days })]);
  assert.equal(columns.map(x => x.label).join(","), dates.slice(0, 5).join(","));
  const cells = helpers.accountCells(row("A".repeat(22), "···135", { previousTradingDays: [
    { date: dates[0], profit: null }
  ] }), columns);
  assert.equal(cells.find(([label]) => label === dates[0])[1], "not yet measured");
});

test("production CSP matches the LF-normalized inline dashboard script", () => {
  const inlineStyle = html.split("<style>")[1].split("</style>")[0];
  const declaredStyle = html.match(/style-src[^;]*'sha256-([^']+)'/);
  assert.ok(declaredStyle, "CSP must pin the inline style hash");
  assert.equal(createHash("sha256").update(inlineStyle.replace(/\r\n/g, "\n")).digest("base64"), declaredStyle[1]);
  const declared = html.match(/script-src 'sha256-([^']+)'/);
  assert.ok(declared, "CSP must pin the inline script hash");
  const actual = createHash("sha256").update(inline.replace(/\r\n/g, "\n")).digest("base64");
  assert.equal(actual, declared[1]);
  assert.match(html, /connect-src 'self' https:\/\/ftb-live\.cmrealestate808\.workers\.dev/);
  assert.doesNotMatch(html, /<th>Multiplier<\/th>/);
  assert.doesNotMatch(html, /configuredMultiplier/);
});
