#!/usr/bin/env python3
"""Render the AFA WorldCard v2 live dashboard from data.json, gate with `wf`, write index.html.
Run: python3 build.py   (reads ./data.json, writes ./index.html)."""
import os, json, base64, pathlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

HERE = pathlib.Path(__file__).parent
D = json.load(open(HERE / "data.json"))
PASSWORD, ITER = "wf", 100_000

def usd(n): return "US$" + f"{n:,.0f}" if n >= 100 else "US$" + f"{n:,.2f}"
def num(n): return f"{n:,.0f}"

def bar(pct, color):
    pct = max(1, min(100, pct))
    return f'<div class="bar"><div class="fill" style="width:{pct:.0f}%;background:{color}"></div></div>'

def region_block(r):
    spent_pct = r["spend"] / r["budget"] * 100 if r["budget"] else 0
    cells = "".join(
        f'<tr><td class="l">{c["c"]}</td><td>{usd(c["spend"])}</td><td>{num(c["impr"])}</td>'
        f'<td>{c["ctr"]:.2f}%</td><td>{num(c["clicks"])}</td><td>US${c["cpc"]:.2f}</td>'
        f'<td>US${c["cpm"]:.2f}</td><td><span class="pill {"warn" if "review" in c["st"] else "ok"}">{c["st"]}</span></td></tr>'
        for c in r["cells"])
    return f"""
    <section class="region">
      <div class="rhead"><h2>{r['name']} <span class="code">{r['code']}</span></h2>
        <div class="rspend">{usd(r['spend'])} <small>/ {usd(r['budget'])} day</small></div></div>
      {bar(spent_pct, '#4f8cff')}
      <div class="rkpi">
        <div><b>{num(r['impr'])}</b><span>impressions</span></div>
        <div><b>{r['ctr']:.2f}%</b><span>CTR</span></div>
        <div><b>{num(r['clicks'])}</b><span>link clicks</span></div>
        <div><b>{num(r['reach'])}</b><span>reach</span></div>
        <div><b>{r['freq']:.2f}</b><span>frequency</span></div>
        <div><b class="{'g' if r['reg'] else 'mut'}">{r['reg']}</b><span>reg completed</span></div>
      </div>
      <table><thead><tr><th class="l">Message cell</th><th>Spend</th><th>Impr</th><th>CTR</th><th>Clicks</th><th>CPC</th><th>CPM</th><th>Delivery</th></tr></thead>
      <tbody>{cells}</tbody></table>
    </section>"""

regions = [r for r in D["regions"] if not r.get("skip")]
t = D["totals"]
avg_cpc = t["spend"] / t["clicks"] if t["clicks"] else 0
px = D["pixel"]
fmax = max(px["start"], px["submit"], px["complete"], px["l3"], 1)
funnel = "".join(
    f'<div class="fl">{lab}</div><div class="fbar"><div class="ff" style="width:{v/fmax*100:.0f}%">{num(v)}</div></div>'
    for lab, v in [("Registration start", px["start"]), ("Registration submit", px["submit"]),
                   ("Registration complete", px["complete"]), ("L3 submitted", px["l3"])])

CONTENT = f"""<style>
  :root{{--bg:#0f1115;--panel:#171a21;--line:#262b36;--ink:#e8eaed;--mut:#9aa3b2;--blue:#4f8cff;--good:#34d399;--warn:#fbbf24;--pink:#f5256e}}
  *{{box-sizing:border-box}} body{{margin:0}}
  .wrap{{max-width:1080px;margin:0 auto;padding:26px 22px 70px;color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg)}}
  h1{{font-size:21px;margin:0 0 3px;letter-spacing:-.2px}} .stamp{{color:var(--mut);font-size:12.5px;margin:0 0 20px}}
  .stamp b{{color:var(--good)}}
  .kpis{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:8px}}
  .k{{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px}}
  .k h3{{margin:0 0 4px;font-size:10.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px;font-weight:600}}
  .k .big{{font-size:22px;font-weight:680;letter-spacing:-.4px}} .k .big small{{font-size:11px;color:var(--mut);font-weight:500}}
  .note{{background:#15171d;border:1px solid var(--line);border-radius:10px;padding:12px 14px;color:var(--mut);font-size:12px;margin:16px 0}}
  b.g{{color:var(--good)}} b.mut{{color:var(--mut)}} .ink{{color:var(--ink)}}
  h4{{font-size:13px;margin:26px 0 10px;border-left:3px solid var(--blue);padding-left:9px}}
  .funnel{{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px}}
  .fl{{color:var(--mut);font-size:12px;text-align:right}} .fbar{{background:#1c2129;border-radius:6px;height:26px;overflow:hidden}}
  .ff{{background:#2f6fd6;height:100%;border-radius:6px;display:flex;align-items:center;padding:0 9px;font-size:12px;font-weight:650;color:#eaf1ff;min-width:44px}}
  .region{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-top:14px}}
  .rhead{{display:flex;justify-content:space-between;align-items:baseline}} .rhead h2{{font-size:17px;margin:0}} .code{{color:var(--mut);font-size:12px;font-weight:500}}
  .rspend{{font-size:18px;font-weight:680}} .rspend small{{font-size:12px;color:var(--mut);font-weight:500}}
  .bar{{height:7px;background:#1c2129;border-radius:5px;overflow:hidden;margin:9px 0 14px}} .fill{{height:100%;border-radius:5px}}
  .rkpi{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:14px}}
  .rkpi div{{text-align:center}} .rkpi b{{display:block;font-size:17px;font-weight:680}} .rkpi span{{font-size:10.5px;color:var(--mut)}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px}}
  th,td{{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:var(--mut);font-weight:600;font-size:10.5px;text-transform:uppercase;letter-spacing:.3px}}
  .l{{text-align:left}} .pill{{font-size:10.5px;padding:1px 7px;border-radius:20px}} .pill.ok{{background:rgba(52,211,153,.14);color:var(--good)}} .pill.warn{{background:rgba(251,191,36,.14);color:var(--warn)}}
  @media(max-width:760px){{.kpis,.rkpi{{grid-template-columns:repeat(3,1fr)}} .funnel{{grid-template-columns:110px 1fr}} table{{display:block;overflow-x:auto}}}}
</style>
<div class="wrap">
  <h1>AFA WorldCard v2 &mdash; Live</h1>
  <p class="stamp">Updated <b>{D['updated_sgt']}</b> &middot; flight since {D['flight_start']} &middot; page auto-refreshes every 15 min, data refreshed hourly</p>
  <div class="kpis">
    <div class="k"><h3>Spend</h3><div class="big">{usd(t['spend'])} <small>/ {usd(D['budget_daily'])} day</small></div></div>
    <div class="k"><h3>Impressions</h3><div class="big">{num(t['impr'])}</div></div>
    <div class="k"><h3>Link clicks</h3><div class="big">{num(t['clicks'])}</div></div>
    <div class="k"><h3>Avg cost / click</h3><div class="big">US${avg_cpc:.2f}</div></div>
    <div class="k"><h3>Reg completed</h3><div class="big mut">{t['reg']} <small>lagged</small></div></div>
    <div class="k"><h3>Cells live</h3><div class="big">6<small>/6</small></div></div>
  </div>
  <div class="note"><b class="ink">How to read this:</b> completions fire only after internal approval (days later), so <b class="ink">0 completed is expected this early</b>, not a failure. Judge daily on <b class="ink">Registration-submit</b> (in Ads Manager custom columns), quality on L3. CTR near 1% and CPC of US$0.30&ndash;2.30 are by design (optimizing to registrations, not cheap clicks) &mdash; v1 bought clicks at US$0.05 and converted almost nobody.</div>

  <h4>Registration funnel &mdash; pixel pulse</h4>
  <div class="funnel">{funnel}</div>
  <div class="note" style="margin-top:8px">{px['note']}</div>

  <h4>By region</h4>
  {''.join(region_block(r) for r in regions)}

  <div class="note">{D['kill_note']} &middot; SG runs the 5.2% new-customer offer copy; MY/ID run 1%. Attributed conversions and per-cell Registration-submit are read in Ads Manager (Meta API does not expose custom pixel events per cell).</div>
</div>"""

# ---- gate with wf ----
salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(PASSWORD.encode())
ct = AESGCM(key).encrypt(iv, CONTENT.encode(), None)
blob = json.dumps({"salt": base64.b64encode(salt).decode(), "iv": base64.b64encode(iv).decode(),
                   "iterations": ITER, "ciphertext": base64.b64encode(ct).decode()})

SHELL = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="900"><meta name="robots" content="noindex"><title>AFA v2 Live</title>
<style>body{margin:0;background:#0f1115;color:#e8eaed;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
#gate{max-width:340px;margin:22vh auto;text-align:center;padding:0 20px}#gate input{width:100%;padding:12px 14px;border-radius:9px;border:1px solid #262b36;background:#171a21;color:#e8eaed;font-size:15px;margin:12px 0}
#gate button{width:100%;padding:12px;border:none;border-radius:9px;background:#4f8cff;color:#fff;font-weight:650;font-size:15px;cursor:pointer}#gate .e{color:#f5256e;font-size:12.5px;min-height:16px;margin-top:8px}
.lockbar{position:fixed;top:8px;right:12px;font-size:11px}.lockbar a{color:#9aa3b2}</style></head>
<body><div id="gate"><div style="font-size:26px">&#128274;</div><p style="color:#9aa3b2;font-size:13px">AFA WorldCard v2 &mdash; live campaign</p>
<input id="pw" type="password" placeholder="Password" autofocus><button onclick="go()">View</button><div class="e" id="e"></div></div>
<div id="app"></div>
<script>
const B=__BLOB__;
function b64(s){const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;}
async function dk(pw,salt,it){const bk=await crypto.subtle.importKey("raw",new TextEncoder().encode(pw),"PBKDF2",false,["deriveKey"]);
return crypto.subtle.deriveKey({name:"PBKDF2",salt,iterations:it,hash:"SHA-256"},bk,{name:"AES-GCM",length:256},false,["decrypt"]);}
async function dec(pw){const k=await dk(pw,b64(B.salt),B.iterations);const p=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64(B.iv)},k,b64(B.ciphertext));return new TextDecoder().decode(p);}
function reveal(h){document.getElementById('gate').style.display='none';const a=document.getElementById('app');a.innerHTML=h+'<div class="lockbar"><a href="#" onclick="localStorage.removeItem(\\'afa_pw\\');location.reload();return false">lock device</a></div>';}
async function go(){const pw=document.getElementById('pw').value;try{const h=await dec(pw);reveal(h);try{localStorage.setItem('afa_pw',pw)}catch(_){}}catch(_){document.getElementById('e').textContent='Wrong password'}}
document.getElementById('pw').addEventListener('keydown',e=>{if(e.key==='Enter')go()});
(async()=>{try{const c=localStorage.getItem('afa_pw');if(c)reveal(await dec(c))}catch(_){try{localStorage.removeItem('afa_pw')}catch(_){}}})();
</script></body></html>"""

(HERE / "index.html").write_text(SHELL.replace("__BLOB__", blob))
print("built index.html  spend=US$%.0f  regions=%d" % (t["spend"], len(regions)))
