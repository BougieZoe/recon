"""
RECON Person Mode API Server
Flask server on port 5001+ providing clean API endpoints for person analysis.
"""

import asyncio
import json
import logging
import os
import socket
import threading
import uuid
import webbrowser
from queue import Queue, Empty
from datetime import datetime

from flask import Flask, Response, jsonify, request, render_template_string

from . import person_sources
from . import person_ai

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

HISTORY_PATH = os.path.expanduser("~/.recon/history.json")
app = Flask(__name__)
sessions = {}
_server_instance = None
_server_port = [None]


def _find_free_port(start=5001, max_attempts=20):
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


# ─── Scraping + AI logic (background) ─────────────────────────────


def _run_search(sid, target, website):
    queue = sessions[sid]["queue"]

    def status_cb(name, status):
        queue.put({"type": "source_status", "source": name, "status": status})

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        parsed, sources_data = loop.run_until_complete(
            person_sources.run_all_sources(target, website=website, status_callback=status_cb)
        )
        loop.close()
    except Exception as e:
        queue.put({"type": "error", "message": str(e)})
        return

    raw_parts = []
    text_lengths = {}
    for src_name, src_data in sources_data.items():
        if src_data.get("raw_text"):
            raw_parts.append(f"[{src_name}]\n{src_data['raw_text'][:2000]}")
            text_lengths[src_name] = len(src_data["raw_text"])
            queue.put({"type": "source_update", "source": src_name, "status": "ok", "text_length": len(src_data["raw_text"])})

    raw_text = "\n\n".join(raw_parts) if raw_parts else "No data collected from any source."
    total_len = len(raw_text)
    low_data = total_len < 200

    if low_data:
        queue.put({"type": "warning", "message": "insufficient data — results are speculative"})

    try:
        intent_map = person_ai.analyze_person(raw_text)
    except Exception as e:
        intent_map = {
            "core_drive": "AI analysis failed", "recurring_signals": [],
            "workarounds": [], "direction": str(e),
            "contact_window": "", "confidence": 0, "data_quality": "low", "error": str(e),
        }

    if low_data:
        intent_map["confidence"] = min(intent_map.get("confidence", 0), 20)

    intent_map["_raw_text_length"] = total_len
    intent_map["_sources"] = {
        name: {"status": "ok" if d.get("raw_text") else "failed", "text_length": len(d.get("raw_text", ""))}
        for name, d in sources_data.items()
    }

    sessions[sid]["result"] = intent_map
    _save_history(target, website, intent_map)
    queue.put({"type": "analysis_complete", "result": intent_map})


def _save_history(target, website, intent_map):
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    history = []
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH) as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []
    entry = {
        "target": target, "website": website,
        "timestamp": datetime.utcnow().isoformat(),
        "result": intent_map,
    }
    history.insert(0, entry)
    history = history[:10]
    try:
        with open(HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


# ─── Flask Routes ────────────────────────────────────────────────


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "version": "2.0"})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid JSON"}), 400
    target = (data.get("target") or "").strip()
    website = (data.get("website") or "").strip()
    if not target and not website:
        return jsonify({"error": "enter at least a name or website"}), 400

    sid = str(uuid.uuid4())
    event_queue = Queue()
    sessions[sid] = {"queue": event_queue, "result": None}

    thread = threading.Thread(target=_run_search, args=(sid, target, website))
    thread.daemon = True
    thread.start()

    return jsonify({"session_id": sid})


@app.route("/api/stream/<sid>")
def api_stream(sid):
    session = sessions.get(sid)
    if not session:
        return jsonify({"error": "session not found"}), 404

    def gen():
        queue = session["queue"]
        try:
            while True:
                try:
                    msg = queue.get(timeout=30)
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                    if msg.get("type") in ("analysis_complete", "error"):
                        break
                except Empty:
                    yield f"data: {json.dumps({'type':'error','message':'timeout'})}\n\n"
                    break
        finally:
            sessions.pop(sid, None)

    return Response(gen(), mimetype="text/event-stream")


@app.route("/api/history")
def api_history():
    if not os.path.exists(HISTORY_PATH):
        return jsonify([])
    try:
        with open(HISTORY_PATH) as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, OSError):
        return jsonify([])


# ─── HTML Frontend (same as person_web.py) ───────────────────────


HISTORY_JS = "/api/history"

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RECON — Person Mode</title>
<style>
:root{--bg:#0a0a0f;--surface:#12121a;--border:#1e1e2a;--text:#c8c8d0;--dim:#6b6b78;--primary:#00ff41;--warning:#f59e0b;--error:#ef4444;--input-bg:#181825;--radius:8px}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,sans-serif;display:flex;min-height:100vh}
a{color:var(--primary);text-decoration:none}
#sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);padding:20px;display:flex;flex-direction:column;flex-shrink:0;overflow-y:auto;max-height:100vh}
#sidebar h3{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
#history-list{list-style:none}
#history-list li{padding:8px 10px;border-radius:var(--radius);cursor:pointer;font-size:13px;color:var(--text);margin-bottom:4px;transition:background .15s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#history-list li:hover{background:var(--input-bg);color:var(--primary)}
#main{flex:1;display:flex;flex-direction:column;max-width:900px;margin:0 auto;padding:30px 24px 80px;width:100%}
#header{text-align:center;margin-bottom:24px}
#header .art{font-family:'Courier New',monospace;font-size:11px;line-height:1.2;color:var(--primary);white-space:pre;margin-bottom:12px}
#header .subtitle{color:var(--primary);font-size:13px;font-weight:600;letter-spacing:2px}
#squares{display:flex;justify-content:center;gap:6px;margin:12px 0 4px;cursor:pointer}
#squares span{width:20px;height:20px;border-radius:50%;display:inline-block;transition:transform .2s,box-shadow .2s}
#squares span:hover{transform:scale(1.25);box-shadow:0 0 12px currentColor}
.sq-cyan{background:#22d3ee}.sq-green{background:#00ff41}.sq-pink{background:#ff6eb4}
#inputs{margin-bottom:20px}
.input-row{display:flex;gap:12px;margin-bottom:10px;flex-wrap:wrap}
.input-row input{flex:1;min-width:200px;padding:12px 14px;border-radius:var(--radius);border:1px solid var(--border);background:var(--input-bg);color:var(--text);font-size:14px;outline:none;transition:border-color .2s}
.input-row input:focus{border-color:var(--primary)}
.input-row input::placeholder{color:var(--dim)}
.btn-search{padding:12px 28px;border:none;border-radius:var(--radius);background:var(--primary);color:var(--bg);font-weight:700;font-size:14px;cursor:pointer;transition:opacity .2s;white-space:nowrap}
.btn-search:hover{opacity:.85}
.btn-search:disabled{opacity:.4;cursor:not-allowed}
#sources-panel{margin-bottom:20px;display:none}
#sources-panel.visible{display:block}
#sources-panel h3{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.source-row{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--radius);background:var(--surface);margin-bottom:4px;font-size:13px;opacity:0;animation:fadeIn .3s forwards}
.source-row .icon{width:18px;text-align:center;font-size:15px}
.source-row.done{color:var(--primary)}
.source-row.failed{color:var(--error)}
.source-row.scanning{color:var(--dim)}
.source-row .spin{animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes fadeIn{to{opacity:1}}
@keyframes slideUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
#data-warning{display:none;padding:10px 14px;border-radius:var(--radius);background:rgba(245,158,11,0.12);color:var(--warning);font-size:13px;margin-bottom:16px;animation:fadeIn .4s forwards}
#results{display:none}
#results.visible{display:block}
.result-section{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:8px;overflow:hidden;animation:slideUp .3s forwards}
.result-header{display:flex;align-items:center;gap:10px;padding:14px 16px;cursor:pointer;user-select:none;transition:background .15s;font-size:13px;font-weight:600;color:var(--text)}
.result-header:hover{background:var(--input-bg)}
.result-header .arrow{transition:transform .2s;font-size:12px}
.result-header .arrow.open{transform:rotate(90deg)}
.result-body{padding:0 16px 14px;font-size:13px;line-height:1.6;color:var(--dim);display:none}
.result-body.open{display:block}
.result-body ul{list-style:none;padding:0}
.result-body ul li{padding:3px 0}
.result-body ul li::before{content:'· ';color:var(--primary)}
.meta-row{display:flex;gap:20px;padding:12px 16px;font-size:13px;flex-wrap:wrap}
.meta-row .label{color:var(--dim)}
.meta-row .value{font-weight:600}
.confidence-bar{height:6px;background:var(--border);border-radius:3px;margin:6px 0;overflow:hidden}
.confidence-bar div{height:100%;border-radius:3px;transition:width .6s ease}
#sidebar .empty{color:var(--dim);font-size:12px;font-style:italic}
@media(max-width:768px){body{flex-direction:column}#sidebar{width:100%;max-height:none;padding:12px 16px;flex-direction:row;flex-wrap:wrap;gap:8px;align-items:center}#sidebar h3{margin-bottom:0;margin-right:8px}#history-list{display:flex;gap:6px;overflow-x:auto;flex:1}#history-list li{flex-shrink:0;font-size:12px;padding:4px 8px}.empty{display:none}#main{padding:16px}.input-row input{min-width:100%}}
</style>
</head>
<body>
<div id="sidebar"><h3>History</h3><ul id="history-list"></ul></div>
<div id="main">
<div id="header">
  <div class="art">
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
  </div>
  <div class="subtitle">[ PASSIVE INTELLIGENCE SYSTEM v2.0 — PERSON MODE ]</div>
  <div id="squares">
    <span class="sq-cyan" data-theme="cyan" title="cyan"></span>
    <span class="sq-green" data-theme="green" title="green"></span>
    <span class="sq-pink" data-theme="pink" title="pink"></span>
  </div>
</div>
<div id="inputs">
  <div class="input-row">
    <input id="target-input" type="text" placeholder="TARGET › name or @handle (optional)" list="target-datalist" autocomplete="off">
    <datalist id="target-datalist"></datalist>
    <input id="website-input" type="text" placeholder="WEBSITE › url or domain (optional)">
  </div>
  <button class="btn-search" id="search-btn" onclick="startSearch()">⟐ SEARCH</button>
</div>
<div id="sources-panel"><h3>SOURCES</h3><div id="sources-list"></div></div>
<div id="data-warning">⚠ insufficient data — results are speculative</div>
<div id="results"></div>
</div>
<script>
const API_BASE = '';
const SOURCES = ["nitter","github","duckduckgo_news","linkedin","instagram","website"];
const THEMES={cyan:{primary:"#22d3ee",warning:"#f59e0b",error:"#ef4444"},green:{primary:"#00ff41",warning:"#f59e0b",error:"#ef4444"},pink:{primary:"#ff6eb4",warning:"#f59e0b",error:"#ef4444"}};
let currentTheme="green";
let history=JSON.parse(localStorage.getItem("recon_history")||"[]");

function applyTheme(n){currentTheme=n;const t=THEMES[n];document.documentElement.style.setProperty("--primary",t.primary);document.documentElement.style.setProperty("--warning",t.warning);document.documentElement.style.setProperty("--error",t.error);localStorage.setItem("recon_theme",n);}
document.querySelectorAll("#squares span").forEach(sq=>{sq.addEventListener("click",()=>applyTheme(sq.dataset.theme));});
const savedTheme=localStorage.getItem("recon_theme")||"green";applyTheme(savedTheme);

function escapeHtml(s){return String(s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}

function renderHistory(){
  const ul=document.getElementById("history-list");
  if(!history.length){ul.innerHTML='<li class="empty">No searches yet</li>';return;}
  ul.innerHTML=history.map((item,i)=>'<li onclick="reloadHistory('+i+')">'+escapeHtml(item.target||item)+'</li>').join("");
  const dl=document.getElementById("target-datalist");
  dl.innerHTML=history.map(item=>'<option value="'+escapeHtml(item.target||item)+'">').join("");
}
function reloadHistory(i){const item=history[i];document.getElementById("target-input").value=item.target||item;document.getElementById("website-input").value=item.website||"";startSearch();}
function addHistory(target,website){
  const entry={target,website,ts:Date.now()};
  history=history.filter(h=>(h.target||h)!==(target||""));history.unshift(entry);if(history.length>10)history=history.slice(0,10);
  localStorage.setItem("recon_history",JSON.stringify(history));renderHistory();
}

function startSearch(){
  const target=document.getElementById("target-input").value.trim();
  const website=document.getElementById("website-input").value.trim();
  if(!target&&!website){alert("Enter at least a name or website");return;}
  addHistory(target||"",website||"");
  document.getElementById("search-btn").disabled=true;
  document.getElementById("results").classList.remove("visible");document.getElementById("results").innerHTML="";
  document.getElementById("data-warning").style.display="none";
  document.getElementById("sources-panel").classList.add("visible");
  const list=document.getElementById("sources-list");
  list.innerHTML=SOURCES.map(s=>'<div class="source-row scanning" data-src="'+s+'"><span class="icon spin">◉</span> '+s+'</div>').join("");

  fetch(API_BASE+"/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target,website})})
  .then(r=>r.json()).then(data=>{
    const es=new EventSource(API_BASE+"/api/stream/"+data.session_id);
    es.onmessage=function(e){
      const msg=JSON.parse(e.data);
      if(msg.type==="source_status"||msg.type==="source_update"){
        const row=list.querySelector('[data-src="'+msg.source+'"]');
        if(row){const s=msg.status||"done";row.className="source-row "+s;row.innerHTML='<span class="icon">'+(s==="done"?"✓":s==="failed"?"✗":"◉")+'</span> '+msg.source;}
      }else if(msg.type==="warning"){
        document.getElementById("data-warning").style.display="block";
      }else if(msg.type==="analysis_complete"){
        es.close();document.getElementById("search-btn").disabled=false;renderResults(msg.result);
      }else if(msg.type==="error"){
        es.close();document.getElementById("search-btn").disabled=false;document.getElementById("results").innerHTML='<div class="source-row failed">✗ '+escapeHtml(msg.message)+'</div>';
      }
    };es.onerror=function(){es.close();document.getElementById("search-btn").disabled=false;};
  }).catch(()=>{document.getElementById("search-btn").disabled=false;});
}

function renderResults(m){
  const container=document.getElementById("results");container.classList.add("visible");let html="";
  const sections=[
    {key:"core_drive",label:"CORE DRIVE",open:true},
    {key:"recurring_signals",label:"RECURRING SIGNALS",list:true,open:false},
    {key:"workarounds",label:"WORKAROUNDS",list:true,open:false},
    {key:"direction",label:"DIRECTION",open:false},
    {key:"contact_window",label:"CONTACT WINDOW",open:false},
  ];
  sections.forEach((s,idx)=>{
    const val=m[s.key];if(!val||(Array.isArray(val)&&!val.length))return;
    const bodyId="sec-"+idx;const isArr=Array.isArray(val);
    const bodyContent=isArr?"<ul>"+val.map(v=>"<li>"+escapeHtml(v)+"</li>").join("")+"</ul>":escapeHtml(val);
    html+='<div class="result-section" style="animation-delay:'+(idx*0.08)+'s"><div class="result-header" onclick="toggleSection(\''+bodyId+'\')"><span class="arrow '+(s.open?"open":"")+'">▶</span> '+s.label+'</div><div id="'+bodyId+'" class="result-body '+(s.open?"open":"")+'">'+bodyContent+'</div></div>';
  });
  const conf=m.confidence||0;const dq=m.data_quality||"unknown";
  html+='<div class="result-section"><div class="meta-row"><span><span class="label">confidence</span> <span class="value">'+conf+'/100</span></span><span><span class="label">data quality</span> <span class="value">'+dq.toUpperCase()+'</span></span></div><div style="padding:0 16px 14px"><div class="confidence-bar"><div style="width:'+conf+'%"></div></div></div></div>';
  container.innerHTML=html;
}
function toggleSection(id){const body=document.getElementById(id);if(!body)return;const arrow=body.previousElementSibling.querySelector(".arrow");body.classList.toggle("open");arrow.classList.toggle("open");}
renderHistory();
</script>
</body>
</html>"""


@app.route("/person")
def person_page():
    return HTML_PAGE, 200, {"Content-Type": "text/html; charset=utf-8"}


# ─── Server lifecycle ────────────────────────────────────────────


def get_server_port():
    return _server_port[0]


def ensure_server():
    """Start the API server in a background thread if not already running."""
    if _server_instance and _server_instance.is_alive():
        return _server_port[0]
    return _start_server_thread()


def _start_server_thread():
    port = _find_free_port()
    _server_port[0] = port

    def run():
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    _server_instance = t
    # Wait for server to be ready
    import time
    import httpx
    for _ in range(50):
        time.sleep(0.1)
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/api/health", timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            continue
    return port


def run_person_server(open_browser=False):
    """Entry point for `--person --web` CLI flag."""
    port = _start_server_thread()
    url = f"http://localhost:{port}/person"
    print(f"  RECON Person API running at http://127.0.0.1:{port}")
    print(f"  Web UI at {url}")
    if open_browser:
        webbrowser.open(url)
    print("  Press Ctrl+C to stop.")
    try:
        _server_instance.join()
    except KeyboardInterrupt:
        print("  shutdown.")
