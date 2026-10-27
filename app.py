import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()
app = Flask(__name__)
@app.get("/health")
def health():
    return {"status": "ok"}, 200
QUERIES = {
    'runs': 'SELECT run_id, commit_sha, commit_msg, actor, status, started_at, finished_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 100',
    'stages': 'SELECT id, run_id, stage, status, details, created_at FROM stage_events ORDER BY created_at DESC LIMIT 500',
    'scans': 'SELECT id, run_id, image, critical, high, medium, low, gate_passed, created_at FROM scan_results ORDER BY created_at DESC LIMIT 100',
    'deployments': 'SELECT id, run_id, image_tag, status, details, created_at FROM deployments ORDER BY created_at DESC LIMIT 100',
}

def json_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value

@app.get('/api/data')
def data():
    try:
        output = {}
        with psycopg.connect(os.environ['NEON_URL'], row_factory=dict_row, connect_timeout=8) as conn:
            with conn.cursor() as cursor:
                for key, statement in QUERIES.items():
                    cursor.execute(statement)
                    output[key] = [{k: json_value(v) for k, v in row.items()} for row in cursor.fetchall()]
        return jsonify(output)
    except Exception:
        app.logger.exception('Failed to load SecureFlow dashboard data')
        return jsonify({'error': 'Could not retrieve data from Neon. Check the Flask terminal.'}), 500

@app.get('/')
def index():
    return render_template_string(PAGE)

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SecureFlow | Security Operations</title>
<style>
:root{color-scheme:dark;--bg:#090f1e;--panel:#142038;--line:#2c3b55;--muted:#a3b4ce;--text:#f0f6ff;--blue:#38bdf8;--green:#4ade80;--red:#fb7185;--yellow:#fbbf24}
*{box-sizing:border-box}body{background:var(--bg);color:var(--text);font:15px system-ui,-apple-system,Segoe UI,sans-serif;margin:0}main{max-width:1350px;margin:auto;padding:28px}h1{margin:0;color:var(--blue);font-size:30px}h2{font-size:19px;margin:0 0 15px}.sub,.muted{color:var(--muted)}.top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center}.top p{margin:5px 0}.status{display:flex;gap:10px;align-items:center;flex-wrap:wrap}button,select{background:#223655;color:var(--text);border:1px solid #496080;border-radius:9px;padding:10px 12px;font:inherit}button{cursor:pointer}button:hover{border-color:var(--blue)}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:24px 0}.card,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px}.card small{color:var(--muted)}.metric{font-size:34px;font-weight:750;margin-top:9px}.cols{display:grid;grid-template-columns:1.05fr .95fr;gap:16px}.panel{margin-bottom:16px;min-width:0}.tablewrap{overflow:auto;max-height:360px}table{width:100%;border-collapse:collapse;text-align:left;font-size:13px}th,td{padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);position:sticky;top:0;background:var(--panel)}tr.pick{cursor:pointer}tr.pick:hover,tr.selected{background:#223653}.pill{display:inline-block;border-radius:99px;padding:4px 9px;background:#334155;color:#dbeafe;font-size:12px;font-weight:650}.pill.success,.pill.passed,.pill.healthy,.pill.synced{background:#164a37;color:#86efac}.pill.failure,.pill.failed,.pill.blocked{background:#562435;color:#fda4af}.pill.running,.pill.pending{background:#51401d;color:#fde68a}.bars{display:grid;gap:12px}.barrow{display:grid;grid-template-columns:78px 1fr 52px;gap:12px;align-items:center}.track{background:#293850;border-radius:9px;height:15px;overflow:hidden}.fill{height:100%;border-radius:9px}.critical{background:#ef4444}.high{background:#fb923c}.medium{background:#facc15}.low{background:#38bdf8}.stages{display:flex;flex-wrap:wrap;gap:9px}.stage{padding:11px;border-radius:10px;background:#23334d;border:1px solid #394d6a;min-width:112px}.stage strong{display:block;margin-bottom:7px}.empty{color:var(--muted);padding:18px 0}.error{color:var(--red);margin:14px 0}.footer{margin:20px 0;color:var(--muted);font-size:12px}a{color:#7dd3fc}#details{min-height:50px}code{overflow-wrap:anywhere}@media(max-width:900px){.cols{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:500px){main{padding:15px}.cards{gap:9px}.card,.panel{padding:14px}.metric{font-size:27px}}
</style></head><body><main>
<header class="top"><div><h1>⬡ SecureFlow</h1><p class="sub">DevSecOps Mission Control · Live Neon PostgreSQL data</p></div><div class="status"><span id="connection" class="pill pending">Connecting</span><span class="muted" id="updated">—</span><button id="refresh">↻ Refresh</button></div></header>
<p id="error" class="error" role="alert"></p>
<div class="cards"><div class="card"><small>Recent pipeline runs</small><div class="metric" id="total">—</div></div><div class="card"><small>Successful</small><div class="metric" id="success">—</div></div><div class="card"><small>Failed</small><div class="metric" id="failed">—</div></div><div class="card"><small>Blocked scans</small><div class="metric" id="blocked">—</div></div></div>
<div class="cols"><section class="panel"><h2>Pipeline runs <span class="muted" style="font-size:13px">· click a row</span></h2><div class="tablewrap"><table><thead><tr><th>Run</th><th>Commit</th><th>Status</th><th>Started</th></tr></thead><tbody id="runs"></tbody></table></div></section><section class="panel"><h2>Selected run</h2><label for="runselect" class="muted">Choose a pipeline run</label> <select id="runselect"></select><div id="details" style="margin-top:15px"></div><h2>Stage timeline</h2><div class="stages" id="stages"></div></section></div>
<div class="cols"><section class="panel"><h2>Trivy vulnerability findings</h2><p class="muted" id="scaninfo">Choose a run to inspect its latest scan.</p><div class="bars" id="chart"></div></section><section class="panel"><h2>Deployment history</h2><div class="tablewrap"><table><thead><tr><th>Run</th><th>Image tag</th><th>Status</th><th>Details</th></tr></thead><tbody id="deployments"></tbody></table></div><p class="muted" style="font-size:12px">Deployment records reflect database events, not a live Kubernetes health check.</p></section></div>
<section class="panel"><h2>Recent stage events</h2><div class="tablewrap"><table><thead><tr><th>Time</th><th>Run</th><th>Stage</th><th>Status</th><th>Details</th></tr></thead><tbody id="events"></tbody></table></div></section>
<p class="footer">Auto-refresh every 5 seconds · Read-only dashboard · Recent records only · Security gate: blocks Critical or High vulnerabilities</p>
</main><script>
const $=id=>document.getElementById(id);let store=null;let selected=null;
function safe(v){return String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function pill(v){const t=String(v??'unknown').toLowerCase();return '<span class="pill '+( /^[a-z-]+$/.test(t)?t:'')+'">'+safe(v)+'</span>';}
function date(v){if(!v)return '—';const d=new Date(v);return Number.isNaN(d.getTime())?safe(v):safe(d.toLocaleString());}
function cells(values){return '<tr>'+values.map(v=>'<td>'+v+'</td>').join('')+'</tr>';}
function empty(colspan){return '<tr><td colspan="'+colspan+'" class="empty">No records available</td></tr>';}
function render(){if(!store)return;const {runs,scans,stages,deployments}=store;
$('total').textContent=runs.length;$('success').textContent=runs.filter(x=>x.status==='success').length;$('failed').textContent=runs.filter(x=>['failure','failed'].includes(x.status)).length;$('blocked').textContent=scans.filter(x=>x.gate_passed===false).length;
$('runs').innerHTML=runs.map(r=>'<tr class="pick '+(String(r.run_id)===selected?'selected':'')+'" data-run="'+safe(r.run_id)+'"><td><code>'+safe(r.run_id)+'</code></td><td>'+safe(r.commit_msg)+'</td><td>'+pill(r.status)+'</td><td>'+date(r.started_at)+'</td></tr>').join('')||empty(4);
$('runselect').innerHTML=runs.map(r=>'<option value="'+safe(r.run_id)+'">'+safe(r.run_id)+' · '+safe(r.status)+'</option>').join('');if(selected)$('runselect').value=selected;
$('deployments').innerHTML=deployments.map(r=>cells([safe(r.run_id),safe(r.image_tag),pill(r.status),safe(r.details)])).join('')||empty(4);
$('events').innerHTML=stages.slice(0,70).map(r=>cells([date(r.created_at),safe(r.run_id),safe(r.stage),pill(r.status),safe(r.details)])).join('')||empty(5);
renderSelected();}
function renderSelected(){if(!store)return;const r=store.runs.find(x=>String(x.run_id)===selected);if(!r){$('details').textContent='No run selected';$('stages').innerHTML='';$('chart').innerHTML='';return;}
const scan=store.scans.find(x=>String(x.run_id)===selected);const events=store.stages.filter(x=>String(x.run_id)===selected).sort((a,b)=>new Date(a.created_at)-new Date(b.created_at));const latest={};events.forEach(x=>latest[x.stage]=x);
$('details').innerHTML='<p><strong>Run '+safe(r.run_id)+'</strong> '+pill(r.status)+'</p><p class="muted">'+safe(r.commit_msg)+'</p><p>Actor: '+safe(r.actor)+'<br>Started: '+date(r.started_at)+'</p>';
$('stages').innerHTML=Object.values(latest).map(x=>'<div class="stage"><strong>'+safe(x.stage)+'</strong>'+pill(x.status)+'</div>').join('')||'<span class="muted">No stage events</span>';
if(!scan){$('scaninfo').textContent='No scan record for this run.';$('chart').innerHTML='';return;}
$('scaninfo').innerHTML='Image: <code>'+safe(scan.image)+'</code><br>Security gate: '+(scan.gate_passed===true?pill('passed'):scan.gate_passed===false?pill('blocked'):pill('unknown'));
const values=[['Critical',scan.critical,'critical'],['High',scan.high,'high'],['Medium',scan.medium,'medium'],['Low',scan.low,'low']];const max=Math.max(1,...values.map(x=>Number(x[1])||0));$('chart').innerHTML=values.map(([name,value,color])=>'<div class="barrow"><span>'+name+'</span><div class="track"><div class="fill '+color+'" style="width:'+Math.max(0,(Number(value)||0)/max*100)+'%"></div></div><strong>'+safe(value)+'</strong></div>').join('');}
function choose(id){selected=String(id);render();}
$('runs').addEventListener('click',e=>{const tr=e.target.closest('tr[data-run]');if(tr)choose(tr.dataset.run);});$('runselect').addEventListener('change',e=>choose(e.target.value));
async function refresh(){try{const response=await fetch('/api/data',{cache:'no-store'});const result=await response.json();if(!response.ok)throw Error(result.error||'API error');store=result;if(!store.runs.some(r=>String(r.run_id)===selected))selected=store.runs.length?String(store.runs[0].run_id):null;render();$('error').textContent='';$('connection').className='pill success';$('connection').textContent='Neon connected';$('updated').textContent='Updated '+new Date().toLocaleTimeString();}catch(err){$('error').textContent='Could not refresh: '+err.message;$('connection').className='pill failed';$('connection').textContent='Disconnected';console.error(err);}}
$('refresh').addEventListener('click',refresh);refresh();setInterval(refresh,5000);
</script></body></html>'''

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
