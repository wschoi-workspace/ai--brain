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
from urllib.error import URLError, HTTPError
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

# ── 주간분장 시트 연동 (개인 대시보드 — 업무분장 입력/조회) ──
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from shared import gws as _asgws
except Exception:
    _asgws = None
DAILY_SHEET = os.environ.get("DAILY_REPORT_SHEET_ID", "")
ASSIGN_TAB = "주간분장"


def _week_label(d=None):
    d = d or datetime.date.today()
    return f"W{d.isocalendar().week:02d}"


def _assign_read():
    """주간분장 탭 → dict 리스트. 탭 없거나 gws 실패 시 [] (안전 — 개인탭이 죽지 않게)."""
    if not (_asgws and DAILY_SHEET):
        return []
    try:
        rows = _asgws.values_get(DAILY_SHEET, f"{ASSIGN_TAB}!A2:J5000", retries=2, timeout=20)
    except Exception:
        return []
    out = []
    for r in rows:
        r = list(r) + [""] * (10 - len(r))
        # 시트 헤더: 날짜·프로젝트명·팀구분·담당자·업무내용·일정(완료예상)·결과물·상태·이해관계자·우선순위
        out.append({"date": (r[0] or "").strip(), "project": (r[1] or "").strip(),
                    "team": (r[2] or "").strip(), "assignee": (r[3] or "").strip(),
                    "task": (r[4] or "").strip(), "deadline": (r[5] or "").strip(),
                    "result": (r[6] or "").strip(), "status": (r[7] or "미착수").strip(),
                    "stakeholder": (r[8] or "").strip(), "priority": (r[9] or "일반").strip()})
    return out


def _assign_append(assignee, task, deadline, priority, by, project="", result="", stakeholder=""):
    """주간분장 append. 사용자 헤더 순서: 날짜·프로젝트명·팀·담당자·업무내용·일정·결과물·상태·이해관계자·우선순위."""
    if not (_asgws and DAILY_SHEET):
        return False, "시트 미설정"
    team = emp_team(assignee) or ""
    row = [datetime.date.today().isoformat(), project, team, assignee, task, deadline,
           result, "미착수", stakeholder, priority]
    try:
        ok = _asgws.append_to_sheet(DAILY_SHEET, f"{ASSIGN_TAB}!A1", row, timeout=20)
        return bool(ok), "" if ok else "주간분장 탭 없음/append 실패"
    except Exception as e:
        return False, str(e)[:80]


OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")


def _llm_todo(text):
    """자유 텍스트 업무지시 → 실행가능 to-do 항목 리스트. OpenAI(urllib, stdlib). 실패 시 []."""
    text = (text or "").strip()
    if not (OPENAI_KEY and text):
        return []
    _today = datetime.date.today().isoformat()
    sys_p = (f"오늘은 {_today}(YYYY-MM-DD)이다. 다음 업무 지시 텍스트를 담당자가 바로 실행할 수 있는 "
             "개별 to-do 항목으로 분해한다. 각 항목은 구체적 한 문장. 지시에 없는 내용을 지어내지 말 것. 항목 5~12개. "
             "**프로젝트 귀속 필수**: 항목이 특정 프로젝트에 속하면 project에 상위 프로젝트명을 넣는다. "
             "예) '봉은사 프로젝트 … (상세항목 _ BM 세부 리서치 및 아이데이션)' → 봉은사의 하위 상세항목이므로 "
             "그 항목의 project는 '봉은사'. 상위 프로젝트가 명시된 문장의 하위 항목들은 모두 같은 project를 상속한다. 불명확하면 빈칸. "
             "마감(deadline)은 텍스트에 명시적 날짜·요일이 있을 때만 오늘 기준 YYYY-MM-DD로 계산하고, 없거나 불명확하면 반드시 빈칸. "
             "임의 날짜 생성 절대 금지. priority는 '긴급' 근거 없으면 '일반'. "
             '반드시 JSON만 출력: {"items":[{"task":"...","project":"","deadline":"","priority":"일반"}]}')
    payload = json.dumps({"model": "gpt-4o-mini", "temperature": 0.2,
                          "response_format": {"type": "json_object"},
                          "messages": [{"role": "system", "content": sys_p},
                                       {"role": "user", "content": text[:4000]}]}).encode("utf-8")
    req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                  headers={"Authorization": "Bearer " + OPENAI_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        items = json.loads(d["choices"][0]["message"]["content"]).get("items", [])
    except Exception:
        return []
    out = []
    for it in items:
        t = (it.get("task") or "").strip()
        if t:
            out.append({"task": t, "project": (it.get("project") or "").strip(),
                        "deadline": (it.get("deadline") or "").strip(),
                        "priority": (it.get("priority") or "일반").strip()})
    return out

# / — 역할 인식 통합 셸: 로그인 1회 후 역할별 탭을 iframe으로 전환.
#   대표   = [프로젝트 | 오늘 Brief | 이번 주 | Decision Window] + 팀 스코프 드롭다운
#   리더   = [프로젝트 | 오늘 Brief(팀) | 이번 주(팀)] (2팀 리더는 드롭다운)
#   직원   = [프로젝트]
# iframe 격리라 CSS 충돌 없음. 통합 로그인이 pm_sess(포트폴리오)+brief_sess 등 세션키를 미리
# 세팅해 각 iframe(/projects·/brief·/weekly·/team-*·/arisa2/)이 게이트를 자동 통과.
UNIFIED_SHELL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Rent 대시보드</title>
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
#f-mywork{overflow:auto;padding:24px}
.mw-wrap{max-width:1000px;margin:0 auto}
.mw-h{font-size:15px;font-weight:600;margin:22px 0 12px}
.mw-form{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
.mw-form select,.mw-form input{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:13px;font-family:inherit}
.mw-form button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer}
.mw-assign{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:8px}
.mw-assign textarea{width:100%;min-height:76px;background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:11px 13px;font-size:13px;font-family:inherit;resize:vertical;line-height:1.5}
.td-actions{display:flex;gap:8px;margin-top:10px;align-items:center}
.td-actions button,.mw-assign button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.td-actions button:disabled{opacity:.5}
button.btn-sec{background:var(--bg-3);color:var(--fg);border:1px solid var(--line)}
.td-row{display:flex;gap:6px;align-items:center;margin-top:7px}
.td-row .td-proj{width:120px;flex-shrink:0;background:var(--bg-3);border:1px solid var(--accent);color:var(--fg);border-radius:8px;padding:9px 10px;font-size:12px;font-family:inherit}
.td-row .td-task{flex:1;min-width:140px;background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:13px;font-family:inherit}
.td-row select,.td-row input[type=date]{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 10px;font-size:12px;font-family:inherit}
.td-row .td-del{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;width:32px;height:34px;cursor:pointer;font-size:16px;flex-shrink:0}
.mw-card{background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:12px 15px;margin-bottom:7px}
.mw-card .t{font-size:14px;font-weight:500}
.mw-card .m{font-size:12px;color:var(--muted);margin-top:4px}
.mw-badge{font-size:11px;border-radius:5px;padding:1px 7px;margin-left:8px}
.mw-urgent{background:rgba(225,112,85,.16);color:var(--red)}
.mw-proj{border-left:2px solid var(--accent);padding-left:14px;margin-bottom:16px}
.mw-proj-name{font-size:14px;font-weight:600;margin-bottom:8px}
.mw-empty{color:var(--muted);font-size:13px;padding:8px 0}
#arisa2-status{font-size:11px;color:var(--muted);margin-left:6px}
#arisa2-status.ok{color:#00b894}
#arisa2-status.err{color:var(--red)}
</style></head>
<body>
<div id="login-gate"><div id="login-box">
  <h2>Project Rent 대시보드</h2>
  <div class="lg-sub">이름 + PIN (첫 로그인 시 PIN 설정)</div>
  <input id="lg-id" placeholder="이름" autocomplete="username">
  <input id="lg-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="lg-btn">로그인</button>
  <div id="login-err"></div>
</div></div>
<div id="shell">
  <div id="tabs">
    <button class="tab on" data-t="mywork">내 업무</button>
    <button class="tab" data-t="projects">프로젝트</button>
    <button class="tab" data-t="brief" style="display:none">오늘 Brief</button>
    <button class="tab" data-t="weekly" style="display:none">이번 주</button>
    <select id="scope-sel" style="display:none"></select>
    <span class="who" id="who"></span>
  </div>
  <div class="frame on" id="f-mywork"></div>
  <iframe class="frame" id="f-projects"></iframe>
  <iframe class="frame" id="f-brief"></iframe>
  <iframe class="frame" id="f-weekly"></iframe>
</div>
<script>
(function(){
  var gate=document.getElementById('login-gate'), shell=document.getElementById('shell'), who=document.getElementById('who');
  var sel=document.getElementById('scope-sel');
  var frames={mywork:document.getElementById('f-mywork'),projects:document.getElementById('f-projects'),
              brief:document.getElementById('f-brief'),weekly:document.getElementById('f-weekly')};
  var SESS=null, curTab='mywork', curScope='', loaded={projects:false,brief:false,weekly:false};
  var MW_ASSIGNEES=[];
  var SESS_KEYS=['pm_sess','brief_sess','weekly_sess','team_brief_sess','team_weekly_sess'];
  var CLEAR_KEYS=SESS_KEYS.concat(['arisa_sess','arisa_token']);
  function tabBtn(t){ return document.querySelector('.tab[data-t="'+t+'"]'); }
  function srcFor(t){
    if(t==='projects') return '/projects';
    if(t==='decision') return '/arisa2/';
    if(SESS.admin && curScope===''){ return t==='brief' ? '/brief' : '/weekly'; }
    return (t==='brief' ? '/team-brief?team=' : '/team-weekly?team=') + encodeURIComponent(curScope);
  }
  function showTab(t){
    curTab=t;
    document.querySelectorAll('.tab').forEach(function(b){ b.classList.toggle('on', b.dataset.t===t); });
    Object.keys(frames).forEach(function(k){ frames[k].classList.toggle('on', k===t); });
    if(t==='mywork'){ renderMyWork(); return; }  // div 직접 렌더(iframe 아님) — 매번 최신
    if(!loaded[t]){ frames[t].src=srcFor(t); loaded[t]=true; }
  }
  function loadScope(scope){
    curScope=scope; loaded.brief=false; loaded.weekly=false;
    frames.brief.src='about:blank'; frames.weekly.src='about:blank';
    if(curTab==='brief'||curTab==='weekly'){ frames[curTab].src=srcFor(curTab); loaded[curTab]=true; }
  }
  function arisa2Login(s){
    // PIN 단일화(users.json symlink)로 같은 자격 재사용 → ARISA 2.0 토큰 발급. Promise<bool> 반환(showTab이 await).
    return fetch('/arisa2/api/login?name='+encodeURIComponent(s.name)+'&pin='+encodeURIComponent(s.pin||''),{method:'POST'})
      .then(function(r){ if(!r.ok) throw new Error('login '+r.status); return r.json(); })
      .then(function(d){
        if(!(d && d.ok)) throw new Error('bad response');
        localStorage.setItem('arisa_sess',JSON.stringify(d.user));
        localStorage.setItem('arisa_token',d.token);
        if(loaded.decision){ frames.decision.src=srcFor('decision'); } // 이미 열려 있었으면 재로드
        return true;
      }).catch(function(e){ console.warn('[arisa2Login]', e && e.message); return false; });
  }
  function checkArisa2(){
    fetch('/arisa2/api/health',{method:'GET'}).then(function(r){
      var ok=r.status<500; // 401 등 4xx = 서버 살아있음(인증 게이트)
      a2s.textContent=ok?'ARISA 2.0 ON':'ARISA 2.0 OFF';
      a2s.className=ok?'ok':'err';
    }).catch(function(){ a2s.textContent='ARISA 2.0 OFF'; a2s.className='err'; });
  }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function renderMyWork(){
    var box=frames.mywork;
    box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오는 중…</div></div>';
    var u=encodeURIComponent(SESS.name);
    Promise.all([
      fetch('/api/my-work?user='+u).then(function(r){return r.json();}),
      fetch('/api/assignees?user='+u).then(function(r){return r.json();})
    ]).then(function(res){
      var mw=res[0]||{}, ac=res[1]||{}, h='<div class="mw-wrap">';
      MW_ASSIGNEES = ac.assignees || [];
      if(ac.canAssign){
        var _lv=ac.level||'담당자';
        h+='<div class="mw-h">업무 분장 <span class="sub2">— 자유롭게 적으면 AI가 항목화 → 편집 후 '+_lv+'에게 배분 → 승인'+(_lv==='팀원'?' (대표가 배분한 내 업무를 참고해도 됩니다)':'')+'</span></div>';
        h+='<div class="mw-assign"><textarea id="mw-text" placeholder="이번주 팀 업무를 자유롭게 적으세요.&#10;예) 봉은사 마스터플랜 검토·정리본 공유, 세스크멘슬 주방도면 정리, KBO 굿즈 발주 최종확인"></textarea>'
          +'<div class="td-actions"><button id="mw-parse">AI로 항목 정리</button></div>'
          +'<div id="mw-todos"></div><div id="mw-msg" class="sub2"></div></div>';
      }
      h+='<div class="mw-h">오늘 할일 · 내 분장</div>';
      var A=mw.assignments||[];
      if(A.length){ A.forEach(function(a){
        var urg=(a.priority==='긴급')?'<span class="mw-badge mw-urgent">긴급</span>':'';
        var dl=a.deadline?(' · 마감 '+esc(a.deadline)):'';
        var pj=a.project?(' · '+esc(a.project)):'';
        h+='<div class="mw-card"><div class="t">'+esc(a.task)+urg+'</div><div class="m">'+esc(a.status)+dl+pj+'</div></div>';
      }); } else { h+='<div class="mw-empty">배정된 분장이 없습니다.</div>'; }
      h+='<div class="mw-h">내 프로젝트 일정</div>';
      var P=mw.projects||[];
      if(P.length){ P.forEach(function(p){
        h+='<div class="mw-proj"><div class="mw-proj-name">'+esc(p.name)+(p.dday?(' <span style="color:var(--muted);font-weight:400;font-size:12px">D-day '+esc(p.dday)+'</span>'):'')+'</div>';
        (p.tasks||[]).forEach(function(t){
          var per=(t.start||'')+(t.end?('~'+t.end):'');
          h+='<div class="mw-card"><div class="t">'+esc(t.task||'')+'</div><div class="m">'+esc(t.status||'')+' · '+esc(t.division||'')+(per?(' · '+esc(per)):'')+'</div></div>';
        });
        h+='</div>';
      }); } else { h+='<div class="mw-empty">배정된 프로젝트 업무가 없습니다.</div>'; }
      h+='</div>'; box.innerHTML=h;
      var pb=document.getElementById('mw-parse');
      if(pb){ pb.onclick=function(){
        var txt=document.getElementById('mw-text').value.trim(), msg=document.getElementById('mw-msg');
        if(!txt){ msg.textContent='업무 내용을 입력하세요'; return; }
        msg.textContent='AI가 항목으로 정리 중…'; pb.disabled=true;
        fetch('/api/assign-parse',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({user:SESS.name,pin:SESS.pin,text:txt})})
          .then(function(r){return r.json();}).then(function(d){
            pb.disabled=false;
            if(d.ok && d.items && d.items.length){ msg.textContent='검토 후 각 항목에 담당자를 지정하고 승인하세요.'; mwRenderTodos(d.items); }
            else { msg.textContent='항목을 뽑지 못했습니다. 더 구체적으로 적어보세요.'; }
          }).catch(function(){ pb.disabled=false; msg.textContent='서버 오류'; });
      };}
    }).catch(function(){ box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오기 실패</div></div>'; });
  }
  function mwAsOpts(sel){ return MW_ASSIGNEES.map(function(a){return '<option value="'+esc(a.name)+'"'+(a.name===sel?' selected':'')+'>'+esc(a.name)+' ('+esc(a.team||'')+')</option>';}).join(''); }
  function mwTodoRow(it){
    it=it||{};
    return '<div class="td-row"><input class="td-proj" value="'+esc(it.project||'')+'" placeholder="프로젝트" title="상위 프로젝트">'
      +'<input class="td-task" value="'+esc(it.task||'')+'" placeholder="업무 내용">'
      +'<select class="td-as"><option value="">담당자</option>'+mwAsOpts('')+'</select>'
      +'<input class="td-dl" type="date" value="'+esc(it.deadline||'')+'" title="마감">'
      +'<select class="td-pr"><option'+(it.priority==='긴급'?'':' selected')+'>일반</option><option'+(it.priority==='긴급'?' selected':'')+'>긴급</option></select>'
      +'<button class="td-del" title="삭제">×</button></div>';
  }
  function mwBindRow(row){ row.querySelector('.td-del').onclick=function(){ row.remove(); }; }
  function mwRenderTodos(items){
    var box=document.getElementById('mw-todos');
    box.innerHTML=items.map(mwTodoRow).join('')
      +'<div class="td-actions"><button id="mw-add" class="btn-sec">+ 항목 추가</button>'
      +'<button id="mw-commit">최종 승인 · 등록</button></div>';
    box.querySelectorAll('.td-row').forEach(mwBindRow);
    document.getElementById('mw-add').onclick=function(){
      var d=document.createElement('div'); d.innerHTML=mwTodoRow({}); var row=d.firstChild;
      mwBindRow(row); box.insertBefore(row, box.querySelector('.td-actions'));
    };
    document.getElementById('mw-commit').onclick=mwCommit;
  }
  function mwCommit(){
    var items=[], msg=document.getElementById('mw-msg');
    document.querySelectorAll('#mw-todos .td-row').forEach(function(r){
      var task=r.querySelector('.td-task').value.trim();
      if(task) items.push({assignee:r.querySelector('.td-as').value, task:task,
        project:r.querySelector('.td-proj').value.trim(),
        deadline:r.querySelector('.td-dl').value, priority:r.querySelector('.td-pr').value});
    });
    if(!items.length){ msg.textContent='등록할 항목이 없습니다'; return; }
    if(items.some(function(i){return !i.assignee;})){ msg.textContent='모든 항목에 담당자를 지정하세요'; return; }
    msg.textContent='등록 중…';
    fetch('/api/assign-commit',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user:SESS.name,pin:SESS.pin,items:items})})
      .then(function(r){return r.json();}).then(function(d){
        if(d.added){ renderMyWork(); } else { msg.textContent=(d.errors&&d.errors.join(', '))||'등록 실패(주간분장 탭 확인)'; }
      }).catch(function(){ msg.textContent='서버 오류'; });
  }
  function changePin(){
    var cur=prompt('현재 PIN을 입력하세요'); if(!cur) return;
    var nw=prompt('새 PIN (4자 이상)'); if(!nw) return;
    fetch('/api/set-pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:SESS.name,pin:cur,new_pin:nw})})
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){ SESS.pin=nw; var j=JSON.stringify(SESS); SESS_KEYS.forEach(function(k){localStorage.setItem(k,j);}); alert('PIN이 변경되었습니다'); }
        else alert(d.error||'변경 실패');
      });
  }
  function enter(s){
    SESS=s; var j=JSON.stringify(s);
    SESS_KEYS.forEach(function(k){ localStorage.setItem(k,j); });
    gate.style.display='none'; shell.style.display='flex';
    who.innerHTML = s.name+' ('+(s.role||'')+') <a id="lg-pin-c">PIN변경</a> <a id="lg-out">로그아웃</a>';
    document.getElementById('lg-out').onclick=function(){ CLEAR_KEYS.forEach(function(k){localStorage.removeItem(k);}); location.reload(); };
    document.getElementById('lg-pin-c').onclick=changePin;
    var lt=s.lead_teams||[];
    if(s.admin){
      tabBtn('brief').style.display=''; tabBtn('weekly').style.display='';
      // Decision Window(ARISA 2.0)는 데이터 취합 백단 창구 — 대시보드 전면 노출 안 함(탭 숨김)
      sel.style.display='inline-block'; sel.innerHTML='<option value="">전체</option>';
      lt.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
      sel.onchange=function(){ loadScope(sel.value); };
      curScope='';
    } else if(lt.length){
      tabBtn('brief').style.display=''; tabBtn('weekly').style.display='';
      curScope=lt[0];
      if(lt.length>1){
        sel.style.display='inline-block'; sel.innerHTML='';
        lt.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
        sel.onchange=function(){ loadScope(sel.value); };
      } else { sel.style.display='none'; }
    } else { sel.style.display='none'; }
    showTab('mywork');
  }
  document.querySelectorAll('.tab').forEach(function(b){ b.onclick=function(){ showTab(b.dataset.t); }; });
  var sess=null; try{ sess=JSON.parse(localStorage.getItem('pm_sess')||'null'); }catch(e){}
  if(sess && sess.name) enter(sess);
  function doLogin(){
    var id=document.getElementById('lg-id').value.trim(), pin=document.getElementById('lg-pin').value.trim();
    var err=document.getElementById('login-err'); err.textContent='';
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,pin:pin})})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.ok){ var s=Object.assign({},d,{id:id,pin:pin}); enter(s); if(d.pin_set) alert('PIN이 설정되었습니다'); }
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
    """users.json 로드 — dict 스키마(대시보드)와 list 스키마(ARISA 2.0, symlink 단일화)를 모두 지원."""
    try:
        u = json.loads((DATA/"users.json").read_text(encoding="utf-8")).get("users", {})
    except Exception:
        return {}
    if isinstance(u, list):  # ARISA 2.0 스키마: [{name, role(admin/leader/member), team, pin}]
        return {x["name"]: {"pin": x.get("pin", ""),
                            "role": "대표" if x.get("role") == "admin" else (x.get("role") or "직원")}
                for x in u if x.get("name")}
    return u

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
    """users.json에 PIN 저장(첫 설정/변경) — dict/list 스키마 모두 지원. 성공 True."""
    p = DATA / "users.json"
    with _lock:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False
        users = doc.get("users")
        if isinstance(users, list):  # ARISA 2.0 스키마
            for x in users:
                if x.get("name") == uid:
                    x["pin"] = str(new_pin)
                    break
            else:
                return False
        else:
            if uid not in (users or {}):
                return False
            users[uid]["pin"] = str(new_pin)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return True

def emp_team(name):
    """직원의 소속 팀(arisa-employees.json by_name[…].team)."""
    return (load_emp().get("by_name", {}).get(name, {}) or {}).get("team")

def is_leader(uid):
    """팀 리더 여부(대표 제외한 순수 리더도 True, 대표도 True)."""
    return bool(lead_teams_of(uid))

def project_teams(p):
    """프로젝트에 걸린 팀 집합 = PM + 멤버들의 소속 팀."""
    people = list(p.get("members") or [])
    if p.get("pm"): people.append(p["pm"])
    return {t for t in (emp_team(x) for x in people) if t}

def can_manage(uid, p):
    """멤버 배정 권한: 대표 / 담당 PM / (본인 리더팀이 이 프로젝트에 걸린) 팀 리더."""
    if is_admin(uid) or uid == p.get("pm"):
        return True
    return bool(set(lead_teams_of(uid)) & project_teams(p))

def can_view(uid, p):
    # 리더는 '본인 팀이 걸린' 프로젝트를 멤버가 아니어도 열람(멤버 배정 위해)
    return is_admin(uid) or uid == p.get("pm") or uid in (p.get("members") or []) or can_manage(uid, p)

def can_edit(uid, p):
    # 내용(업무·이슈·브리프) 편집은 기존대로 담당 PM·대표만 — 리더는 멤버 배정만
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
        for h in ("Content-Type", "Authorization"):  # Bearer 토큰 전달(ARISA 2.0 인증)
            v = self.headers.get(h)
            if v:
                headers[h] = v
        try:
            req = Request(url, data=body, headers=headers, method=method)
            with urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                ctype = resp.headers.get("Content-Type", "application/octet-stream")
                if "text/html" in ctype:
                    # SPA의 API 베이스를 프록시 프리픽스로 재작성 → /arisa2/api/* 로 호출
                    resp_body = resp_body.replace(b"var API='';", b"var API='/arisa2';")
                self.send_response(resp.status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(resp_body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(resp_body)
        except HTTPError as e:
            # upstream이 4xx/5xx를 반환해도 상태·본문 그대로 전달(401 인증게이트 = 서버 살아있음)
            resp_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json; charset=utf-8"))
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
            # 통합 셸 — 로그인 1회, 역할별 탭(프로젝트/Brief/Weekly/Decision)
            return self._send(200, UNIFIED_SHELL.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/projects":
            # 포트폴리오 HTML (구 / 핸들러) — 셸 iframe 또는 직접 접속(자체 로그인)
            try:
                html = HTML.read_text(encoding="utf-8")
            except Exception:
                return self._send(500, "<h1>대시보드 파일이 없습니다. generate-portfolio.py 실행 필요</h1>".encode("utf-8"), "text/html; charset=utf-8")
            inject = "<script>window.SERVED=true;window.API_BASE='/api';</script>\n</head>"
            html = html.replace("</head>", inject, 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path in ("/dashboard", "/team"):
            # 구 대표/리더 셸 → 통합 셸로 (기존 알림 링크 호환)
            self.send_response(301)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
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
            recent = biz[-7:]  # 오늘 + 직전 6영업일 (최근 일주일 이력)
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
            recent = biz[-7:]  # 최근 일주일 이력 (팀)
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
        if path == "/api/assignees":
            # 계층적 분장 후보 — 대표=리더급에게만, 리더=자기 팀원에게만
            uid = (q.get("user") or [""])[0]
            emp = load_emp().get("by_name", {})
            tl = load_emp().get("team_leads", {})
            if is_admin(uid):
                lead_team = {}
                for team, ldr in tl.items():
                    lead_team.setdefault(ldr, []).append(team)
                data = [{"name": n, "team": "·".join(lead_team[n])} for n in sorted(lead_team.keys())]
                if uid not in lead_team:  # 대표 본인도 담당자 후보(직접 챙기는 업무)
                    data.insert(0, {"name": uid, "team": emp_team(uid) or "경영"})
                level = "리더"
            else:
                my = set(lead_teams_of(uid))
                data = [{"name": n, "team": (v or {}).get("team", "")} for n, v in sorted(emp.items())
                        if (v or {}).get("team") in my]
                level = "팀원"
            return self._send(200, {"ok": True, "canAssign": is_admin(uid) or is_leader(uid),
                                    "level": level, "assignees": data})
        if path == "/api/my-work":
            # 개인 대시보드 — 내 분장(미완) + 내 프로젝트 일정(owner)
            uid = (q.get("user") or [""])[0]
            mine = [a for a in _assign_read() if a["assignee"] == uid and a["status"] != "완료"]
            mine.sort(key=lambda a: (a["status"] != "진행중", a.get("deadline") or "9999"))
            projs = []
            for p in load_projects():
                ts = [t for t in (p.get("tasks") or []) if t.get("owner") == uid and (t.get("status") or "") != "완료"]
                if ts:
                    projs.append({"id": p.get("id"), "name": p.get("name"), "dday": p.get("dday"),
                                  "tasks": [{"task": t.get("task"), "start": t.get("start"), "end": t.get("end"),
                                             "status": t.get("status"), "priority": t.get("priority"),
                                             "division": t.get("division")} for t in ts]})
            return self._send(200, {"ok": True, "user": uid, "assignments": mine, "projects": projs})
        if path == "/api/projects":
            uid = (q.get("user") or [""])[0]
            if not load_users().get(uid): return self._send(401, {"ok": False, "error": "unknown user"})
            vis = []
            for p in load_projects():
                if can_view(uid, p):
                    q = dict(p); q["canManage"] = can_manage(uid, p); q["canEdit"] = can_edit(uid, p)
                    vis.append(q)
            return self._send(200, {"ok": True, "projects": vis, "admin": is_admin(uid),
                                    "canCreate": is_admin(uid) or is_leader(uid)})
        if path == "/api/project":
            uid = (q.get("user") or [""])[0]; pid = (q.get("id") or [""])[0]
            p = get_project(pid)
            if not p: return self._send(404, {"ok": False, "error": "not found"})
            if not can_view(uid, p): return self._send(403, {"ok": False, "error": "forbidden"})
            return self._send(200, {"ok": True, "project": p, "canEdit": can_edit(uid, p), "canManage": can_manage(uid, p)})
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
        if path == "/api/assign-parse":
            # 자유 텍스트 → AI to-do 항목화 (담당자 미지정 — 리더가 이후 지정)
            if not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "분장 권한 없음"})
            items = _llm_todo(b.get("text") or "")
            return self._send(200, {"ok": True, "items": items})
        if path == "/api/assign-commit":
            # 편집·담당자 지정 완료된 항목 일괄 등록
            items = b.get("items") or []
            added, errs = 0, []
            for it in items:
                assignee = (it.get("assignee") or "").strip()
                task = (it.get("task") or "").strip()
                if not (assignee and task):
                    errs.append(f"'{task[:16] or '항목'}': 담당자·업무 누락"); continue
                if is_admin(uid):
                    if assignee not in (set(load_emp().get("team_leads", {}).values()) | {uid}):
                        errs.append(f"{assignee}: 대표는 리더·본인에게만 배분"); continue
                elif emp_team(assignee) not in set(lead_teams_of(uid)):
                    errs.append(f"{assignee}: 자기 팀원만 분장 가능"); continue
                ok, msg = _assign_append(assignee, task, (it.get("deadline") or "").strip(),
                                         (it.get("priority") or "일반").strip(), uid,
                                         project=(it.get("project") or "").strip())
                if ok: added += 1
                else: errs.append(msg or "append 실패")
            return self._send(200, {"ok": added > 0, "added": added, "errors": errs})
        if path == "/api/assign":
            # (단건 — 하위호환) 업무분장 입력. 대표=전 직원, 리더=자기 팀원에게만
            assignee = (b.get("assignee") or "").strip()
            task = (b.get("task") or "").strip()
            if not (assignee and task): return self._send(400, {"ok": False, "error": "담당자·업무 필수"})
            if is_admin(uid):
                if assignee not in (set(load_emp().get("team_leads", {}).values()) | {uid}):
                    return self._send(403, {"ok": False, "error": "대표는 리더·본인에게만 배분할 수 있습니다"})
            elif emp_team(assignee) not in set(lead_teams_of(uid)):
                return self._send(403, {"ok": False, "error": "자기 팀원에게만 분장할 수 있습니다"})
            ok, msg = _assign_append(assignee, task, (b.get("deadline") or "").strip(),
                                     (b.get("priority") or "일반").strip(), uid)
            return self._send(200 if ok else 500, {"ok": ok, "error": msg})
        if path == "/api/project/save":
            p = b.get("project") or {}
            if not p.get("id"): return self._send(400, {"ok": False, "error": "id 없음"})
            existing = get_project(p["id"])
            if existing and not can_edit(uid, existing):
                return self._send(403, {"ok": False, "error": "수정 권한 없음(담당 PM·대표만)"})
            if not existing and not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "생성은 대표·팀 리더만"})
            save_project(p)
            return self._send(200, {"ok": True})
        if path == "/api/project/members":
            # 멤버(열람 직원) 배정 전용 — 내용은 안 건드림. 대표·PM·해당 팀 리더만.
            pid = b.get("id", ""); members = b.get("members")
            p = get_project(pid)
            if not p: return self._send(404, {"ok": False, "error": "not found"})
            if not can_manage(uid, p):
                return self._send(403, {"ok": False, "error": "멤버 배정 권한 없음(대표·PM·해당 팀 리더만)"})
            if not isinstance(members, list):
                return self._send(400, {"ok": False, "error": "members 배열이 필요합니다"})
            known = set(load_users().keys())
            clean = [m for m in members if m in known]
            if p.get("pm") and p["pm"] not in clean: clean.append(p["pm"])  # PM은 항상 유지
            p["members"] = clean
            save_project(p)
            return self._send(200, {"ok": True, "members": clean})
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
