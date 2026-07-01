/**
 * sns-webhook.gs — SNS 카드뉴스 자동화의 B 모듈 (웹훅 → Google Drive).
 *
 * ChatGPT 커스텀GPT의 Action이 대화 종료 시 이 웹앱으로 카드뉴스 구조화 JSON을 POST한다.
 * 웹앱은 공유시크릿을 검증한 뒤 지정 Drive 폴더(SNS_Automation/input)에 .json 파일로 저장한다.
 * Claude Code의 /sns-cardnews 스킬이 이 폴더에서 최신 파일을 읽어 처리한다.
 *
 * 배포 방법:
 *   1) script.google.com 에서 새 프로젝트 생성 → 이 코드 붙여넣기
 *   2) 프로젝트 설정 → 스크립트 속성(Script Properties)에 아래 2개 추가
 *        INPUT_FOLDER_ID  = SNS_Automation/input 폴더 ID
 *        WEBHOOK_SECRET   = 커스텀GPT와 공유할 비밀 문자열 (.env의 SNS_WEBHOOK_SECRET와 동일)
 *   3) 배포 → 새 배포 → 유형: 웹 앱
 *        실행 주체: 나
 *        액세스 권한: 모든 사용자(Anyone)   ← 시크릿으로 보호하므로 안전
 *   4) 배포 URL(/exec)을 커스텀GPT Action의 server url로 사용
 *
 * 테스트(터미널):
 *   curl -X POST "<배포URL>" -H "Content-Type: application/json" \
 *     -H "X-Webhook-Secret: <SECRET>" --data @sample.json
 */

function doPost(e) {
  try {
    var props = PropertiesService.getScriptProperties();
    var INPUT_FOLDER_ID = props.getProperty('INPUT_FOLDER_ID');
    var WEBHOOK_SECRET = props.getProperty('WEBHOOK_SECRET');

    // --- 공유시크릿 검증 (헤더 우선, 없으면 body.secret / 쿼리 fallback) ---
    var provided = '';
    if (e && e.parameter && e.parameter.secret) provided = e.parameter.secret;
    var bodyText = (e && e.postData && e.postData.contents) ? e.postData.contents : '';
    var payload = {};
    if (bodyText) {
      try { payload = JSON.parse(bodyText); } catch (err) {
        return _json({ ok: false, error: 'invalid_json' }, 400);
      }
    }
    if (!provided && payload && payload.secret) provided = payload.secret;

    if (!WEBHOOK_SECRET || provided !== WEBHOOK_SECRET) {
      return _json({ ok: false, error: 'unauthorized' }, 401);
    }

    // body에 secret이 섞여 있으면 저장 전에 제거
    if (payload && payload.secret) delete payload.secret;

    if (!payload || !payload.topic) {
      return _json({ ok: false, error: 'missing_topic' }, 400);
    }

    // --- 파일명: YYYYMMDD-HHMMSS-{slug}.json ---
    var ts = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyyMMdd-HHmmss');
    var slug = _slugify(payload.topic);
    var name = ts + '-' + slug + '.json';

    var folder = DriveApp.getFolderById(INPUT_FOLDER_ID);
    var content = JSON.stringify(payload, null, 2);
    var file = folder.createFile(name, content, 'application/json');

    return _json({ ok: true, fileId: file.getId(), name: name }, 200);
  } catch (err) {
    return _json({ ok: false, error: String(err) }, 500);
  }
}

/** 헬스체크용 GET */
function doGet(e) {
  return _json({ ok: true, service: 'sns-webhook', ts: new Date().toISOString() }, 200);
}

function _slugify(s) {
  if (!s) return 'untitled';
  var slug = String(s)
    .replace(/[\s\/\\]+/g, '-')          // 공백/슬래시 → -
    .replace(/[^0-9A-Za-z가-힣\-]/g, '') // 안전 문자만
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  return (slug || 'untitled').slice(0, 40);
}

/** ContentService JSON 응답 (Apps Script 웹앱은 상태코드를 직접 제어 못 하므로 body의 ok 필드로 판단) */
function _json(obj, _status) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
