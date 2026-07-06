/**
 * 봉은문화센터 미래 방향 설문 — 응답 수집 엔드포인트
 * 구글시트 > 확장 프로그램 > Apps Script 에 이 코드를 붙여넣고,
 * [배포 > 새 배포 > 웹 앱] (액세스: 모든 사용자)으로 배포한 뒤,
 * 발급된 URL을 index.html 의 APPS_SCRIPT_URL 에 입력하세요.
 *
 * 연결 시트: "봉은문화회관 활용방향 설문 응답"
 *   - '응답' 탭: timestamp + Q1~Q22 + 자유의견 (헤더 24열 사전 세팅됨)
 */

function doPost(e) {
  try {
    var lock = LockService.getScriptLock();
    lock.tryLock(10000);

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sh = ss.getSheetByName('응답');
    if (!sh) sh = ss.insertSheet('응답');

    var data = JSON.parse(e.postData.contents);

    var headers;
    if (sh.getLastRow() === 0) {
      headers = Object.keys(data);
      sh.appendRow(headers);
      sh.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#F2F0FB');
      sh.setFrozenRows(1);
    } else {
      headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
      Object.keys(data).forEach(function (k) {
        if (headers.indexOf(k) < 0) {
          headers.push(k);
          sh.getRange(1, headers.length).setValue(k).setFontWeight('bold').setBackground('#F2F0FB');
        }
      });
    }

    var row = headers.map(function (h) { return data[h] !== undefined ? data[h] : ''; });
    sh.appendRow(row);

    lock.releaseLock();
    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  return ContentService.createTextOutput('봉은문화센터 설문 수집 엔드포인트 — 정상 작동 중입니다.');
}

/**
 * (관리자용) 집계 탭 자동 생성. 응답이 쌓인 뒤 Apps Script 편집기에서 1회 실행.
 * 동의율(매우동의+동의 비율), 핵심 단일문항 분포, 교차분석 예시를 만듭니다.
 */
function setupAggregation() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var agg = ss.getSheetByName('집계');
  if (agg) ss.deleteSheet(agg);
  agg = ss.insertSheet('집계');

  agg.getRange('A1').setValue('봉은문화센터 설문 — 집계').setFontWeight('bold').setFontSize(14);
  agg.getRange('A2').setValue('총 응답 수');
  agg.getRange('B2').setFormula('=COUNTA(응답!A2:A)');

  // 동의 척도 (저장값 1=매우동의 ~ 5=전혀비동의)
  agg.getRange('A4').setValue('■ 핵심 동의 문항 (동의율 = 매우동의+동의 비율)').setFontWeight('bold');
  agg.getRange('A5:C5').setValues([['문항', '동의율', '평균(1=동의 ~ 5=비동의)']]);
  var ag = [['Q5 삶을 정리할 공간 필요', 'F'], ['Q6 서울 정신문화공간 필요', 'G'], ['Q9 수행하는 삶 존중받을 가치', 'J']];
  for (var i = 0; i < ag.length; i++) {
    var row = 6 + i, c = ag[i][1];
    agg.getRange(row, 1).setValue(ag[i][0]);
    agg.getRange(row, 2).setFormula('=IFERROR(COUNTIF(응답!' + c + '2:' + c + ',"<=2")/COUNTA(응답!' + c + '2:' + c + '),"")').setNumberFormat('0%');
    agg.getRange(row, 3).setFormula('=IFERROR(AVERAGE(응답!' + c + '2:' + c + '),"")').setNumberFormat('0.0');
  }

  // 단일문항 분포
  var r = 11;
  var dist = [['Q1 연령', 'B'], ['Q2 종교', 'C'], ['Q3 사찰 방문', 'D'],
              ['Q10 불교 방향 공감', 'K'], ['Q12 본원·센터 구조', 'M'], ['Q15 수익시설', 'P'],
              ['Q17 우려', 'R'], ['Q18 서울에서 공간', 'S'], ['Q21 미래방향 공감', 'V'], ['Q22 우선 투자', 'W']];
  for (var j = 0; j < dist.length; j++) {
    var c2 = dist[j][1];
    agg.getRange(r, 1).setValue('■ ' + dist[j][0]).setFontWeight('bold'); r++;
    agg.getRange(r, 1).setFormula('=QUERY(응답!' + c2 + '2:' + c2 + ', "select Col1, count(Col1) where Col1 is not null group by Col1 order by count(Col1) desc label count(Col1) \'\'", 0)');
    r += 8;
  }

  agg.getRange(r, 1).setValue('※ 복수응답(Q4·Q7·Q8·Q11·Q13·Q14·Q16)은 보기별  =COUNTIF(해당열,"*보기명*")  으로 집계').setFontColor('#888');
  agg.getRange(r + 1, 1).setValue('※ 교차분석 예) 비(非)불교인의 Q5 동의율:  =COUNTIFS(응답!C2:C,"<>불교",응답!F2:F,"<=2")/COUNTIF(응답!C2:C,"<>불교")').setFontColor('#888');
  agg.autoResizeColumns(1, 3);
}
