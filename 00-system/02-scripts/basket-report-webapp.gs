/**
 * basket-report-webapp.gs — RX 매장 일일보고 웹앱 (백엔드)
 *
 * 흐름: 담당자 로그인(매장코드+PIN) → 오늘 진행로그(봇 /jot 누적) 표시
 *       → AI 자동 구성(OpenAI) → 12섹션 검토·수정 → 제출(일일보고 append + 매니저 알림)
 *
 * 프론트(index.html)는 google.script.run 으로 아래 함수를 호출(=CORS 없음).
 *
 * ── 배포 전 Script Properties 설정 (프로젝트 설정 → 스크립트 속성) ──
 *   SHEET_ID         18fx3jmb8x6NkiITRc4Y1fqpBJuftBmvC1_sV-8p5VkI
 *   OPENAI_API_KEY   sk-...
 *   BASKET_BOT_TOKEN 8803370629:AA...   (매니저 알림용)
 *   MANAGER_CHAT_ID  8123576679
 * 배포: 새 배포 → 웹 앱 → 실행=나 / 액세스=링크 가진 모든 사용자 → URL 공유
 */

var CONFIG = {};  // 배포 시 주입(저장소엔 비움). Script Properties가 우선, 없으면 CONFIG.
function P_(k){ return PropertiesService.getScriptProperties().getProperty(k) || CONFIG[k] || ''; }
function SS_(){ return SpreadsheetApp.openById(P_('SHEET_ID')); }
function today_(){ return Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyMMdd'); }

// 12섹션 (일일보고 시트 컬럼 매핑과 동일)
// 시트 저장 순서(일일보고 D열~). 절대 임의 변경 금지(시트·봇 정합).
var SECTION_KEYS = ['sales','jichul','approval','notes','equipment','worklog','rental','staff','purchase','tenant','reflection'];
var SECTION_LABELS = {
  sales:'💰 매출', jichul:'지출 총합', approval:'③ 송금·승인 급한 건', notes:'④ 특이사항', equipment:'⑤ 장비',
  worklog:'⑥ 업무 보고(완료/진행/예정)', rental:'⑦ 대관', staff:'⑧ 스태프',
  purchase:'⑨ 구매', tenant:'⑩ 입점 제안', reflection:'⑪ 복기(선택)'
};
// 폼 표시 순서(중요도) — 시트 순서와 별개
var DISPLAY_ORDER = ['sales','worklog','notes','approval','equipment','jichul','staff','purchase','rental','tenant','reflection'];
// 입력창 크기/타입
var SECTION_SIZE = { sales:'num', jichul:'num', purchase:'sm', reflection:'sm',
  approval:'md', staff:'md', rental:'md', tenant:'md', worklog:'lg', notes:'lg', equipment:'lg' };
var APPROVAL_KEYS = { approval:'③ 송금·승인', equipment:'⑤ 장비(견적·AS)', tenant:'⑩ 입점 제안' };

// ── 웹앱 진입점 ──
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('RX 매장 일일보고')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ── 로그인 (매장코드 + PIN) ──
function login(storeCode, pin) {
  var rows = SS_().getSheetByName('담당자').getDataRange().getValues();
  // header: store_id 매장명 매장코드 담당자명 PIN role
  for (var i = 1; i < rows.length; i++) {
    var r = rows[i];
    if (String(r[2]).trim().toLowerCase() === String(storeCode).trim().toLowerCase() && String(r[4]).trim() === String(pin).trim()) {
      return { ok: true, store_id: r[0], store_name: r[1], author: r[3], role: r[5] };
    }
  }
  return { ok: false, error: '매장코드 또는 PIN이 올바르지 않습니다.' };
}

// ── 오늘 진행로그 불러오기 ──
function getProgress(store_id, date) {
  date = date || today_();
  var rows = SS_().getSheetByName('진행로그').getDataRange().getValues();
  // header: store_id 날짜 시간 작성자 내용
  var out = [];
  for (var i = 1; i < rows.length; i++) {
    var r = rows[i];
    if (String(r[0]) === String(store_id) && String(r[1]) === String(date)) {
      out.push({ time: r[2], author: r[3], text: r[4] });
    }
  }
  return out;
}

// ── OpenAI 호출 헬퍼 ──
function openai_(sys, user, jsonMode) {
  var key = P_('OPENAI_API_KEY');
  if (!key) return null;
  var payload = { model:'gpt-4o-mini', temperature:0.3,
    messages:[{role:'system',content:sys},{role:'user',content:user}] };
  if (jsonMode) payload.response_format = { type:'json_object' };
  try {
    var res = UrlFetchApp.fetch('https://api.openai.com/v1/chat/completions', {
      method:'post', contentType:'application/json',
      headers:{ Authorization:'Bearer '+key }, payload:JSON.stringify(payload), muteHttpExceptions:true });
    return JSON.parse(res.getContentText()).choices[0].message.content;
  } catch(e){ return null; }
}
function emptySections_(){ var o={}; SECTION_KEYS.forEach(function(k){o[k]='';}); return o; }
function sectionsBody_(sec){ return SECTION_KEYS.map(function(k){ return sec[k]?(SECTION_LABELS[k]+': '+sec[k]):null; }).filter(String).join('\n'); }
function rowToSections_(r){ var o={}; SECTION_KEYS.forEach(function(k,i){ o[k]=r[3+i]||''; }); return o; }

// 관찰 해상도(resolution) 점검 — 공통 프롬프트. 보고가 누가·무엇·왜·수치·맥락·다음액션까지 구체적인지 본다.
var RESO_SYS = '너는 매장 운영 보고 코치다. 핵심 기준은 "관찰 해상도(resolution)" — 보고가 추상적("호평","바빴음","이슈있음","좋았음")에 머물지 않고, '
  + '누가/무엇을/왜/수치/맥락/다음 액션까지 구체적인지다. 특히 ④특이사항·⑥업무보고가 자주 저해상도다.\n'
  + '아래 일일보고를 검토해 JSON으로:\n'
  + '{"resolution": 1~5 정수(보고 전체 해상도, 5=매우 구체), "recos": ["..."]}\n'
  + 'recos = 해상도가 낮거나 중요 정보가 빠진 항목별 개선 권고(최대 5개). 각 권고는 "어느 항목 → 무엇이 모호/누락 → 이렇게 구체화(짧은 예시)" 형식. '
  + '예) ④특이사항: "신메뉴 호평"은 저해상도 → 누가·어떤 메뉴·어떤 반응을 (예: "20대 단골이 흑임자라떼 보고 사진 찍고 재구매") / '
  + '⑦대관: 일정만 있고 금액·인원 누락 → 금액·인원·회신기한 명시. '
  + '문제 없으면 recos 빈 배열. JSON만 출력.';

function reviewReport(sections) {
  var body = sectionsBody_(sections);
  if (!body) return { resolution: 0, recos: ['보고 내용이 비어 있습니다. 먼저 작성/구성하세요.'] };
  var raw = openai_(RESO_SYS, body, true);
  try { var o = JSON.parse(raw); return { resolution: o.resolution || 0, recos: (o.recos || []).slice(0,5) }; }
  catch(e){ return { resolution: 0, recos: [] }; }
}

// ── 진행로그 → 12섹션 + 해상도 점검(권고) ──
function compileReport(progressRows) {
  var joined = (progressRows || []).map(function(p){ return '['+(p.time||'')+' '+(p.author||'')+'] '+p.text; }).join('\n');
  if (!joined) return { sections: emptySections_(), review: { resolution:0, recos:[] } };
  var sys = '너는 Basket 매장 일일보고 정리 비서다. 아래 진행로그를 일일보고 12섹션 JSON으로 구조화하라. '
    + '로그에 있는 내용만(지어내지 않음), 없으면 빈 문자열, 원문 표현 보존.\n'
    + '스키마: {jichul,approval,notes,equipment,worklog,rental,staff,purchase,tenant,reflection}. JSON만 출력.';
  var raw = openai_(sys, joined, true);
  var out = emptySections_();
  if (raw) { try { var obj = JSON.parse(raw); SECTION_KEYS.forEach(function(k){ if (obj[k]) out[k]=String(obj[k]); }); } catch(e){} }
  return { sections: out, review: reviewReport(out) };
}

// ── 보고자 피드백 (사고의 거울) ──
function reflectOnReport(sections) {
  var body = sectionsBody_(sections);
  if (!body) return '';
  var sys = '너는 매장 운영 코치다. 아래 일일보고를 보고 작성자 본인에게 주는 피드백을 한국어 2~3문장으로. '
    + '① 잘 정리된 점 1개 ② 보완점 1개는 반드시 "관찰 해상도(구체성)" 관점에서 — 어떤 항목을 어떻게 더 구체적으로(누가·수치·맥락·다음액션) 적으면 좋은지 ③ 내일 챙길 것 1개. '
    + '따뜻하고 담백하게, 질책 금지.';
  return openai_(sys, body, false) || '';
}

// ── 지난 보고 검색 (날짜 또는 키워드) ──
function searchReports(store_id, query) {
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var q = String(query||'').trim(); var qd = q.replace(/[^0-9]/g,'');
  var out = [];
  for (var i = rows.length-1; i >= 1 && out.length < 12; i--) {
    var r = rows[i]; if (String(r[0]) !== String(store_id)) continue;
    var hay = r.slice(3,13).join(' ');
    var hit = !q || (qd && String(r[1]).indexOf(qd)>=0) || hay.indexOf(q) >= 0;
    if (hit) out.push({ date:r[1], author:r[2], summary: hay.replace(/\s+/g,' ').trim().slice(0,180), sections: rowToSections_(r) });
  }
  return out;
}

// ── 어제 보고 미결/이월 ──
function getYesterdayPending(store_id) {
  var y = new Date(); y.setDate(y.getDate()-1);
  var yk = Utilities.formatDate(y,'Asia/Seoul','yyMMdd');
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var found = null;
  for (var i = rows.length-1; i >= 1; i--) { if (String(rows[i][0])===String(store_id) && String(rows[i][1])===yk) { found = rows[i]; break; } }
  if (!found) return { found:false, date:yk };
  var sec = rowToSections_(found);
  var sys = '아래는 어제 일일보고다. 아직 끝나지 않은·회신대기·미처리·후속 필요 항목만 골라 한국어 짧은 리스트 "pending"(최대 6개)으로. 끝난 일은 제외. {"pending":[]} JSON만.';
  var raw = openai_(sys, sectionsBody_(sec), true); var pending=[];
  try{ pending = (JSON.parse(raw).pending||[]); }catch(e){}
  return { found:true, date:yk, sections:sec, pending:pending };
}

// ── 제출: 일일보고 append + 매니저 알림 ──
function substantive_(sec){ return SECTION_KEYS.some(function(k){ return String(sec[k]||'').trim() !== ''; }); }
function submitReport(store_id, sections, author) {
  if (!substantive_(sections)) return { ok:false, error:'보고 내용이 비어 있습니다. 매출 또는 업무 내용을 한 가지 이상 입력해 주세요.' };
  var now = new Date();
  var row = [ store_id, Utilities.formatDate(now,'Asia/Seoul','yyMMdd'), author ];
  SECTION_KEYS.forEach(function(k){ row.push(sections[k] || ''); });
  row.push(Utilities.formatDate(now,'Asia/Seoul','HH:mm'));
  SS_().getSheetByName('일일보고').appendRow(row);

  sendDailySummary_(store_id, author, sections);   // 대표 텔레그램 일일보고 요약
  var reflection = reflectOnReport(sections);
  return { ok: true, reflection: reflection };
}

function trunc_(s,n){ s=String(s||''); return s.length>n ? s.slice(0,n)+'…' : s; }

// 제출 완료 → 대표에게 일일보고 요약 푸시 (매출·결재필요·주요 업무/특이·어제 미결)
function sendDailySummary_(store_id, author, sections) {
  var tok = P_('BASKET_BOT_TOKEN'), chat = P_('MANAGER_CHAT_ID');
  if (!tok || !chat) return;
  var d = Utilities.formatDate(new Date(),'Asia/Seoul','yyMMdd');
  var L = ['🧺 *Basket 일일보고* '+d+' · '+author, ''];
  if (sections.sales && String(sections.sales).trim()) L.push('💰 매출 ' + sections.sales + (/[0-9]\s*$/.test(sections.sales) ? '원' : ''));
  var appr = [];
  Object.keys(APPROVAL_KEYS).forEach(function(k){ if (sections[k] && String(sections[k]).trim()) appr.push('• '+APPROVAL_KEYS[k]+': '+sections[k]); });
  if (appr.length) { L.push(''); L.push('🔔 *결재 필요*'); L = L.concat(appr); }
  if (sections.worklog && String(sections.worklog).trim()) { L.push(''); L.push('📌 *업무*\n'+trunc_(sections.worklog,240)); }
  if (sections.notes && String(sections.notes).trim()) { L.push('📍 *특이*\n'+trunc_(sections.notes,180)); }
  try {
    var y = getYesterdayPending(store_id);
    if (y.found && y.pending && y.pending.length) { L.push(''); L.push('🔁 *어제 미결*'); y.pending.forEach(function(p){ L.push('  ↪ '+p); }); }
  } catch(e){}
  try {
    UrlFetchApp.fetch('https://api.telegram.org/bot'+tok+'/sendMessage', {
      method:'post', muteHttpExceptions:true,
      payload:{ chat_id:chat, text:L.join('\n'), parse_mode:'Markdown' }
    });
  } catch(e){}
}

function SECTIONS_meta() { return { keys: SECTION_KEYS, labels: SECTION_LABELS, order: DISPLAY_ORDER, sizes: SECTION_SIZE }; }

// ── 주간업무 관리 (시트 '주간업무' = 엑셀 편집면 / 웹앱 = 직접 edit) ──
var WEEK_DAYS = ['월','화','수','목','금','토'];
function getWeeklyTasks(store_id) {
  var sh = SS_().getSheetByName('주간업무');
  var rows = sh ? sh.getDataRange().getValues() : [];
  var map = {}; WEEK_DAYS.forEach(function(d){ map[d] = { jeonggi:'', chaju:'' }; });
  for (var i=1;i<rows.length;i++){
    var r=rows[i]; if(String(r[0])!==String(store_id)) continue;
    var d=String(r[1]); if(map[d]){ map[d].jeonggi=r[2]||''; map[d].chaju=r[3]||''; }
  }
  return map;
}
// data = {월:{jeonggi,chaju}, ...}. admin·manager만 저장.
function saveWeeklyTasks(role, store_id, data) {
  if (role!=='admin' && role!=='manager') return { ok:false, error:'권한이 없습니다.' };
  var sh = SS_().getSheetByName('주간업무');
  var rows = sh.getDataRange().getValues();
  var rowIndex = {};  // 요일 → 시트 행번호(1-based)
  for (var i=1;i<rows.length;i++){ if(String(rows[i][0])===String(store_id)) rowIndex[String(rows[i][1])]=i+1; }
  WEEK_DAYS.forEach(function(d){
    var v = data[d] || { jeonggi:'', chaju:'' };
    var line = [store_id, d, v.jeonggi||'', v.chaju||''];
    if (rowIndex[d]) sh.getRange(rowIndex[d],1,1,4).setValues([line]);
    else sh.appendRow(line);
  });
  return { ok:true };
}
// 차주계획 → 정기로 승격(주 넘어갈 때) + 차주 비우기. (선택 기능)
function promoteChaju(role, store_id) {
  if (role!=='admin' && role!=='manager') return { ok:false };
  var wt = getWeeklyTasks(store_id), data={};
  WEEK_DAYS.forEach(function(d){
    var j=wt[d].jeonggi, c=wt[d].chaju;
    data[d] = { jeonggi: c ? (j? j+'\n'+c : c) : j, chaju:'' };
  });
  return saveWeeklyTasks(role, store_id, data);
}

// ── 관리자 대시보드: 매장별 써머리 ──
// role: admin → 전체 매장 / manager·staff → 본인 store_id. 카드 = 매출·지출·특이·대관·입점
function getStoreSummaries(role, store_id) {
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var dz = SS_().getSheetByName('담당자').getDataRange().getValues();
  var nameMap = {}; for (var j=1;j<dz.length;j++){ if(dz[j][0]) nameMap[dz[j][0]] = dz[j][1]; }
  var latest = {};  // store_id → 최신 행(마지막 등장)
  for (var i=1;i<rows.length;i++){ if(rows[i][0]) latest[rows[i][0]] = rows[i]; }
  var pick = (role === 'admin') ? Object.keys(latest) : [store_id];
  var out = [];
  pick.forEach(function(s){
    var r = latest[s];
    var sec = r ? rowToSections_(r) : emptySections_();
    var appr = 0; Object.keys(APPROVAL_KEYS).forEach(function(k){ if(sec[k] && String(sec[k]).trim()) appr++; });
    out.push({ store_id:s, store_name: nameMap[s]||s, has: !!r,
      date: r?r[1]:'', time: r?r[14]:'',
      sales: sec.sales, jichul: sec.jichul, notes: sec.notes, rental: sec.rental, tenant: sec.tenant,
      approvalCount: appr });
  });
  return out;
}

// 매장 주간 써머리(이번 주 월~오늘): 매출합계·보고일수·결재누적·특이 하이라이트
function getWeeklySummary(store_id) {
  var now = new Date();
  var day = now.getDay();                  // 0=일..6=토
  var mon = new Date(now); mon.setDate(now.getDate() - (day===0?6:day-1));
  var monK = Utilities.formatDate(mon,'Asia/Seoul','yyMMdd');
  var todayK = Utilities.formatDate(now,'Asia/Seoul','yyMMdd');
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var salesSum=0, days=0, appr=0, notes=[];
  for (var i=1;i<rows.length;i++){
    var r=rows[i]; if(String(r[0])!==String(store_id)) continue;
    var dk=String(r[1]); if(dk<monK || dk>todayK) continue;
    var sec=rowToSections_(r); days++;
    var n=parseInt(String(sec.sales||'').replace(/[^0-9]/g,''),10); if(!isNaN(n)) salesSum+=n;
    Object.keys(APPROVAL_KEYS).forEach(function(k){ if(sec[k]&&String(sec[k]).trim()) appr++; });
    if(sec.notes&&String(sec.notes).trim()) notes.push(dk+': '+trunc_(sec.notes,60));
  }
  return { weekStart:monK, days:days, salesSum:salesSum, approvalCount:appr, highlights: notes.slice(-5) };
}

// 매장 상세: 최신 일일보고 전체 섹션
function getStoreLatest(store_id) {
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var found = null;
  for (var i=rows.length-1;i>=1;i--){ if(String(rows[i][0])===String(store_id)){ found=rows[i]; break; } }
  if(!found) return { found:false };
  return { found:true, date:found[1], author:found[2], time:found[14], sections: rowToSections_(found) };
}

// ── Executive(경영) 대시보드: 최근 4주 매출 추이 + 매장 비교 (admin 전용) ──
function getExecutiveDashboard(role) {
  if (role !== 'admin') return { ok:false, error:'권한이 없습니다.' };
  function fmt(d){ return Utilities.formatDate(d,'Asia/Seoul','yyMMdd'); }
  var now = new Date(), day = now.getDay();
  var thisMon = new Date(now); thisMon.setDate(now.getDate() - (day===0?6:day-1)); thisMon.setHours(0,0,0,0);
  var todayK = fmt(now);
  var weeks = [];                              // 최근 4주(월~일) 버킷
  for (var w=3; w>=0; w--){
    var s = new Date(thisMon); s.setDate(thisMon.getDate()-7*w);
    var e = new Date(s); e.setDate(s.getDate()+6);
    weeks.push({ label:(s.getMonth()+1)+'/'+s.getDate(), startK:fmt(s), endK:fmt(e), salesSum:0, days:0 });
  }
  var dz = SS_().getSheetByName('담당자').getDataRange().getValues();
  var nameMap = {}; for (var j=1;j<dz.length;j++){ if(dz[j][0]) nameMap[dz[j][0]] = dz[j][1]; }
  var rows = SS_().getSheetByName('일일보고').getDataRange().getValues();
  var thisStartK = weeks[3].startK, store = {}, latest = {};
  for (var i=1;i<rows.length;i++){
    var r = rows[i], sid = r[0]; if(!sid) continue;
    var dk = String(r[1]), sec = rowToSections_(r);
    var won = parseInt(String(sec.sales||'').replace(/[^0-9]/g,''),10); if(isNaN(won)) won=0;
    for (var wi=0; wi<weeks.length; wi++){ if(dk>=weeks[wi].startK && dk<=weeks[wi].endK){ weeks[wi].salesSum+=won; weeks[wi].days++; break; } }
    latest[sid] = r;
    if (dk>=thisStartK && dk<=todayK){ if(!store[sid]) store[sid]={weekSales:0,reportDays:0}; store[sid].weekSales+=won; store[sid].reportDays++; }
  }
  var opDays = 0, probe = new Date(thisMon);   // 이번 주 영업일(월~오늘, 일 휴무)
  while (fmt(probe) <= todayK){ if(probe.getDay()!==0) opDays++; probe.setDate(probe.getDate()+1); }
  var ids = {}; for (var k in latest) ids[k]=1; for (var j2=1;j2<dz.length;j2++){ if(dz[j2][0]) ids[dz[j2][0]]=1; }
  var stores = [], totSales=0, totDays=0, totAppr=0;
  Object.keys(ids).forEach(function(sid){
    var st = store[sid] || { weekSales:0, reportDays:0 };
    var lr = latest[sid], lsec = lr ? rowToSections_(lr) : emptySections_();
    var appr = 0; Object.keys(APPROVAL_KEYS).forEach(function(kk){ if(lsec[kk]&&String(lsec[kk]).trim()) appr++; });
    stores.push({ store_id:sid, name:nameMap[sid]||sid, weekSales:st.weekSales, reportDays:st.reportDays,
      opDays:opDays, approvalOpen:appr, lastDate:lr?lr[1]:'', lastTime:lr?lr[14]:'', notes:trunc_(lsec.notes||'',60) });
    totSales+=st.weekSales; totDays+=st.reportDays; totAppr+=appr;
  });
  var totOp = opDays * (stores.length||1);
  return { ok:true, weeks:weeks, stores:stores,
    totals:{ weekSalesAll:totSales, storeCount:stores.length, approvalOpen:totAppr,
      reportRate: totOp? Math.round(totDays/totOp*100):0, opDays:opDays } };
}
