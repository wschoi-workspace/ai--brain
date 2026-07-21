/**
 * PROJECT RENT 홈페이지 문의 → 구글시트 취합 웹훅
 *
 * 배포 방법 (3분):
 * 1. script.google.com → 새 프로젝트
 * 2. 이 코드 전체 붙여넣기 → 저장 (프로젝트명: rent-inquiry-sheet)
 * 3. 우상단 [배포] → 새 배포 → 유형: 웹 앱
 *    - 실행 계정: 나 (ws.choi@project-rent.com)
 *    - 액세스 권한: 누구나
 * 4. [배포] 클릭 → 권한 승인 → 웹 앱 URL 복사해서 알려주기
 */

const SHEET_ID = '1zdGWTmBmMCYKOvmU7IqPgttgUcZwYpf-oGm-wgjuzHM'; // PROJECT RENT 홈페이지 문의 취합
const SHEET_TAB = '문의내역';
const SECRET = 'f432cd5cc4a6b36d8abf98b6fed2b892'; // Cloudflare Function과 공유

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    if (data.secret !== SECRET) {
      return jsonResponse({ ok: false, error: 'unauthorized' });
    }

    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_TAB);
    sheet.appendRow([
      data.ts || new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }),
      data.type || '-',
      data.name || '-',
      data.company || '-',
      data.email || '-',
      data.phone || '-',
      data.message || '-',
    ]);

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: err.message });
  }
}

function doGet() {
  return jsonResponse({ ok: true, message: 'rent-inquiry-sheet webhook 작동 중' });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
