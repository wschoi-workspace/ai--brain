"""comonstyle 스크립트를 가나용으로 일괄 치환"""
import os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = '80-r-tech/84-scripts/gana-chocolate-house'
FILES = ['gana_report_gen.py', 'gana_external_gen.py', 'gana_excel_gen.py']

# 순서 중요: 긴 토큰 먼저
REPLACEMENTS = [
    # 파일 경로
    ('comonstyle-popup-2layer-results.json', '../../85-analysis-results/gana-chocolate-house/gana-chocolate-house-2layer-results.json'),
    ('comonstyle-popup-rxr-sns-report.html', '../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report.html'),
    ('comonstyle-popup-rxr-sns-report-external.html', '../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report-external.html'),
    ('comonstyle-popup-rxr-sns-report-locked.html', '../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report-locked.html'),
    ('comonstyle-popup-rxr-sns-data.xlsx', '../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-data.xlsx'),

    # 타이틀/브랜드
    ('CJ온스타일 컴온스타일 팝업스토어', '가나초콜릿하우스 부산 시즌2'),
    ('CJ온스타일 컴온스타일 — 쇼케이스 팝업스토어', '가나초콜릿하우스 부산 · 시즌2'),
    ('컴온스타일 팝업스토어', '가나초콜릿하우스 부산 시즌2'),
    ('컴온스타일 쇼케이스 팝업스토어', '가나초콜릿하우스 부산 (2023 시즌2)'),
    ('CJ온스타일의 첫 오프라인 팝업스토어', '롯데제과 가나의 두 번째 오프라인 팝업스토어'),
    ('CJ온스타일', '롯데제과 가나'),
    ('컴온스타일', '가나초콜릿하우스'),

    # 장소/컨셉
    ('서울 성수동 XYZ서울', '부산 전포동 프로젝트렌트'),
    ('성수동 XYZ서울', '부산 전포동 프로젝트렌트'),
    ('슬로우에이징 라이프스타일 + 4 IP프로그램 + 무라카미 다카시 콜라보', '초콜릿 × 위스키 페어링 바 + 애프터눈티'),
    ('슬로우에이징 라이프스타일 솔루션', '초콜릿 × 위스키 페어링 라이프스타일'),
    ('"슬로우에이징" 컨셉', '"위스키 페어링" 컨셉'),
    ('"슬로우에이징"', '"위스키 페어링"'),
    ('슬로우에이징', '위스키 페어링'),

    # 기간
    ('2025.04.04 ~ 04.08', '2023.02.12 ~ 03.14'),
    ('2025.03.21 ~ 04.22', '2023.01.29 ~ 04.11'),
    ('5일간', '31일간'),
    ('5일 단기 집중형', '31일 장기 운영형'),
    ('5일 집중 운영', '31일 장기 운영'),
    ('5일이라는 짧은 운영 기간', '31일이라는 장기 운영 기간'),
    ('16일간 운영된 다른 팝업', '5일간 운영된 다른 팝업(컴온스타일)'),
    ('5일', '31일'),
    ('14일', '14일'),  # 사전 기간은 동일

    # 날짜 (하드코딩된 string 비교)
    ('d < "20250404"', 'd < "20230212"'),
    ('d <= "20250408"', 'd <= "20230314"'),
    ('d == "20250404"', 'd == "20230212"'),
    ('d == "20250409"', 'd == "20230315"'),
    ('"20250404"', '"20230212"'),
    ('"20250408"', '"20230314"'),
    ('"20250409"', '"20230315"'),

    # 기간 라벨
    ('사전 (03/21~04/03)', '사전 (01/29~02/11)'),
    ('팝업기간 (04/04~04/08)', '팝업기간 (02/12~03/14)'),
    ('팝업후 (04/09~04/22)', '팝업후 (03/15~04/11)'),

    # 일수 나눗셈
    ('/14,1)', '/14,1)'),  # 사전 동일
    ('/5,1)', '/31,1)'),    # 팝업기간: 5→31일
    ('/5)', '/31)'),
    ('get("사전",{}).get("n",1)*100', 'get("사전",{}).get("n",1)*100'),

    # 브랜드 전용 해석 (치환 후 유효)
    ('"보라색 공간이 예뻤다"(41%)', '"초콜릿 맛"(93.4%)'),
    ('"보라색 예쁜 공간"', '"초콜릿 맛집"'),
    ('"나의 슬로우에이징 루틴 만들기"', '"나의 시그니처 페어링 찾기"'),

    # IP 프로그램 섹션 — 가나는 IP 없음, 컨셉 분석으로 전환
    ('("최화정", "겟잇뷰티", "한예슬", "안재현")', '("위스키", "페어링", "애프터눈티", "다크초콜릿")'),
    ('4개 IP 프로그램(최화정쇼, 겟잇뷰티, 한예슬의 오늘 뭐 입지, 안재현의 잠시 실내합니다)', '팝업의 4대 체험 요소(위스키 페어링, 다크초콜릿 바, 애프터눈티, 포토존)'),
    ('4개 IP가 하나의 공간에 통합되면서 개별 인지가 희미해졌습니다', '4개 체험 요소 중 페어링·애프터눈티 같은 차별화 콘텐츠는 초콜릿 맛이라는 기본 경험에 완전히 가려졌습니다'),
    ('각 IP 전용 포토존과 해시태그를 분리 운영', '차별화 콘텐츠별 전용 포토존과 해시태그 분리 운영'),
    ('IP 프로그램별 독립 화제성', '차별화 콘텐츠별 독립 화제성'),
    ('4개 IP', '4개 체험 요소'),
    ('각 IP', '각 체험 요소'),
    ('IP 프로그램', '체험 요소'),
    ('IP별 팬덤', '체험별 관심층'),
    ('IP 개별 화제성', '체험 요소별 화제성'),
    ('최화정쇼만이', '"초콜릿 맛" 주제만이'),
    ('{ip_mentions.get("최화정",0)}', '{ip_mentions.get("위스키",0)+ip_mentions.get("페어링",0)}'),
    ('나머지 IP는', '나머지 차별화 요소(애프터눈티·페어링·다크초콜릿)는'),
    ('IP 전용 포토존', '체험 요소별 전용 포토존'),

    # Brand24 없음 처리 — 가나는 Brand24 미확보, 네이버만 분석
    ('b24 = {"total": 462, "reach": "~4M", "instagram": 229, "tiktok": 52, "x": 12, "news": 8, "facebook": 4, "web": 1, "blogs": 156}',
     'b24 = {"total": 0, "reach": "N/A", "instagram": 0, "tiktok": 0, "x": 0, "news": 0, "facebook": 0, "web": 1, "blogs": 0}'),

    # 최화정쇼 라인 치환
    ('최화정쇼',  '"위스키 페어링"'),
]

for fname in FILES:
    path = os.path.join(BASE, fname)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    original_len = len(content)
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"{fname}: {original_len} → {len(content)} bytes")

print("localize 완료")
