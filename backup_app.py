
import os
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()

app = Flask(__name__)

def query(sql):
    with psycopg.connect(os.environ["NEON_URL"], row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

@app.get("/api/data")
def data():
    try:
        return jsonify({
            "runs": query("""
                SELECT * FROM pipeline_runs
                ORDER BY started_at DESC LIMIT 20
            """),
            "stages": query("""
                SELECT * FROM stage_events
                ORDER BY created_at DESC LIMIT 100
            """),
            "scans": query("""
                SELECT * FROM scan_results
                ORDER BY created_at DESC LIMIT 20
            """),
            "deployments": query("""
                SELECT * FROM deployments
                ORDER BY created_at DESC LIMIT 20
            """)
        })
    except Exception:
        app.logger.exception("Database query failed")
        return jsonify({"error": "Database connection or query failed"}), 500

@app.get("/")
def home():
    return render_template_string(PAGE)

PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecureFlow Dashboard</title>
<style>
body{margin:0;background:#0b1120;color:#e2e8f0;font-family:Arial,sans-serif;padding:28px}
h1{color:#38bdf8;margin-bottom:5px}
small{color:#94a3b8}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:15px;margin:24px 0}
.card,.panel{background:#172338;border:1px solid #334155;border-radius:12px;padding:20px}
.number{font-size:32px;font-weight:bold;margin-top:10px}
.panel{margin:20px 0;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:12px;text-align:left;border-bottom:1px solid #334155}
th{color:#94a3b8}
.success{color:#4ade80}.failed{color:#fb7185}
.running,.pending{color:#facc15}
button{background:#0284c7;color:white;border:0;border-radius:8px;padding:10px;cursor:pointer}
#error{color:#fb7185}
</style>
</head>
<body>
<h1>🛡 SecureFlow</h1>
<small>DevSecOps Pipeline Monitoring • Neon PostgreSQL</small>
<p><button onclick="refresh()">Refresh now</button>
<small id="updated"></small></p>
<p id="error"></p>
<div class="cards" id="cards"></div>
<div class="panel"><h2>Pipeline Runs</h2><div id="runs"></div></div>
<div class="panel"><h2>Vulnerability Scan Results</h2><div id="scans"></div></div>
<div class="panel"><h2>Pipeline Stage History</h2><div id="stages"></div></div>
<div class="panel"><h2>Deployments</h2><div id="deployments"></div></div>

<script>
function safe(value) {
  return String(value ?? "-").replace(/[&<>"']/g, c =>
    ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[c]
  );
}

function makeTable(rows, columns) {
  if (!rows || rows.length === 0) {
    return "<p>No records available</p>";
  }

  let html = "<table><thead><tr>";

  columns.forEach(col => {
    html += "<th>" + safe(col) + "</th>";
  });

  html += "</tr></thead><tbody>";

  rows.forEach(row => {
    html += "<tr>";
    columns.forEach(col => {
      html += "<td>" + safe(row[col]) + "</td>";
    });
    html += "</tr>";
  });

  return html + "</tbody></table>";
}

async function refresh() {
  try {
    const response = await fetch("/api/data");
    if (!response.ok) throw new Error("API request failed");

    const d = await response.json();

    const success = d.runs.filter(
      r => r.status === "success"
    ).length;

    const failed = d.runs.filter(
      r => r.status === "failure" || r.status === "failed"
    ).length;

    const blocked = d.scans.filter(
      s => s.gate_passed === false
    ).length;

    const cards = [
      ["Recent Runs", d.runs.length],
      ["Successful", success],
      ["Failed", failed],
      ["Blocked Scans", blocked]
    ];

    document.getElementById("cards").innerHTML =
      cards.map(c =>
        '<div class="card"><small>' + safe(c[0]) +
        '</small><div class="number">' + safe(c[1]) +
        '</div></div>'
      ).join("");

    document.getElementById("runs").innerHTML =
      makeTable(d.runs,
        ["run_id", "commit_msg", "actor", "status", "started_at"]);

    document.getElementById("scans").innerHTML =
      makeTable(d.scans,
        ["run_id", "critical", "high", "medium", "low", "gate_passed"]);

    document.getElementById("stages").innerHTML =
      makeTable(d.stages,
        ["run_id", "stage", "status", "details", "created_at"]);

    document.getElementById("deployments").innerHTML =
      makeTable(d.deployments,
        ["run_id", "image_tag", "status", "details", "created_at"]);

    document.getElementById("updated").textContent =
      "Updated " + new Date().toLocaleTimeString();

    document.getElementById("error").textContent = "";

  } catch (error) {
    document.getElementById("error").textContent =
      "Dashboard error: " + error.message;
    console.error(error);
  }
}

refresh();
setInterval(refresh, 5000);
</script>

</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
