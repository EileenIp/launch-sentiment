"""Phase 5: build the self-contained HTML dashboard.

One file, no dependencies, no network — it has to work opened from disk and served
from GitHub Pages alike, and still work in five years when a CDN has moved on.

The data is numbers and dates only, so it inlines as plain JSON.

Run: python -m src.dashboard
"""
from __future__ import annotations

import json

from src import config, patches, taxonomy, timeseries

OUT = config.PROJECT_ROOT / "dashboard" / "index.html"

# Volume spans 117 reviews on a quiet day to 78,185 on 6 May. Linear bars would
# render every ordinary day as a flat line, so volume is drawn on a log scale and
# the axis says so.
ANNOTATIONS = [
    {"date": "2024-02-08", "label": "Launch"},
    {"date": "2024-05-03", "label": "Sony announces PSN account linking"},
    {"date": "2024-05-06", "label": "Sony reverses"},
    {"date": "2024-08-06", "label": "Patch 1.001.002 'Escalation of Freedom'"},
    {"date": "2024-09-17", "label": "Patch 1.001.100 rebalance"},
]

THEME_COLOURS = {
    "psn_access": "#e0645a",
    "balance": "#e0a23c",
    "bugs_stability": "#5aa9e0",
    "dev_conduct": "#b07ae0",
    "content_design": "#4fbf8b",
    "monetisation": "#e08cc0",
    "price_value": "#8a93a8",
    "performance": "#6fd0c4",
}


def payload(appid: int | None = None) -> dict:
    appid = appid or config.TARGET_APPID
    days = timeseries.load(appid)["days"]
    patch_rows = [p for p in patches.patches_in_window(appid) if p["official"]]

    slim = []
    for row in days:
        entry = {
            "d": row["date"],
            "n": row["reviews"],
            "p": round(row["positive_share"], 4) if row["positive_share"] is not None else None,
            "neg": row["negatives"],
        }
        for theme in taxonomy.THEMES:
            share = row.get(f"share_{theme}")
            entry[theme] = round(share, 4) if share is not None else None
        slim.append(entry)

    return {
        "days": slim,
        "patches": [{"d": p["date"], "t": p["title"]} for p in patch_rows],
        # Same key shape as patches — the drawing code reads `.d` for every date, and
        # passing these through with a "date" key made findIndex return -1 and draw
        # nothing at all, silently.
        "annotations": [{"d": a["date"], "label": a["label"]} for a in ANNOTATIONS],
        "themes": list(taxonomy.THEMES),
        "colours": THEME_COLOURS,
    }


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Helldivers 2 &mdash; Launch Sentiment</title>
<style>
:root{--bg:#0f1117;--panel:#171a23;--line:#262b38;--ink:#e9ecf3;--soft:#98a0b3;--accent:#7c8cf0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:17px;margin:34px 0 10px;font-weight:600}
.sub{color:var(--soft);margin:0 0 26px}
.verdict{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
 border-radius:8px;padding:16px 18px;margin:0 0 26px}
.verdict b{color:#fff}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:0 0 26px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px}
.card .v{font-size:22px;font-weight:650}
.card .k{color:var(--soft);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.card .n{color:var(--soft);font-size:12px;margin-top:4px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:16px;overflow-x:auto}
svg{display:block;min-width:640px;width:100%;height:auto}
.ctl{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:0 0 12px;color:var(--soft);font-size:13px}
input[type=range]{width:260px;accent-color:var(--accent)}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--soft);margin-top:10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.note{color:var(--soft);font-size:13px;margin-top:10px}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}
th{color:var(--soft);font-weight:600}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{font-size:11px;padding:1px 6px;border-radius:9px;background:#232838;color:var(--soft)}
</style></head><body><div class="wrap">

<h1>When a launch goes sideways, what turned sentiment &mdash; and how early was it visible?</h1>
<p class="sub">HELLDIVERS&trade; 2 &middot; 886,850 Steam reviews &middot; 8 Feb to 5 Nov 2024</p>

<div class="verdict">
<b>The answer is no &mdash; nothing led.</b> Both sentiment collapses were triggered by dated
developer actions, so complaint themes and the review score moved on the same day. You cannot
get early warning of an announcement from reactions to it. What the data does support is
same-day <i>diagnosis</i>: within hours the theme mix names the cause.
</div>

<div class="cards" id="cards"></div>

<h2>Daily review score and volume</h2>
<div class="panel">
 <div class="ctl">
   <label>Window <input type="range" id="from" min="0" value="0"></label>
   <label>to <input type="range" id="to" min="0"></label>
   <span id="range"></span>
 </div>
 <svg id="main" viewBox="0 0 1000 340"></svg>
 <div class="legend">
   <span><i style="background:#7c8cf0"></i>7-day positive share</span>
   <span><i style="background:#2f3648"></i>daily reviews (log scale)</span>
   <span><i style="background:#4a5268"></i>official patch</span>
 </div>
 <p class="note">Volume is drawn on a log scale: quiet days carry ~120 reviews, 6 May carried 78,185.</p>
</div>

<h2>What people complained about, as a share of each day's negative reviews</h2>
<div class="panel">
 <svg id="themes" viewBox="0 0 1000 300"></svg>
 <div class="legend" id="tlegend"></div>
 <p class="note">Composition, not volume &mdash; this asks what the complaints were <i>about</i>,
 independent of how many there were. Smoothed over 7 days.</p>
</div>

<h2>The two events, day by day</h2>
<div class="panel"><table id="events"></table></div>

</div>
<script>
const DATA = __DATA__;
const D = DATA.days, TH = DATA.themes, C = DATA.colours;
const patchDates = new Set(DATA.patches.map(p => p.d));
const svgns = "http://www.w3.org/2000/svg";

function el(tag, attrs, parent){
  const n = document.createElementNS(svgns, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function roll(vals, w){
  const out = [];
  for (let i = 0; i < vals.length; i++){
    let s = 0, c = 0;
    for (let j = Math.max(0, i-w+1); j <= i; j++){ if (vals[j] != null){ s += vals[j]; c++ } }
    out.push(c ? s/c : null);
  }
  return out;
}
function fmt(n){ return n.toLocaleString() }

function cards(){
  const tot = D.reduce((a,r)=>a+r.n,0);
  const worst = D.filter(r=>r.n>=500).sort((a,b)=>a.p-b.p)[0];
  const peak = D.slice().sort((a,b)=>b.n-a.n)[0];
  const rows = [
    ["Reviews analysed", fmt(886850), "100% of the window"],
    ["Deepest day", (worst.p*100).toFixed(1)+"%", worst.d + " \\u2014 the nerf patch"],
    ["Busiest day", fmt(peak.n), peak.d + " \\u2014 PSN reversal"],
    ["Best lead found", "0 days", "same-day, no early warning"]
  ];
  document.getElementById("cards").innerHTML = rows.map(r =>
    `<div class="card"><div class="k">${r[0]}</div><div class="v">${r[1]}</div><div class="n">${r[2]}</div></div>`
  ).join("");
}

function drawMain(a, b){
  const svg = document.getElementById("main");
  svg.innerHTML = "";
  const rows = D.slice(a, b+1);
  const L=52, R=14, T=14, B=30, W=1000, H=340;
  const iw = W-L-R, ih = H-T-B;
  const x = i => L + (rows.length<2 ? iw/2 : iw*i/(rows.length-1));
  const maxN = Math.max(...rows.map(r=>r.n), 10);
  const ly = n => { const v = Math.log10(Math.max(n,1)), m = Math.log10(maxN); return T+ih-(ih*0.55)*(v/m) };

  for (let g=0; g<=4; g++){
    const yy = T + ih*g/4;
    el("line",{x1:L,x2:W-R,y1:yy,y2:yy,stroke:"#262b38"},svg);
    el("text",{x:8,y:yy+4,fill:"#98a0b3","font-size":11},svg).textContent = (100-g*25)+"%";
  }
  // Routine patches are context, not content — kept faint so they cannot be mistaken
  // for the annotated events that actually moved sentiment.
  rows.forEach((r,i)=>{
    if (patchDates.has(r.d))
      el("line",{x1:x(i),x2:x(i),y1:T+ih-14,y2:T+ih,stroke:"#4a5268","stroke-width":1,opacity:.55},svg);
  });
  const bw = Math.max(1, iw/rows.length*0.8);
  rows.forEach((r,i)=>{
    const yy = ly(r.n);
    el("rect",{x:x(i)-bw/2,y:yy,width:bw,height:T+ih-yy,fill:"#2f3648"},svg);
  });
  const sm = roll(rows.map(r=>r.p), 7);
  let d = "";
  sm.forEach((v,i)=>{ if(v==null) return; d += (d?"L":"M") + x(i) + " " + (T+ih-ih*v) });
  el("path",{d,fill:"none",stroke:"#7c8cf0","stroke-width":2.2},svg);

  // Stagger the labels so they never sit on top of each other, and flip to the left
  // of the line when a label would run off the right edge.
  DATA.annotations.forEach((an, k)=>{
    const i = rows.findIndex(r=>r.d===an.d);
    if (i<0) return;
    el("line",{x1:x(i),x2:x(i),y1:T,y2:T+ih,stroke:"#e0645a","stroke-dasharray":"3 3",opacity:.8},svg);
    el("circle",{cx:x(i),cy:T+4,r:3,fill:"#e0645a"},svg);
    const flip = x(i) > W - 260;
    const t = el("text",{x:x(i)+(flip?-6:6), y:T+16+(k%3)*13, fill:"#e0645a",
                         "font-size":10, "text-anchor":flip?"end":"start"},svg);
    t.textContent = an.label;
  });
  [0, Math.floor(rows.length/2), rows.length-1].forEach(i=>{
    if (rows[i]) el("text",{x:x(i),y:H-10,fill:"#98a0b3","font-size":11,"text-anchor":"middle"},svg)
      .textContent = rows[i].d;
  });
}

function drawThemes(a, b){
  const svg = document.getElementById("themes");
  svg.innerHTML = "";
  const rows = D.slice(a, b+1);
  const L=52,R=14,T=14,B=30,W=1000,H=300, iw=W-L-R, ih=H-T-B;
  const x = i => L + (rows.length<2 ? iw/2 : iw*i/(rows.length-1));
  for (let g=0; g<=4; g++){
    const yy = T+ih*g/4;
    el("line",{x1:L,x2:W-R,y1:yy,y2:yy,stroke:"#262b38"},svg);
    el("text",{x:8,y:yy+4,fill:"#98a0b3","font-size":11},svg).textContent = (100-g*25)+"%";
  }
  TH.forEach(th=>{
    const sm = roll(rows.map(r=>r[th]), 7);
    let d="";
    sm.forEach((v,i)=>{ if(v==null) return; d += (d?"L":"M") + x(i) + " " + (T+ih-ih*Math.min(v,1)) });
    el("path",{d,fill:"none",stroke:C[th],"stroke-width":1.8,opacity:.95},svg);
  });
  [0, Math.floor(rows.length/2), rows.length-1].forEach(i=>{
    if (rows[i]) el("text",{x:x(i),y:H-10,fill:"#98a0b3","font-size":11,"text-anchor":"middle"},svg)
      .textContent = rows[i].d;
  });
  document.getElementById("tlegend").innerHTML = TH.map(t=>
    `<span><i style="background:${C[t]}"></i>${t.replace(/_/g," ")}</span>`).join("");
}

function events(){
  const pick = ["2024-05-02","2024-05-03","2024-05-04","2024-05-05","2024-05-06",
                "2024-08-05","2024-08-06","2024-08-07","2024-08-08"];
  const notes = {"2024-05-03":"Sony announces PSN linking","2024-05-06":"Sony reverses",
                 "2024-08-06":"Patch 1.001.002"};
  let h = "<tr><th>Date</th><th class='num'>Reviews</th><th class='num'>Positive</th>"
        + "<th class='num'>PSN</th><th class='num'>Balance</th><th></th></tr>";
  pick.forEach(dt=>{
    const r = D.find(z=>z.d===dt); if(!r) return;
    h += `<tr><td>${dt}</td><td class="num">${fmt(r.n)}</td>`
      +  `<td class="num">${(r.p*100).toFixed(1)}%</td>`
      +  `<td class="num">${((r.psn_access||0)*100).toFixed(1)}%</td>`
      +  `<td class="num">${((r.balance||0)*100).toFixed(1)}%</td>`
      +  `<td>${notes[dt] ? '<span class="tag">'+notes[dt]+'</span>' : ''}</td></tr>`;
  });
  document.getElementById("events").innerHTML = h;
}

const f = document.getElementById("from"), t = document.getElementById("to");
f.max = D.length-1; t.max = D.length-1; t.value = D.length-1;
function redraw(){
  let a = +f.value, b = +t.value;
  if (a > b-10) a = Math.max(0, b-10);
  document.getElementById("range").textContent = D[a].d + "  \\u2192  " + D[b].d + "   (" + (b-a+1) + " days)";
  drawMain(a,b); drawThemes(a,b);
}
f.addEventListener("input", redraw); t.addEventListener("input", redraw);
cards(); events(); redraw();
</script></body></html>
"""


def build(appid: int | None = None) -> str:
    html = TEMPLATE.replace("__DATA__", json.dumps(payload(appid), separators=(",", ":")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return str(OUT)


if __name__ == "__main__":
    path = build()
    size = OUT.stat().st_size
    print(f"wrote {path} ({size/1024:.0f} KB)")
