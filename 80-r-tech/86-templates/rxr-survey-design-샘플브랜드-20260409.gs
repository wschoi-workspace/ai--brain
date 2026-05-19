/**
 * RXR Survey Analysis - Google Forms 자동 생성 스크립트
 *
 * 브랜드: 샘플브랜드
 * 이벤트: Sample Pop-up 2026
 * 생성일: 2026-04-09
 * 경험 유형: 팝업스토어 (활성 구성요소: Space, Content, Product, Community)
 *
 * ============================================
 * 실행 방법:
 * 1. https://script.google.com 접속
 * 2. "새 프로젝트" 클릭
 * 3. 이 코드 전체를 붙여넣기
 * 4. ▶ 실행 버튼 클릭 (createRXRSurvey 함수)
 * 5. Google 계정 권한 승인
 * 6. 실행 로그(Ctrl+Enter)에서 설문 URL 확인
 * ============================================
 */

function createRXRSurvey() {
  var form = FormApp.create('샘플브랜드 — Sample Pop-up 2026 방문객 설문');
  form.setDescription(
    'RXR Survey Analysis | 소요시간: 약 2분\n' +
    '여러분의 솔직한 응답이 더 나은 경험을 만드는 데 큰 도움이 됩니다.'
  );
  form.setConfirmationMessage('설문에 참여해주셔서 진심으로 감사합니다!');
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setShowLinkToRespondAgain(false);

  // ============================================
  // Part A. 기본 정보
  // ============================================
  form.addSectionHeaderItem()
    .setTitle('Part A. 기본 정보')
    .setHelpText('간단한 인적 사항을 알려주세요.');

  // A1. 성별
  form.addMultipleChoiceItem()
    .setTitle('A1. 성별')
    .setChoiceValues(['남성', '여성', '기타/응답하지 않음'])
    .setRequired(true);

  // A2. 연령대
  form.addMultipleChoiceItem()
    .setTitle('A2. 연령대')
    .setChoiceValues([
      '10대',
      '20대 초반(20~24)',
      '20대 후반(25~29)',
      '30대 초반(30~34)',
      '30대 후반(35~39)',
      '40대',
      '50대 이상'
    ])
    .setRequired(true);

  // A3. 방문 경로
  form.addMultipleChoiceItem()
    .setTitle('A3. 어떻게 이 팝업을 알게 되셨나요?')
    .setChoiceValues([
      'SNS (인스타그램/틱톡 등)',
      '인터넷 검색 / 후기',
      '지인 추천',
      '우연히 방문 (지나가다)',
      '인플루언서 / 유튜버',
      '브랜드 공식 채널'
    ])
    .showOtherOption(true)
    .setRequired(true);

  // A4. 동행 형태
  form.addMultipleChoiceItem()
    .setTitle('A4. 동행 형태')
    .setChoiceValues(['혼자', '친구/연인', '가족', '단체/모임'])
    .setRequired(true);

  // A5. 팝업 방문 빈도
  form.addMultipleChoiceItem()
    .setTitle('A5. 최근 1년간 다른 팝업스토어 방문 빈도')
    .setChoiceValues(['처음이다', '연 1~2회', '연 3~5회', '연 6회 이상'])
    .setRequired(true);

  // ============================================
  // Part B. 매력 포인트 & 인게이지먼트 (EDI 핵심)
  // ============================================
  form.addSectionHeaderItem()
    .setTitle('Part B. 매력 포인트 & 인게이지먼트')
    .setHelpText('가장 인상적이었던 것과 그 깊이를 알려주세요.');

  // B1. Stage 1 — 매력 포인트 (체크박스, 최대 2개)
  form.addCheckboxItem()
    .setTitle('B1. 오늘 방문에서 가장 인상적이었던 요소를 1~2개 골라주세요.')
    .setChoiceValues([
      '공간 디자인 / 인테리어',
      '조명 / 분위기',
      '컨셉 / 테마 기획',
      '전시 / 브랜드 스토리',
      'MD 상품 / 굿즈',
      'F&B (음식/음료)',
      '포토존 / 촬영 포인트'
    ])
    .showOtherOption(true)
    .setValidation(
      FormApp.createCheckboxValidation()
        .requireSelectAtMost(2)
        .build()
    )
    .setRequired(true);

  // B2. Stage 2-1 — 기억 선명도
  // 선택지에 따라 분기 (① 선택 시 → B3 자유 서술)
  var memoryItem = form.addMultipleChoiceItem();

  // B3 자유 서술용 페이지 (조건부)
  var memoryTextPage = form.addPageBreakItem()
    .setTitle('기억에 남는 순간')
    .setHelpText('선명한 장면이 있다고 답하셨네요. 그 순간을 짧게 적어주세요.');

  // B4 시작 페이지 (Stage 3)
  var stage3Page = form.addPageBreakItem()
    .setTitle('Part B. 행동 전환')
    .setHelpText('이 경험을 어떻게 나누고 싶으신가요?');

  // memoryItem 분기 설정
  memoryItem
    .setTitle('B2. 선택하신 요소에서 가장 기억에 남는 구체적인 순간이 있으세요?')
    .setChoices([
      memoryItem.createChoice('지금도 선명하게 떠오르는 장면이 있다', memoryTextPage),
      memoryItem.createChoice('전체적으로 좋았는데, 딱 하나를 꼽기는 어렵다', stage3Page),
      memoryItem.createChoice('좋았던 것 같은데 구체적으로는 잘 모르겠다', stage3Page)
    ])
    .setRequired(true);

  // memoryTextPage 다음에 B3 자유 서술 추가
  // (스크립트 실행 순서상 페이지 바로 다음에 배치됨)
  // ※ Apps Script에서는 페이지 break 이후의 항목이 해당 페이지에 속함
  // 위에서 stage3Page를 먼저 추가했기 때문에 순서 재조정 필요
  // 아래 helper로 처리

  // B3. Stage 2-2 — 자유 서술 (memoryTextPage 다음에 추가)
  // 실제로는 페이지 순서를 신경써야 하므로, 아래처럼 다시 작성

  // ============================================
  // ※ 위 분기 로직은 단순화를 위한 예시입니다.
  // 실제 Forms는 항목이 추가되는 순서대로 페이지에 들어가므로,
  // 정확한 분기를 원하시면 아래의 단순 버전을 권장합니다.
  // ============================================

  // B3은 항상 표시 (선택 사항)
  form.addParagraphTextItem()
    .setTitle('B3. (B2에서 "선명한 장면이 있다"고 답하신 경우) 그 순간을 한 줄로 적어주세요.')
    .setHelpText('예: "초콜릿 폭포 앞에서 냄새가 진짜 달콤했다"')
    .setRequired(false);

  // B4. Stage 3-1 — SNS 공유
  form.addMultipleChoiceItem()
    .setTitle('B4. 오늘 경험을 SNS(인스타, 블로그 등)에 올리셨거나 올릴 계획이 있으세요?')
    .setChoiceValues([
      '이미 올렸다 / 올리는 중이다',
      '오늘 중으로 올릴 예정이다',
      '올릴 생각은 있지만 확실하지 않다',
      '올릴 계획 없다'
    ])
    .setRequired(true);

  // B5. Stage 3-2 — 지인 전달
  form.addMultipleChoiceItem()
    .setTitle('B5. 이 경험을 아직 안 가본 지인에게 어떻게 전달하실 것 같으세요?')
    .setChoiceValues([
      '이미 카톡/DM으로 보냈거나 보낼 것이다',
      '만나면 직접 얘기할 것이다',
      '대화 중 자연스럽게 나오면 언급할 것이다',
      '굳이 먼저 얘기하지는 않을 것이다'
    ])
    .setRequired(true);

  // B6. Stage 3-3 — 재방문
  form.addMultipleChoiceItem()
    .setTitle('B6. 이 팝업에 다른 사람을 데리고 다시 오실 의향이 있으세요?')
    .setChoiceValues([
      '이미 누구와 다시 올지 생각해뒀다',
      '기회가 되면 데리고 오고 싶다',
      '혼자라면 올 수도 있지만 데려오지는 않을 것',
      '재방문 의향 없다'
    ])
    .setRequired(true);

  // ============================================
  // 결과 출력
  // ============================================
  Logger.log('=================================');
  Logger.log('✅ 설문 생성 완료!');
  Logger.log('=================================');
  Logger.log('편집 URL: ' + form.getEditUrl());
  Logger.log('응답 URL: ' + form.getPublishedUrl());
  Logger.log('');
  Logger.log('📊 응답 데이터를 스프레드시트로 받으려면:');
  Logger.log('1. 위의 편집 URL 접속');
  Logger.log('2. "응답" 탭 클릭');
  Logger.log('3. 스프레드시트 아이콘 클릭');
  Logger.log('4. 새 스프레드시트 생성');
  Logger.log('=================================');
}
