import socket
from flask import Flask, jsonify, render_template_string

# ── Easy-edit constants for demo pushes ──────────────────────────
SITE_VERSION = "v2"
SITE_COLOR   = "#2563eb"          # page background colour
# ─────────────────────────────────────────────────────────────────

app = Flask(__name__)


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.get("/info")
def info():
    return jsonify({
        "version": SITE_VERSION,
        "pod":     socket.gethostname(),
        "color":   SITE_COLOR,
    })


@app.get("/")
def index():
    return render_template_string(PAGE)


# ── Single self-contained HTML page (inline CSS + JS) ────────────
PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bean &amp; Byte Cafe</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
:root{--bg:''' + SITE_COLOR + r''';--card:rgba(255,255,255,.12);--text:#f0f4ff;--accent:#fbbf24}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;
     min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 20px}

/* ── header ── */
.logo{font-size:3rem;margin-bottom:4px}
h1{font-size:2.6rem;font-weight:800;letter-spacing:-1px}
.tagline{opacity:.75;margin:6px 0 30px;font-size:1.05rem}

/* ── version badge ── */
.version{display:inline-block;background:var(--accent);color:#1e293b;font-weight:800;
         font-size:2.2rem;padding:10px 28px;border-radius:14px;margin-bottom:32px;
         box-shadow:0 4px 20px rgba(0,0,0,.25);letter-spacing:1px}

/* ── menu grid ── */
.menu{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
      gap:20px;width:100%;max-width:820px;margin-bottom:36px}
.item{background:var(--card);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.18);
      border-radius:18px;padding:28px 24px;transition:transform .2s,box-shadow .2s}
.item:hover{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,0,0,.3)}
.item h2{font-size:1.35rem;margin-bottom:6px}
.item .price{font-size:1.5rem;font-weight:800;color:var(--accent)}
.item p{opacity:.72;font-size:.92rem;margin-top:8px;line-height:1.45}

/* ── status bar ── */
.status-bar{background:var(--card);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.18);
            border-radius:14px;padding:18px 28px;display:flex;align-items:center;gap:18px;
            flex-wrap:wrap;font-size:.95rem;margin-bottom:14px;max-width:820px;width:100%}
.dot{width:14px;height:14px;border-radius:50%;background:#4ade80;flex-shrink:0;
     transition:background .3s;box-shadow:0 0 8px #4ade8088}
.dot.red{background:#fb7185;box-shadow:0 0 8px #fb718588}
.counter b{font-variant-numeric:tabular-nums}

/* ── pod label ── */
.pod{opacity:.55;font-size:.82rem;margin-top:6px;word-break:break-all}

@media(max-width:560px){h1{font-size:2rem}.version{font-size:1.6rem;padding:8px 18px}
  .menu{grid-template-columns:1fr}.status-bar{flex-direction:column;align-items:flex-start}}
</style></head><body>

<div class="logo">☕</div>
<h1>Bean &amp; Byte Cafe</h1>
<p class="tagline">Freshly brewed code &amp; coffee</p>

<div class="version" id="ver">''' + SITE_VERSION + r'''</div>

<div class="menu">
  <div class="item">
    <h2>Espresso Classico</h2>
    <span class="price">$3.50</span>
    <p>Rich double-shot pulled from single-origin beans. Bold, smooth, no nonsense.</p>
  </div>
  <div class="item">
    <h2>Matcha Cloudlatte</h2>
    <span class="price">$5.00</span>
    <p>Ceremonial-grade matcha folded into oat milk foam. Vibrant and creamy.</p>
  </div>
  <div class="item">
    <h2>Byte-Size Brownie</h2>
    <span class="price">$4.25</span>
    <p>Fudgy dark-chocolate brownie with a hint of sea salt. Pairs perfectly with espresso.</p>
  </div>
</div>

<div class="status-bar">
  <span class="dot" id="dot"></span>
  <span class="counter">requests OK: <b id="ok">0</b></span>
  <span class="counter">failed: <b id="fail">0</b></span>
</div>

<p class="pod" id="pod">served by pod: …</p>

<script>
let ok=0,fail=0;
const $=id=>document.getElementById(id);
async function poll(){
  try{
    const r=await fetch('/info',{cache:'no-store'});
    if(!r.ok) throw Error(r.status);
    const d=await r.json();
    ok++;$('ok').textContent=ok;
    $('pod').textContent='served by pod: '+d.pod;
    $('dot').classList.remove('red');
  }catch(e){
    fail++;$('fail').textContent=fail;
    $('dot').classList.add('red');
  }
}
poll();setInterval(poll,500);
</script>
</body></html>'''


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
