// Synthetic public contract only; never real accounts, balances, exports or credentials.
const START=Date.parse('2026-09-30T22:00:00Z'),END=Date.parse('2026-10-01T21:00:00Z');
function projection(now){
  const cash=(date,startTs,endTs,asOfTs,profit)=>({date,startTs,endTs,state:'verified',reason:null,asOfTs,profit});
  return {version:'ny-18-17-v1',timezone:'America/New_York',active:now<END,
    today:cash('2026-10-01',START,END,Math.min(now,END),40),
    yesterday:cash('2026-09-30',START-86400000,END-86400000,END-86400000,90),
    comparison:{date:'2026-10-01',startTs:START,endTs:END,state:'verified',reason:null,asOfTs:Math.min(now,END),pnlDivergence:-10,missedTesterTrades:1}};
}
function unavailable(block,comparison=false,reason='incomplete_coverage'){return {...block,state:'unavailable',reason,asOfTs:null,...(comparison?{pnlDivergence:null,missedTesterTrades:null}:{profit:null})};}
module.exports={START,END,projection,unavailable};
