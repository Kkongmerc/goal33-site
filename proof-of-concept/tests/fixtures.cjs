'use strict';
// SYNTHETIC OFFLINE TEST DATA ONLY. No real account, credential, financial, or trading data.
const NOW = Date.UTC(2026, 9, 1, 12, 0, 0);
const KEYS = ['SYNTHETIC_KEY_A_000000','SYNTHETIC_KEY_B_000000','SYNTHETIC_KEY_C_000000','SYNTHETIC_KEY_D_000000','SYNTHETIC_KEY_P_000000'];
const DATES = ['2026-09-30', '2026-09-29', '2026-09-28', '2026-09-25', '2026-09-24'];
const APPROVED_DISCLAIMER = "Simulated trading environment. The accounts on this page are trading live in a simulated environment. They range from prop-firm simulated evaluation accounts to funded accounts, and they take live market data and the executions of trades produced by TradingView strategy-tester strategies, sent through CrossTrade. Because the environment is simulated, fills may differ in a live trading environment. Results shown are simulated, are not a guarantee or projection of future results, and are not investment advice.Risk disclosure. Futures and derivatives trading involves substantial risk of loss and is not suitable for every investor. You may lose more than your initial investment. Only risk capital should be used for trading, and only those with sufficient risk capital should consider trading.Hypothetical performance disclaimer. Performance figures displayed on this site are hypothetical or simulated. Hypothetical performance results have many inherent limitations. No representation is being made that any account will or is likely to achieve profits or losses similar to those shown.";
const MALICIOUS = '<img src=x onerror="window.__SYNTHETIC_XSS__=true">';
const history = values => DATES.map((date, i) => ({date, profit: values[i]}));
function fixture() {
  return {
    _fixture: 'SYNTHETIC OFFLINE REGRESSION ONLY — no real accounts or results',
    asOf: NOW, ts: NOW,
    uptime: {state:'live', h24:99.5, d7:98.2, d30:null, lastUpdateAgeS:5, dataAgeS:5},
    accounts: [
      {accountKey:KEYS[0], id:'···101', product:'Midas', firm:'SYNTHETIC Alpha', nominalSize:50000, startingBalance:50000, currentBalance:50125, currentEquity:50130, totalNetProfit:125, todayProfit:25, netToday:25, openTrades:2, balanceAsOfTs:NOW, previousTradingDays:history([10,20,null,-5,0])},
      {accountKey:KEYS[1], id:'···101', product:'Midas', firm:'SYNTHETIC Beta', nominalSize:100000, startingBalance:100000, currentBalance:99950, currentEquity:99970, totalNetProfit:-50, todayProfit:-10, netToday:-10, openTrades:0, balanceAsOfTs:NOW, previousTradingDays:history([-10,0,5,0,0])},
      {accountKey:KEYS[2], id:'···303', product:'Continuum', firm:'SYNTHETIC Gamma', nominalSize:null, startingBalance:null, currentBalance:null, currentEquity:25333, totalNetProfit:null, todayProfit:null, netToday:null, openTrades:null, balanceAsOfTs:NOW, previousTradingDays:history([null,null,null,null,null])},
      {accountKey:KEYS[3], id:'···404', product:'Slipstream', configuredContracts:3, firm:'SYNTHETIC Delta', nominalSize:75000, startingBalance:75000, currentBalance:75300, currentEquity:null, totalNetProfit:300, todayProfit:15, netToday:15, openTrades:1, balanceAsOfTs:NOW, previousTradingDays:history([1,2,3,4,5])},
      {accountKey:KEYS[4], id:'···999', product:'Midas', visibility:'private', firm:'SYNTHETIC PRIVATE MUST NOT APPEAR', nominalSize:123456, currentBalance:765432, todayProfit:111, openTrades:7},
      {accountKey:'invalid-key', id:'···777', product:'Midas', firm:'SYNTHETIC INVALID KEY MUST NOT APPEAR'},
      {accountKey:'SYNTHETIC_KEY_X_000000', id:'RAW-ACCOUNT-SYNTHETIC', product:'Midas', firm:'SYNTHETIC INVALID ALIAS MUST NOT APPEAR'}
    ],
    daily: {date:'2026-10-01', trades:4, wins:3, losses:1, net:30, byProduct:[{product:'Midas', trades:2, net:15},{product:'Continuum', trades:null, net:null},{product:'Slipstream', trades:2, net:15}]},
    health: {watcherUp:true, identities:KEYS.map((accountKey,i) => ({accountKey,id:i<2?'···101':i===2?'···303':i===3?'···404':'···999',ok:i!==2}))},
    calendar: {
      '2026-10-01': {total:30,byAccount:{[KEYS[0]]:25,[KEYS[1]]:-10,[KEYS[2]]:null,[KEYS[3]]:15},byStrategy:{Midas:{total:15,byAccount:{[KEYS[0]]:25,[KEYS[1]]:-10}},Continuum:{total:null,byAccount:{[KEYS[2]]:null}},Slipstream:{total:15,byAccount:{[KEYS[3]]:15}}}},
      '2026-09-30': {total:1,byAccount:{[KEYS[0]]:10,[KEYS[1]]:-10,[KEYS[3]]:1},byStrategy:{Midas:{total:0,byAccount:{[KEYS[0]]:10,[KEYS[1]]:-10}},Slipstream:{total:1,byAccount:{[KEYS[3]]:1}}}}
    },
    automation: {
      asOf:NOW,
      components:[{name:'SYNTHETIC Summary feed',state:'up',since:NOW-60000},{name:'SYNTHETIC Monitor',state:'degraded',since:null}],
      incidents:[{approved:true,title:'SYNTHETIC approved incident'},{approved:false,title:'SYNTHETIC UNAPPROVED INCIDENT MUST NOT APPEAR'}],
      accuracy:{leads:[{product:'Midas',testerTrades:12,accountTrades:12,fillsCompared:12,withinTolerancePct:100,medianTicks:0,worstTicks:1,worseThanTester:0,missedEntries:null,stopsPresentPct:null,orderedCloses:null}]},
      implemented:[{approved:true,title:'SYNTHETIC approved protection',status:'live',date:'2026-10-01',text:'SYNTHETIC verified fixture text'},{approved:false,title:'SYNTHETIC UNAPPROVED IMPLEMENTATION MUST NOT APPEAR'}],
      testing:{strategiesTested:3,strategiesAtTarget:null,openItems:0,byStrategy:[{name:'Midas',trades:12,state:'sim-tested'}]},
      risks:[{approved:true,title:'SYNTHETIC approved risk',status:'monitored',text:'SYNTHETIC review pending'},{approved:false,title:'SYNTHETIC UNAPPROVED RISK MUST NOT APPEAR'}]
    }
  };
}
function privateFixture() {
  const d = fixture(); d.accounts = d.accounts.slice(0,5);
  d.accounts[0].positions=[{instrument:'SYNTHETIC_PRIVATE_POSITION',side:'buy',qty:2,avg:12345.67,last:12346.78,unrealized:2.22}];
  d.accounts[0].private={balance:50125,marginUsed:123,workingOrders:[{instrument:'SYNTHETIC_PRIVATE_ORDER',side:'sell',qty:2,type:'limit',price:12400}]};
  d.fillsToday=[{ts:NOW,account:'···101',instrument:'SYNTHETIC_PRIVATE_FILL',side:'buy',qty:2,price:12345.67}];
  return d;
}
module.exports={NOW,KEYS,DATES,MALICIOUS,APPROVED_DISCLAIMER,fixture,privateFixture};
