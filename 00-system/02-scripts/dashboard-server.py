#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""프로젝트 포트폴리오 대시보드 — 공유 서버 (표준 라이브러리만).
화면(포트폴리오_대시보드.html)과 JSON API를 한 서버에서 서빙한다.
PM이 수정하면 서버에 저장되어 대표·팀원 모두 같은 데이터를 본다.

데이터: 00-system/01-templates/_data/  (users.json + projects/{id}.json)
권한:   대표=전체 열람·수정·생성·삭제 / PM=본인 프로젝트 수정 / 직원=배정 프로젝트 열람
실행:   python3 dashboard-server.py [port]   (기본 8770, 127.0.0.1 — Tailscale serve로 노출)
"""
import json, os, re, threading, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import urlopen, Request
from urllib.error import URLError
from pathlib import Path

# .env 로드(WEEKLY_KEY 등 — 환경 미설정 시 do-better-workspace/.env에서 보충)
_WS = Path(__file__).resolve().parent.parent.parent
for _envp in (_WS / ".env",):
    if _envp.exists():
        for _l in _envp.read_text(encoding="utf-8").splitlines():
            _l = _l.strip()
            if _l and not _l.startswith("#") and "=" in _l:
                _k, _, _v = _l.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

# 이관 가능: 경로는 스크립트 기준(상대) + 환경변수로 덮어쓰기 가능
BASE = Path(os.environ.get("DASHBOARD_BASE") or (Path(__file__).resolve().parent.parent / "01-templates"))
HTML = BASE / "포트폴리오_대시보드.html"
DATA = Path(os.environ.get("DASHBOARD_DATA") or (BASE / "_data"))
PROJ_DIR = DATA / "projects"
HOST = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("DASHBOARD_PORT", "8770"))
# ARISA 주간 대시보드 서빙 — /weekly. 성장지표는 대표 토큰(?key=WEEKLY_KEY)일 때만 노출.
WEEKLY_DIR = Path(os.environ.get("WEEKLY_DIR") or (_WS / "20-operations" / "23-arisa" / "weekly"))
WEEKLY_KEY = os.environ.get("WEEKLY_KEY", "")
# ARISA 대표 Daily Brief — /brief. HTML 내장 로그인이 대표(admin)만 입장시킴.
BRIEF_DIR = Path(os.environ.get("BRIEF_DIR") or (_WS / "20-operations" / "23-arisa" / "brief"))
# 팀 리더 판정 출처 — arisa-employees.json의 team_leads(팀→리더이름) 역매핑.
EMP_PATH = Path(__file__).resolve().parent / "arisa-employees.json"
# ARISA 2.0 리버스 프록시 — /arisa2/* → localhost:ARISA2_PORT
ARISA2_PORT = int(os.environ.get("ARISA2_PORT", "8787"))
ARISA2_UPSTREAM = f"http://127.0.0.1:{ARISA2_PORT}"
_lock = threading.Lock()

# /dashboard — 대표 전용 통합 셸: 로그인 1회 후 탭[오늘 Brief / 이번 주 / Decision Window]을 iframe으로 전환.
# iframe 격리라 대시보드 CSS 충돌 없음. 통합 로그인이 brief_sess/weekly_sess를 미리 세팅해
# 각 iframe(/brief·/weekly·/arisa2/)이 게이트를 자동 통과(깜빡임 최소). aggregator·/api/login 무수정.
DASHBOARD_SHELL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARISA 대시보드</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;--accent:#6C5CE7;--red:#E17055}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300}
#login-gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:100}
#login-box{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:38px 40px;width:330px;text-align:center}
#login-box h2{font-size:19px;font-weight:600;margin-bottom:6px}
#login-box .lg-sub{color:var(--muted);font-size:13px;margin-bottom:22px}
#login-box input{width:100%;background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--fg);font-size:14px;margin-bottom:10px;font-family:inherit}
#login-box button{width:100%;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:12px;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}
#login-err{color:var(--red);font-size:12px;margin-top:12px;min-height:16px}
#shell{display:none;flex-direction:column;height:100vh}
#tabs{display:flex;gap:6px;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--bg-2);align-items:center;flex-shrink:0}
.tab{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:8px 18px;font-size:14px;cursor:pointer;font-family:inherit;font-weight:500}
.tab.on{background:var(--accent);color:#fff;border-color:var(--accent)}
#scope-sel{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:8px 12px;font-size:13px;font-family:inherit}
#tabs .who{margin-left:auto;font-size:12px;color:var(--muted)}
#tabs .who a{color:var(--accent);cursor:pointer;margin-left:8px}
.frame{flex:1;border:0;width:100%;display:none;background:var(--bg)}
.frame.on{display:block}
#arisa2-status{font-size:11px;color:var(--muted);margin-left:6px}
#arisa2-status.ok{color:#00b894}
#arisa2-status.err{color:var(--red)}
</style></head>
<body>
<div id="login-gate"><div id="login-box">
  <h2>ARISA 대시보드</h2>
  <div class="lg-sub">대표 전용 · 로그인</div>
  <input id="lg-id" placeholder="이름" autocomplete="username">
  <input id="lg-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="lg-btn">로그인</button>
  <div id="login-err"></div>
</div></div>
<div id="shell">
  <div id="tabs">
    <button class="tab on" data-t="brief">오늘 Brief</button>
    <button class="tab" data-t="weekly">이번 주</button>
    <button class="tab" data-t="decision">Decision Window</button>
    <span id="arisa2-status"></span>
    <select id="scope-sel" style="display:none"></select>
    <span class="who" id="who"></span>
  </div>
  <iframe class="frame on" id="f-brief"></iframe>
  <iframe class="frame" id="f-weekly"></iframe>
  <iframe class="frame" id="f-decision"></iframe>
</div>
<script>
(function(){
  var gate=document.getElementById('login-gate'), shell=document.getElementById('shell'), who=document.getElementById('who');
  var sel=document.getElementById('scope-sel');
  var fb=document.getElementById('f-brief'), fw=document.getElementById('f-weekly'), fd=document.getElementById('f-decision');
  var a2s=document.getElementById('arisa2-status');
  var loaded={brief:false,weekly:false,decision:false}, curScope='';
  function srcFor(t){
    if(t==='decision') return '/arisa2/';
    if(curScope===''){ return t==='brief' ? '/brief' : '/weekly'; }
    return (t==='brief' ? '/team-brief?team=' : '/team-weekly?team=') + encodeURIComponent(curScope);
  }
  function showTab(t){
    document.querySelectorAll('.tab').forEach(function(b){ b.classList.toggle('on', b.dataset.t===t); });
    fb.classList.toggle('on', t==='brief'); fw.classList.toggle('on', t==='weekly'); fd.classList.toggle('on', t==='decision');
    if(t==='weekly' && !loaded.weekly){ fw.src=srcFor('weekly'); loaded.weekly=true; }
    if(t==='decision' && !loaded.decision){ fd.src=srcFor('decision'); loaded.decision=true; }
  }
  function loadScope(scope){
    curScope=scope; loaded={brief:false,weekly:false,decision:false};
    fb.src=srcFor('brief'); loaded.brief=true;
    fw.src='about:blank'; fd.src='about:blank';
    showTab('brief');
  }
  function checkArisa2(){
    fetch('/arisa2/api/health',{method:'GET'}).then(function(r){
      a2s.textContent=r.ok?'ARISA 2.0 ON':'ARISA 2.0 OFF';
      a2s.className=r.ok?'ok':'err';
    }).catch(function(){ a2s.textContent='ARISA 2.0 OFF'; a2s.className='err'; });
  }
  function enter(s){
    var j=JSON.stringify(s);
    ['brief_sess','weekly_sess','team_brief_sess','team_weekly_sess'].forEach(function(k){ localStorage.setItem(k,j); });
    gate.style.display='none'; shell.style.display='flex';
    who.innerHTML = s.name+' ('+(s.role||'')+') <a id="lg-out">로그아웃</a>';
    document.getElementById('lg-out').onclick=function(){ ['arisa_sess','brief_sess','weekly_sess','team_brief_sess','team_weekly_sess'].forEach(function(k){localStorage.removeItem(k);}); location.reload(); };
    if(s.lead_teams && s.lead_teams.length){
      sel.style.display='inline-block'; sel.innerHTML='<option value="">전체</option>';
      s.lead_teams.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
      sel.onchange=function(){ loadScope(sel.value); };
    } else { sel.style.display='none'; }
    loadScope('');
    checkArisa2();
  }
  document.querySelectorAll('.tab').forEach(function(b){ b.onclick=function(){ showTab(b.dataset.t); }; });
  var sess=null; try{ sess=JSON.parse(localStorage.getItem('arisa_sess')||'null'); }catch(e){}
  if(sess && sess.admin) enter(sess);
  function doLogin(){
    var id=document.getElementById('lg-id').value.trim(), pin=document.getElementById('lg-pin').value.trim();
    var err=document.getElementById('login-err'); err.textContent='';
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,pin:pin})})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.ok && d.admin){ localStorage.setItem('arisa_sess',JSON.stringify(d)); enter(d); }
        else if(d.ok && !d.admin){ err.textContent='대표 전용 화면입니다'; }
        else { err.textContent=d.error||'로그인 실패'; }
      })
      .catch(function(){ err.textContent='서버 연결 실패'; });
  }
  document.getElementById('lg-btn').onclick=doLogin;
  document.getElementById('lg-pin').addEventListener('keydown',function(e){ if(e.key==='Enter') doLogin(); });
})();
</script>
</body></html>"""

# /team — 팀 리더 전용 셸. 로그인 1회 후 (2팀 리더는 드롭다운) 탭[오늘 Brief / 이번 주]을
# iframe(/team-brief·/team-weekly?team=)으로 전환. lead_teams 없는 사람은 입장 차단.
TEAM_SHELL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>팀 리더 대시보드</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;--accent:#6C5CE7;--red:#E17055}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300}
#login-gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:100}
#login-box{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:38px 40px;width:330px;text-align:center}
#login-box h2{font-size:19px;font-weight:600;margin-bottom:6px}
#login-box .lg-sub{color:var(--muted);font-size:13px;margin-bottom:22px}
#login-box input{width:100%;background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--fg);font-size:14px;margin-bottom:10px;font-family:inherit}
#login-box button{width:100%;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:12px;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}
#login-err{color:var(--red);font-size:12px;margin-top:12px;min-height:16px}
#shell{display:none;flex-direction:column;height:100vh}
#tabs{display:flex;gap:6px;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--bg-2);align-items:center;flex-shrink:0}
.tab{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:8px 18px;font-size:14px;cursor:pointer;font-family:inherit;font-weight:500}
.tab.on{background:var(--accent);color:#fff;border-color:var(--accent)}
#team-sel{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:8px 12px;font-size:13px;font-family:inherit}
#tabs .who{margin-left:auto;font-size:12px;color:var(--muted)}
#tabs .who a{color:var(--accent);cursor:pointer;margin-left:8px}
.frame{flex:1;border:0;width:100%;display:none;background:var(--bg)}
.frame.on{display:block}
</style></head>
<body>
<div id="login-gate"><div id="login-box">
  <h2>팀 리더 대시보드</h2>
  <div class="lg-sub">팀 리더 전용 · 로그인</div>
  <input id="lg-id" placeholder="이름" autocomplete="username">
  <input id="lg-pin" type="password" placeholder="PIN (첫 로그인 시 설정)" autocomplete="current-password">
  <button id="lg-btn">로그인</button>
  <div id="login-err"></div>
</div></div>
<div id="shell">
  <div id="tabs">
    <button class="tab on" data-t="brief">오늘 Brief</button>
    <button class="tab" data-t="weekly">이번 주</button>
    <select id="team-sel" style="display:none"></select>
    <span class="who" id="who"></span>
  </div>
  <iframe class="frame on" id="f-brief"></iframe>
  <iframe class="frame" id="f-weekly"></iframe>
</div>
<script>
(function(){
  var gate=document.getElementById('login-gate'), shell=document.getElementById('shell'), who=document.getElementById('who');
  var sel=document.getElementById('team-sel');
  var fb=document.getElementById('f-brief'), fw=document.getElementById('f-weekly');
  var SESS=null, curTeam=null, loaded={brief:false,weekly:false};
  function setTeamSess(s){ var j=JSON.stringify(s); localStorage.setItem('team_brief_sess',j); localStorage.setItem('team_weekly_sess',j); }
  function showTab(t){
    document.querySelectorAll('.tab').forEach(function(b){ b.classList.toggle('on', b.dataset.t===t); });
    fb.classList.toggle('on', t==='brief'); fw.classList.toggle('on', t==='weekly');
    if(t==='weekly' && !loaded.weekly){ fw.src='/team-weekly?team='+encodeURIComponent(curTeam); loaded.weekly=true; }
  }
  function loadTeam(t){
    curTeam=t; loaded={brief:false,weekly:false};
    fb.src='/team-brief?team='+encodeURIComponent(t); loaded.brief=true;
    fw.src='about:blank';
    showTab('brief');
  }
  function changePin(){
    var cur=prompt('현재 PIN을 입력하세요'); if(!cur) return;
    var nw=prompt('새 PIN (4자 이상)'); if(!nw) return;
    fetch('/api/set-pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:SESS.name,pin:cur,new_pin:nw})})
      .then(function(r){return r.json();}).then(function(d){ alert(d.ok?'PIN이 변경되었습니다':(d.error||'변경 실패')); });
  }
  function enter(s){
    SESS=s; setTeamSess(s);
    gate.style.display='none'; shell.style.display='flex';
    who.innerHTML = s.name+' ('+(s.role||'')+') <a id="lg-pin-c">PIN변경</a> <a id="lg-out">로그아웃</a>';
    document.getElementById('lg-out').onclick=function(){ ['team_sess','team_brief_sess','team_weekly_sess'].forEach(function(k){localStorage.removeItem(k);}); location.reload(); };
    document.getElementById('lg-pin-c').onclick=changePin;
    if(s.lead_teams.length>1){
      sel.style.display='inline-block'; sel.innerHTML='';
      s.lead_teams.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
      sel.onchange=function(){ loadTeam(sel.value); };
    } else { sel.style.display='none'; }
    loadTeam(s.lead_teams[0]);
  }
  document.querySelectorAll('.tab').forEach(function(b){ b.onclick=function(){ showTab(b.dataset.t); }; });
  var sess=null; try{ sess=JSON.parse(localStorage.getItem('team_sess')||'null'); }catch(e){}
  if(sess && sess.lead_teams && sess.lead_teams.length) enter(sess);
  function doLogin(){
    var id=document.getElementById('lg-id').value.trim(), pin=document.getElementById('lg-pin').value.trim();
    var err=document.getElementById('login-err'); err.textContent='';
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,pin:pin})})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.ok && d.lead_teams && d.lead_teams.length){ localStorage.setItem('team_sess',JSON.stringify(d)); enter(d); if(d.pin_set) err.textContent='PIN이 설정되었습니다'; }
        else if(d.ok){ err.textContent='팀 리더 전용 화면입니다'; }
        else { err.textContent=d.error||'로그인 실패'; }
      })
      .catch(function(){ err.textContent='서버 연결 실패'; });
  }
  document.getElementById('lg-btn').onclick=doLogin;
  document.getElementById('lg-pin').addEventListener('keydown',function(e){ if(e.key==='Enter') doLogin(); });
})();
</script>
</body></html>"""

def load_users():
    try: return json.loads((DATA/"users.json").read_text(encoding="utf-8")).get("users", {})
    except Exception: return {}

def load_projects():
    out = []
    if PROJ_DIR.exists():
        for f in sorted(PROJ_DIR.glob("*.json")):
            try: out.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    return out

def get_project(pid):
    f = PROJ_DIR / f"{_safe(pid)}.json"
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except Exception: return None
    return None

def save_project(p):
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    pid = _safe(p["id"])
    with _lock:
        (PROJ_DIR / f"{pid}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def _safe(pid):
    return re.sub(r"[^A-Za-z0-9가-힣_\-]", "_", str(pid))[:80] or "proj"

def auth(uid, pin):
    u = load_users().get(uid)
    if u and str(u.get("pin")) == str(pin): return u
    return None

def is_admin(uid):
    u = load_users().get(uid)
    return bool(u) and u.get("role") in ("대표", "admin")

def load_emp():
    try: return json.loads(EMP_PATH.read_text(encoding="utf-8"))
    except Exception: return {}

def lead_teams_of(uid):
    """이 사람이 리더인 팀 목록(team_leads 역매핑). 대표(admin)는 전체 팀."""
    tl = load_emp().get("team_leads", {})
    if is_admin(uid):
        return sorted(set(tl.keys()))
    return sorted([team for team, leader in tl.items() if leader == uid])

def set_pin(uid, new_pin):
    """users.json에 PIN 저장(첫 설정/변경). 성공 True."""
    p = DATA / "users.json"
    with _lock:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False
        if uid not in doc.get("users", {}):
            return False
        doc["users"][uid]["pin"] = str(new_pin)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return True

def can_view(uid, p):
    return is_admin(uid) or uid == p.get("pm") or uid in (p.get("members") or [])

def can_edit(uid, p):
    return is_admin(uid) or uid == p.get("pm")

class H(BaseHTTPRequestHandler):
    server_version = "PRDashboard/1.0"
    def log_message(self, *a): pass

    def _proxy_arisa2(self, method="GET"):
        """리버스 프록시: /arisa2/* → ARISA2_UPSTREAM (stdlib only)."""
        # /arisa2/foo → /foo 로 변환 (/arisa2 자체는 / 로)
        upstream_path = self.path[len("/arisa2"):] or "/"
        url = ARISA2_UPSTREAM + upstream_path
        body = None
        if method in ("POST", "PUT", "PATCH"):
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(n) if n else b""
        headers = {}
        ct = self.headers.get("Content-Type")
        if ct:
            headers["Content-Type"] = ct
        try:
            req = Request(url, data=body, headers=headers, method=method)
            with urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/octet-stream"))
                self.send_header("Content-Length", str(len(resp_body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(resp_body)
        except URLError:
            err = b'{"ok":false,"error":"ARISA 2.0 unavailable"}'
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n: return {}
        try: return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception: return {}

    def do_GET(self):
        u = urlparse(self.path); path = u.path; q = parse_qs(u.query)
        if path.startswith("/arisa2"):
            return self._proxy_arisa2("GET")
        if path in ("/", "/index.html"):
            try:
                html = HTML.read_text(encoding="utf-8")
            except Exception:
                return self._send(500, "<h1>대시보드 파일이 없습니다. generate-portfolio.py 실행 필요</h1>".encode("utf-8"), "text/html; charset=utf-8")
            inject = "<script>window.SERVED=true;window.API_BASE='/api';</script>\n</head>"
            html = html.replace("</head>", inject, 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/weekly":
            # 로그인은 HTML 내장 JS가 /api/login으로 처리. 성장지표(.growth)는 admin(대표)만
            # CSS로 노출(직원 로그인 시 숨김 — 측정설계 v2). 서버는 최신 HTML만 서빙.
            # 날짜 형식만 매칭(팀 suffix 파일 `…-W26-공간팀.html` 격리)
            files = sorted(f for f in WEEKLY_DIR.glob("weekly-report-2*.html")
                           if re.fullmatch(r"weekly-report-\d{4}-W\d{2}", f.stem))
            if not files:
                return self._send(404, "<h1>주간 대시보드가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, files[-1].read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/brief":
            # 대표 Daily Brief — 로그인은 HTML 내장 JS가 /api/login으로 처리(대표 admin만 입장).
            # 날짜 네비: 업무 맥락 위해 오늘 + 직전 3영업일(주말 제외)을 버튼으로 주입. ?date=로 전환.
            # 날짜 형식만 매칭(팀 suffix 파일 `…-06-30-공간팀.html` 격리)
            files = sorted(f for f in BRIEF_DIR.glob("daily-brief-2*.html")
                           if re.fullmatch(r"daily-brief-\d{4}-\d{2}-\d{2}", f.stem))
            if not files:
                return self._send(404, "<h1>오늘 브리프가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            biz = []  # 영업일 brief 날짜(월~금)
            for f in files:
                ds = f.stem.replace("daily-brief-", "")
                try:
                    if datetime.datetime.strptime(ds, "%Y-%m-%d").weekday() < 5:
                        biz.append(ds)
                except ValueError:
                    pass
            recent = biz[-4:]  # 오늘 + 직전 3영업일
            sel = (q.get("date") or [""])[0]
            target = BRIEF_DIR / f"daily-brief-{sel}.html"
            if not (sel and target.exists()):
                target = files[-1]
                sel = files[-1].stem.replace("daily-brief-", "")
            wk = ["월", "화", "수", "목", "금", "토", "일"]
            btns = []
            for ds in recent:
                d = datetime.datetime.strptime(ds, "%Y-%m-%d")
                lab = f"{wk[d.weekday()]} {d.strftime('%m/%d')}"
                on = "background:var(--accent);color:#fff;border-color:var(--accent)" if ds == sel else "color:var(--muted)"
                btns.append(f'<a href="/brief?date={ds}" style="text-decoration:none;border:1px solid var(--line);'
                            f'border-radius:7px;padding:5px 12px;font-size:12px;{on}">{lab}</a>')
            nav = ('<div style="display:flex;gap:6px;margin:0 0 18px;align-items:center">'
                   '<span style="color:var(--muted);font-size:11px;margin-right:4px">최근 영업일</span>'
                   + "".join(btns) + '</div>')
            html = target.read_text(encoding="utf-8").replace("</header>", "</header>" + nav, 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/dashboard":
            # 대표 전용 통합 셸 — 로그인 1회 후 탭(오늘 Brief / 이번 주)을 iframe으로 전환.
            return self._send(200, DASHBOARD_SHELL.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/team":
            # 팀 리더 전용 셸 — lead_teams 기반 입장. (2팀 리더는 드롭다운)
            return self._send(200, TEAM_SHELL.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/team-brief":
            # 팀 Brief — 로그인은 셸이 처리(team_brief_sess). team별 파일 + 날짜네비.
            team = (q.get("team") or [""])[0]
            if not team:
                return self._send(400, "<h1>team 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            pre = "daily-brief-"
            pat = re.compile(r"daily-brief-\d{4}-\d{2}-\d{2}-" + re.escape(team) + r"$")
            files = sorted(f for f in BRIEF_DIR.glob(f"daily-brief-2*-{team}.html") if pat.fullmatch(f.stem))
            if not files:
                return self._send(404, f"<h1>{team} 팀 브리프가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            def _ds(f):  # stem에서 날짜부분(YYYY-MM-DD) 추출
                return f.stem[len(pre):-(len(team) + 1)]
            biz = []
            for f in files:
                ds = _ds(f)
                try:
                    if datetime.datetime.strptime(ds, "%Y-%m-%d").weekday() < 5:
                        biz.append(ds)
                except ValueError:
                    pass
            recent = biz[-4:]
            sel = (q.get("date") or [""])[0]
            target = BRIEF_DIR / f"daily-brief-{sel}-{team}.html"
            if not (sel and target.exists()):
                target = files[-1]
                sel = _ds(files[-1])
            wk = ["월", "화", "수", "목", "금", "토", "일"]
            btns = []
            for ds in recent:
                d = datetime.datetime.strptime(ds, "%Y-%m-%d")
                lab = f"{wk[d.weekday()]} {d.strftime('%m/%d')}"
                on = "background:var(--accent);color:#fff;border-color:var(--accent)" if ds == sel else "color:var(--muted)"
                btns.append(f'<a href="/team-brief?team={quote(team)}&date={ds}" style="text-decoration:none;border:1px solid var(--line);'
                            f'border-radius:7px;padding:5px 12px;font-size:12px;{on}">{lab}</a>')
            nav = ('<div style="display:flex;gap:6px;margin:0 0 18px;align-items:center">'
                   '<span style="color:var(--muted);font-size:11px;margin-right:4px">최근 영업일</span>'
                   + "".join(btns) + '</div>')
            html_str = target.read_text(encoding="utf-8").replace("</header>", "</header>" + nav, 1)
            return self._send(200, html_str.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/team-weekly":
            # 팀 주간 — 로그인은 셸이 처리(team_weekly_sess). team별 최신 파일.
            team = (q.get("team") or [""])[0]
            if not team:
                return self._send(400, "<h1>team 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            pat = re.compile(r"weekly-report-\d{4}-W\d{2}-" + re.escape(team) + r"$")
            files = sorted(f for f in WEEKLY_DIR.glob(f"weekly-report-2*-{team}.html") if pat.fullmatch(f.stem))
            if not files:
                return self._send(404, f"<h1>{team} 팀 주간이 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, files[-1].read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/guide":
            # 일일업무보고 가이드 — 직원 열람용(무인증, 공개).
            gp = _WS / "20-operations" / "23-arisa" / "guide" / "daily-report-guide.html"
            if not gp.exists():
                return self._send(404, "<h1>가이드가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, gp.read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/health":
            return self._send(200, {"ok": True})
        if path == "/api/projects":
            uid = (q.get("user") or [""])[0]
            if not load_users().get(uid): return self._send(401, {"ok": False, "error": "unknown user"})
            vis = [p for p in load_projects() if can_view(uid, p)]
            return self._send(200, {"ok": True, "projects": vis, "admin": is_admin(uid)})
        if path == "/api/project":
            uid = (q.get("user") or [""])[0]; pid = (q.get("id") or [""])[0]
            p = get_project(pid)
            if not p: return self._send(404, {"ok": False, "error": "not found"})
            if not can_view(uid, p): return self._send(403, {"ok": False, "error": "forbidden"})
            return self._send(200, {"ok": True, "project": p, "canEdit": can_edit(uid, p)})
        return self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/arisa2"):
            return self._proxy_arisa2("POST")
        b = self._body()
        if path == "/api/login":
            uid = b.get("id", ""); pin = b.get("pin", "")
            users = load_users()
            u = users.get(uid)
            if not u: return self._send(401, {"ok": False, "error": "등록되지 않은 이름입니다."})
            cur = str(u.get("pin") or "")
            pin_set = False
            if cur == "":
                # PIN 미설정 → 첫 로그인 시 본인이 설정
                if len(str(pin)) < 4:
                    return self._send(400, {"ok": False, "error": "첫 로그인입니다. PIN을 4자 이상으로 설정해주세요."})
                set_pin(uid, pin); pin_set = True
            elif cur != str(pin):
                return self._send(401, {"ok": False, "error": "ID 또는 PIN이 올바르지 않습니다."})
            return self._send(200, {"ok": True, "name": uid, "role": u.get("role", "직원"),
                                    "admin": is_admin(uid), "lead_teams": lead_teams_of(uid), "pin_set": pin_set})
        if path == "/api/set-pin":
            # PIN 변경(자가설정) — 현재 PIN 검증 후 새 PIN 저장
            uid = b.get("id", ""); cur = b.get("pin", ""); new = b.get("new_pin", "")
            if not auth(uid, cur): return self._send(401, {"ok": False, "error": "현재 PIN이 올바르지 않습니다."})
            if len(str(new)) < 4: return self._send(400, {"ok": False, "error": "새 PIN은 4자 이상이어야 합니다."})
            set_pin(uid, new)
            return self._send(200, {"ok": True})
        # 이하 쓰기: user+pin 검증
        uid = b.get("user", ""); pin = b.get("pin", "")
        if not auth(uid, pin): return self._send(401, {"ok": False, "error": "인증 실패"})
        if path == "/api/project/save":
            p = b.get("project") or {}
            if not p.get("id"): return self._send(400, {"ok": False, "error": "id 없음"})
            existing = get_project(p["id"])
            if existing and not can_edit(uid, existing):
                return self._send(403, {"ok": False, "error": "수정 권한 없음(담당 PM·대표만)"})
            if not existing and not is_admin(uid):
                return self._send(403, {"ok": False, "error": "생성은 대표만"})
            save_project(p)
            return self._send(200, {"ok": True})
        if path == "/api/project/delete":
            pid = b.get("id", "")
            if not is_admin(uid): return self._send(403, {"ok": False, "error": "삭제는 대표만"})
            f = PROJ_DIR / f"{_safe(pid)}.json"
            if f.exists(): f.unlink()
            return self._send(200, {"ok": True})
        return self._send(404, {"ok": False, "error": "not found"})

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1: PORT = int(sys.argv[1])
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer((HOST, PORT), H)
    print(f"▶ 대시보드 서버 http://{HOST}:{PORT}  (데이터: {DATA})")
    print(f"  프로젝트 {len(load_projects())}개 · 사용자 {len(load_users())}명")
    try: srv.serve_forever()
    except KeyboardInterrupt: srv.shutdown()
