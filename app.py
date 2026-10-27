import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify

app = Flask(__name__)


def q(sql):
    with psycopg2.connect(os.environ["NEON_URL"]) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()


@app.get("/api/state")
def state():
    return jsonify(
        runs=q("select * from pipeline_runs order by started_at desc limit 10"),
        stages=q("select * from stage_events order by id desc limit 80"),
        scans=q("select * from scan_results order by id desc limit 10"),
        deployments=q("select * from deployments order by id desc limit 10"),
    )


PAGE = """<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecureFlow Mission Control</title>
<style>
 body{font-family:system-ui,sans-serif;margin:24px;background:#0f172a;color:#e2e8f0}
 h1,h2{margin:.4em 0} table{border-collapse:collapse;width:100%;margin-bottom:24px;font-size:14px}
 th,td{border-bottom:1px solid #334155;padding:6px 8px;text-align:left}
 .pill{display:inline-block;padding:6px 10px;border-radius:999px;background:#334155;margin:2px;font-size:13px}
 .success,.healthy{background:#166534}.failed,.stalled{background:#991b1b}
 .running{background:#b45309}.pending{background:#1d4ed8}
</style>
<h1>SecureFlow Mission Control</h1><div id="app">Loading...</div>
<script>
const STAGES=["BUILD","SCAN","POLICY","PUBLISH","MANIFEST-UPDATE","SYNC","NOTIFY"];
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function table(title,rows,cols){
  let h="<h2>"+title+"</h2><table><tr>"+cols.map(c=>"<th>"+c+"</th>").join("")+"</tr>";
  for(const r of rows){h+="<tr>"+cols.map(c=>"<td>"+esc(r[c])+"</td>").join("")+"</tr>";}
  return h+"</table>";
}
async function load(){
  try{
    const d=await (await fetch("/api/state")).json();
    const run=d.runs[0]; let html="<h2>Latest pipeline run</h2>";
    if(run){
      const ev=d.stages.filter(e=>e.run_id===run.run_id);
      html+="<p>"+esc(run.commit_sha.slice(0,7))+" by "+esc(run.actor)+" - <b>"+esc(run.status)+"</b></p><div>";
      for(const s of STAGES){
        const last=ev.filter(e=>e.stage===s).sort((a,b)=>b.id-a.id)[0];
        const st=last?last.status:"waiting";
        html+='<span class="pill '+esc(st)+'">'+s+": "+esc(st)+"</span>";
      }
      html+="</div>";
    }
    html+=table("Vulnerability reports",d.scans,["image","critical","high","medium","low","gate_passed"]);
    html+=table("Deployment timeline",d.deployments,["created_at","image_tag","status","details"]);
    html+=table("Recent runs",d.runs,["run_id","commit_sha","actor","status","started_at"]);
    document.getElementById("app").innerHTML=html;
  }catch(e){document.getElementById("app").textContent="Error: "+e;}
}
load(); setInterval(load,5000);
</script>"""


@app.get("/")
def index():
    return PAGE
