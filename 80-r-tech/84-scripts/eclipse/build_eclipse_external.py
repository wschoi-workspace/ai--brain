"""이클립스 외부용 리포트 생성: 부록 교체 + Executive Summary 추가"""

with open('eclipse-popup-rxr-sns-report-external.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace appendix (63건 Raw Data → 하이라이트 20건)
start = content.find('<!-- 부록 -->')
end = content.find('<div class="footer">')

highlight = """<!-- 부록 -->
<h2>부록: 진심 필터 통과 — 하이라이트 20건</h2>
<p style="font-size:12px;color:var(--body);margin-bottom:12px;line-height:1.7;">676건의 멘션 중 진심 필터를 통과한 63건에서, 진정성이 가장 높은 후기 10건과 가장 낮은 후기 10건을 선별했습니다.</p>

<h3 style="color:var(--green);">진정성이 빛나는 후기 TOP 10</h3>
<div style="margin-bottom:16px;">
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 매우 높음</div><div style="font-size:11px;color:var(--body);">"성수 팝업 이클립스 월드 Into the tincase 방문 후기..." (03/14) &middot; 긍정 &middot; Q5 서사형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">694자의 장편 체험기 &mdash; 게임/미션부터 굿즈까지 구체적 동선 묘사</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 매우 높음</div><div style="font-size:11px;color:var(--body);">"성수 핫플 팝업 이클립스 월드투어 성수성수성수 뿌" (03/15) &middot; 혼합 &middot; Q5 서사형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">좋은 점과 아쉬운 점을 균형 있게 서술한 솔직한 체험기</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 매우 높음</div><div style="font-size:11px;color:var(--body);">"성수 인더틴 틴케이스 성수 이클립스 월드 팝업스토어..." (03/14) &middot; 긍정 &middot; Q5 서사형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">제품 맛 평가와 공간 분위기를 구체적으로 기록</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 매우 높음</div><div style="font-size:11px;color:var(--body);">"이클립스 팝업 성수 3월 성수동 팝업 성수동 후기" (03/13) &middot; 긍정 &middot; Q5 서사형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">웨이팅 경험부터 미니게임까지 시간순 생생한 서술</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 매우 높음</div><div style="font-size:11px;color:var(--body);">"성수 성수동 이클립스 월드 팝업스토어 후기 (+체험, 이벤트 정보)" (03/13) &middot; 혼합 &middot; Q5 서사형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">체험 구성에 대한 상세한 분석과 균형 잡힌 평가</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 높음</div><div style="font-size:11px;color:var(--body);">"#5 일상편 (성수 이클립스)" (03/19) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">팝업 종료 후에도 기억에 남는 경험을 진솔하게 회상</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 높음</div><div style="font-size:11px;color:var(--body);">"3월 성수 팝업스토어 - 이클립스 월드 : Into the tincase..." (03/13) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">예약 방법부터 체험 구성까지 정보성과 감상을 겸비</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 높음</div><div style="font-size:11px;color:var(--body);">"성수 팝업스토어 예약 및 리뷰 이클립스 월드 팝업 방문 후기" (03/11) &middot; 중립 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">객관적 톤으로 장단점을 분석한 정보 중심 후기</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 높음</div><div style="font-size:11px;color:var(--body);">"해외에서 먼저 인기였던 이클립스 캔디향, 드디어 한국 팝업..." (03/08) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">해외 트렌드 맥락에서 한국 팝업의 의미를 분석</div></div>
  <div style="padding:10px 14px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--green);margin-bottom:2px;">진정성 높음</div><div style="font-size:11px;color:var(--body);">"성수동 팝업 예약 일정 무료! 룰루카, 태그미웰딩 팝업..." (03/14) &middot; 중립 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">여러 팝업을 비교하며 이클립스만의 차별점을 객관적으로 기술</div></div>
</div>

<h3 style="color:var(--coral);">과장이 눈에 띄는 후기 10건</h3>
<div style="margin-bottom:16px;">
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 매우 낮음</div><div style="font-size:11px;color:var(--body);">"[성수] 성수성수동 이클립스 월드투어 팝업스토어 후기" (03/18) &middot; 긍정 &middot; Q3 경험형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 64개 &mdash; 과도한 감탄이 구체적 경험을 대체</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 매우 낮음</div><div style="font-size:11px;color:var(--body);">"성수 | 3월 성수 팝업스토어 3곳 (중앙 룰루카페, 이클립스 월드..." (03/14) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 64개 &mdash; 정보는 있으나 감탄 과잉으로 진정성 하락</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 매우 낮음</div><div style="font-size:11px;color:var(--body);">"성수 3월 팝업스토어 성수 이클립스 월드, 룰루카페 뉴메달..." (03/14) &middot; 혼합 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 57개 &mdash; 여러 팝업을 다루며 깊이가 분산</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"[성수] 성수팝업 - 이클립스팝업(이클립스 월드: Into the..." (03/14) &middot; 중립 &middot; Q3 경험형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 34개 &mdash; 체험 내용이 사진 위주로 텍스트 깊이 부족</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"3월 성수 이클립스 팝업 월드 후기, 성수 성수동" (03/15) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 34개 &mdash; 긍정이지만 구체적 체험 서술 부재</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"[성수/성수] 이클립스 월드투어 성수! 성수 팝업스토어..." (03/14) &middot; 긍정 &middot; Q3 경험형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 31개 &mdash; 반복적 감탄사 위주의 짧은 감상</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"팝 팝업 성수동 후기(루루카페/에디포인트/이클립스..." (03/13) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 30개 &mdash; 여러 팝업 나열로 개별 깊이 부족</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"[성수팝업] 이클립스 월드 성수 팝업스토어 - 한정품 언팩 ~3월..." (03/13) &middot; 혼합 &middot; Q3 경험형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 27개 &mdash; 한정품 정보 위주, 체험 감상 부족</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"성수팝업 이클립스 월드 성수성수 씹는링크 이벤트 사전 예약..." (03/07) &middot; 긍정 &middot; Q3 경험형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 23개 &mdash; 이벤트 정보 나열에 그침</div></div>
  <div style="padding:10px 14px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);margin-bottom:6px;"><div style="font-size:12px;font-weight:700;color:var(--coral);margin-bottom:2px;">진정성 낮음</div><div style="font-size:11px;color:var(--body);">"12~3.15) 후기 | 이클립스 한정품 성수 대형매장쇼핑 팝업스토어" (03/15) &middot; 긍정 &middot; Q4 분석형</div><div style="font-size:10px;color:#94a3b8;margin-top:2px;">느낌표 21개 &mdash; 쇼핑 위주, 체험 깊이 제한적</div></div>
</div>

<div class="insight" style="font-size:12px;line-height:1.7;">
  <strong>같은 "긍정"이지만 전혀 다른 깊이.</strong> 진정성이 높은 후기는 구체적인 경험과 솔직한 감상이 담겨 있고, 낮은 후기는 느낌표와 감탄사가 내용을 대신합니다. RXR의 진심 필터는 이 차이를 수치로 포착하여, 브랜드가 정말로 귀 기울여야 할 목소리를 찾아냅니다.
</div>

"""

content = content[:start] + highlight + '\n' + content[end:]

# 2. Add Executive Summary after 리서치 개요, before 섹션 0
idx = content.find('<!-- 0. ')

exec_summary = """<!-- Executive Summary -->
<div style="padding:28px;background:linear-gradient(135deg,#f8f7ff,#eef2ff);border-radius:16px;margin-bottom:28px;border:1px solid var(--primary-pale);">
  <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--primary);margin-bottom:8px;">EXECUTIVE SUMMARY</div>
  <h2 style="margin:0 0 16px;border:none;padding:0;font-size:18px;">이 리포트가 말하는 것</h2>

  <div style="font-size:13px;color:var(--body);line-height:1.9;">
    <p style="margin-bottom:14px;">이클립스 월드 팝업은 4일간의 짧은 운영 기간 동안 네이버 블로그와 SNS를 합쳐 <strong style="color:var(--primary);">총 676건의 멘션</strong>을 만들어냈습니다. 기존 분석 도구로 보면 "긍정 46%, 관심은 높았다"는 결론이 나옵니다. 하지만 RXR의 다층 분석으로 들여다보면, 숫자 뒤에 숨겨진 이야기가 보입니다.</p>

    <p style="margin-bottom:14px;">676건 중 텍스트 심층 분석이 가능한 90건을 진심 필터로 걸러낸 결과, 유효 반응은 <strong style="color:var(--primary);">63건</strong>이었습니다. 이 과정에서 <strong style="color:var(--coral);">긍정률은 46%에서 33%로 떨어졌습니다.</strong> 과장된 감탄이 실제 긍정을 부풀리고 있었던 것입니다.</p>

    <p style="margin-bottom:14px;">흥미로운 점은 <strong style="color:var(--primary);">신제품 버즈가 팝업 자체보다 4.5배 더 컸다</strong>는 사실입니다. 2월 말 포도향 이클립스 출시 소식이 3월 초까지 일 평균 30건 이상의 포스트를 만들어냈고, 정작 팝업 기간(3/12~15)에는 일 평균 11.5건에 그쳤습니다. 팝업이 신제품 화제의 부록처럼 소비된 셈입니다.</p>

    <p style="margin-bottom:14px;">토픽 분석에서도 비슷한 패턴이 나타났습니다. 이클립스 월드의 핵심 체험인 미니게임과 미션이 전체 토픽의 <strong style="color:var(--primary);">8%에 불과</strong>했고, 68%는 제품/맛 이야기로 채워졌습니다. 방문자들은 "게임이 재미있었다"보다 "포도향이 맛있었다"를 더 많이 기억하고 공유했습니다.</p>

    <p style="margin-bottom:20px;">반면 긍정적인 발견도 있었습니다. <strong style="color:var(--green);">4일 단기 운영 덕분에 진정성 하락이 적었습니다.</strong> 16일 운영된 새로중앙박물관은 후반부 진정성이 20점 급락했지만, 이클립스는 6점 하락에 그쳤습니다. 짧은 기간이 오히려 생생한 체험 기억을 보존한 것입니다.</p>

    <div style="padding:16px;background:#fff;border-radius:12px;border-left:4px solid var(--primary);">
      <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">다음 팝업을 위한 제언</div>
      <div style="font-size:12px;color:var(--body);line-height:1.8;">
        <strong>1. 팝업 독자 화제화가 필요합니다.</strong> 신제품 출시 버즈에 의존하지 않고, 팝업 자체가 화제가 되는 콘텐츠를 설계해야 합니다. "이클립스 팝업에서만 할 수 있는 경험"을 명확히 하고, 사전 홍보에서 이를 중심으로 기대감을 형성하는 것이 효과적입니다.<br><br>
        <strong>2. 체험 요소의 화제화 비중을 높여야 합니다.</strong> 미니게임과 미션이 8%만 언급된 것은 체험이 콘텐츠로 전환되지 못했음을 의미합니다. 게임 결과를 SNS에 공유하는 장치, 미션 클리어 인증샷 포토존 등 "말하고 싶게 만드는" 설계가 필요합니다.<br><br>
        <strong>3. 4일 단기 운영의 강점을 살려야 합니다.</strong> 진정성 하락이 적다는 것은 단기 집중 운영의 명확한 장점입니다. 이 특성을 활용해 "한정된 시간, 특별한 경험"이라는 희소성 메시지를 강화하면 브랜드 옹호자 전환율을 높일 수 있습니다.
      </div>
    </div>
  </div>
</div>

"""

content = content[:idx] + exec_summary + content[idx:]

with open('eclipse-popup-rxr-sns-report-external.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("External version complete")
