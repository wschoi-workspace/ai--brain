"""
RXR 2-Layer Analysis Engine v0.1
이클립스 월드 팝업 — 네이버 블로그 본문 크롤링 + Content Layer + Psyche Layer
"""
import json, re, sys, urllib.request, time, html
from collections import Counter
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

BASE = Path(r'C:\Users\insig\do-better-workspace\30-knowledge')

# ============================================================
# 1. 본문 크롤링
# ============================================================
print("=" * 60)
print("STEP 1: 블로그 본문 크롤링")
print("=" * 60)

with open(BASE / 'eclipse-popup-naver-final.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

print(f"대상 포스트: {len(posts)}건 (팝업 관련 정밀 필터)")

def fetch_blog_content(url, max_len=5000):
    try:
        if 'blog.naver.com' in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        })
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8', errors='ignore')

        # 본문 추출 패턴들
        patterns = [
            r'class="se-main-container">(.*?)</div>\s*</div>\s*</div>',
            r'class="post[_-]?view.*?">(.*?)</div>\s*(?:</div>){2,}',
            r'class="se-component se-text.*?">(.*?)</div>',
            r'<div class="content">(.*?)</div>',
        ]

        text = ''
        for pat in patterns:
            matches = re.findall(pat, raw, re.DOTALL)
            if matches:
                combined = ' '.join(matches)
                text = re.sub(r'<[^>]+>', ' ', combined)
                text = html.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 100:
                    break

        if not text or len(text) < 50:
            # 최후 수단: body 전체
            match = re.search(r'<body.*?>(.*?)</body>', raw, re.DOTALL)
            if match:
                text = re.sub(r'<script.*?</script>', '', match.group(1), flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = html.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()

        return text[:max_len]
    except Exception as e:
        return ''

crawled = 0
for i, post in enumerate(posts):
    content = fetch_blog_content(post.get('link', ''))
    post['full_content'] = content
    if content and len(content) > 100:
        crawled += 1
    time.sleep(0.3)
    if (i + 1) % 10 == 0:
        print(f"  {i+1}/{len(posts)}건 처리... (본문 확보: {crawled}건)")

print(f"본문 크롤링 완료: {crawled}/{len(posts)}건 확보")

# ============================================================
# 2. Content Layer 분석
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Content Layer 분석")
print("=" * 60)

# 토픽 키워드 사전
topics = {
    '공간/분위기': ['공간', '분위기', '인테리어', '예쁘', '포토존', '포토', '사진', '비주얼', '감성', '꾸며', '디자인'],
    '게임/미션': ['게임', '미션', '오락실', '레트로', '총', '조이스틱', '아케이드', '슈팅', '클리어'],
    '제품/맛': ['포도', '포도향', '민트', '맛', '상큼', '달콤', '향', '먹어', '맛있'],
    '굿즈/가챠': ['굿즈', '가챠', '뽑기', '키링', '커스텀', '한정판', '비누', '키캡', '젤리케이스'],
    '포토부스': ['포토부스', '사진', '네컷', '부스', '스티커'],
    '웨이팅/예약': ['웨이팅', '예약', '사전예약', '줄', '대기', '오픈런'],
    '가격/혜택': ['무료', '공짜', '증정', '혜택', '이벤트', '선물'],
}

# 감성 키워드
pos_words = ['좋았', '좋다', '좋아', '추천', '만족', '재미', '재밌', '예쁘', '예뻤', '귀엽', '귀여', '맛있', '대박', '최고',
             '행복', '즐거', '감동', '사랑', '완전', '꼭 가', '핫플', '인생', '꿀잼', '대존잼', '신나', '상큼', '깔끔']
neg_words = ['별로', '실망', '아쉬', '불편', '짜증', '최악', '후회', '비싸', '비쌌', '웨이팅 길', '사람 많', '혼잡',
             '부족', '없었', '못 받', '아깝', '그냥 그', '기대 이하', '별거 없']

# 협찬 감지
sponsored_markers = ['제공받', '협찬', '원고료', '체험단', '소정의', '제품을 받', '광고', '#광고', '#ad',
                     '서포터즈', '지원받', '원고', '대가를 받']

results = []

for post in posts:
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    desc = re.sub(r'<[^>]+>', '', post.get('description', ''))
    full_text = title + ' ' + desc + ' ' + text
    full_lower = full_text.lower()

    if len(full_text) < 50:
        continue

    # --- Content Layer ---

    # 토픽 분석
    topic_scores = {}
    for topic, keywords in topics.items():
        score = sum(full_lower.count(kw) for kw in keywords)
        if score > 0:
            topic_scores[topic] = score

    top_topics = sorted(topic_scores.items(), key=lambda x: -x[1])[:3]
    primary_topic = top_topics[0][0] if top_topics else '기타'

    # 감성 분석
    pos_count = sum(1 for w in pos_words if w in full_lower)
    neg_count = sum(1 for w in neg_words if w in full_lower)

    if pos_count > neg_count + 2:
        sentiment = '긍정'
    elif neg_count > pos_count:
        sentiment = '부정'
    elif pos_count > 0 and neg_count > 0:
        sentiment = '혼합'
    else:
        sentiment = '중립'

    # 협찬 감지
    is_sponsored = any(m in full_lower for m in sponsored_markers)

    # 후기 깊이 (RQL)
    word_count = len(full_text.split())
    has_detail = sum(1 for w in ['시간', '분', '층', '구역', '메뉴', '코스', '가격'] if w in full_lower)
    has_personal = sum(1 for w in ['나는', '내가', '저는', '우리', '남자친구', '친구랑', '엄마'] if w in full_lower)

    if word_count > 500 and has_detail >= 3 and has_personal >= 1:
        rql = 'Q5_서사형'
    elif word_count > 300 and has_detail >= 2:
        rql = 'Q4_분석형'
    elif word_count > 150 and (has_detail >= 1 or has_personal >= 1):
        rql = 'Q3_경험형'
    elif word_count > 50:
        rql = 'Q2_감상형'
    else:
        rql = 'Q1_간단형'

    # --- Psyche Layer ---

    # 대명사 패턴
    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s', full_text))
    we_person = len(re.findall(r'우리|같이|함께|다같이', full_text))
    place_ref = len(re.findall(r'여기|이곳|이 공간|이 매장|이 팝업', full_text))

    # 조사 패턴: 이/가 (초점/발견) vs 은/는 (주제/설명)
    iga_count = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', full_text))
    eunneun_count = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', full_text))

    # Freshness Index (이/가 비율이 높을수록 새로운 발견 느낌)
    total_particles = iga_count + eunneun_count
    freshness = round(iga_count / max(total_particles, 1) * 100, 1)

    # 감정어 다양성
    emotion_words_found = [w for w in pos_words + neg_words if w in full_lower]
    emotion_diversity = len(set(emotion_words_found))

    # 과잉 긍정 패턴 (Authenticity 역지표)
    extreme_pos = sum(full_lower.count(w) for w in ['진짜', '너무너무', '완전', '대박', '미쳤', '최고의', '인생'])
    exclamation = full_text.count('!') + full_text.count('!!') + full_text.count('ㅋㅋ')

    # Authenticity 추정 (0~100)
    # 높을수록 진정성 높음
    auth_score = 60  # 기본값
    if is_sponsored:
        auth_score -= 15
    if extreme_pos > 5:
        auth_score -= (extreme_pos - 5) * 3
    if exclamation > 10:
        auth_score -= (exclamation - 10) * 2
    if has_personal >= 2:
        auth_score += 10
    if has_detail >= 3:
        auth_score += 10
    if neg_count > 0 and pos_count > 0:
        auth_score += 8  # 균형 잡힌 평가
    auth_score = max(10, min(95, auth_score))

    # Clout 추정 (0~100)
    # 높을수록 추천 확신 강함
    clout_score = 40  # 기본값
    recommend_words = sum(1 for w in ['추천', '꼭 가', '강추', '가보세요', '가봐', '놓치지'] if w in full_lower)
    if recommend_words > 0:
        clout_score += recommend_words * 15
    if we_person > first_person:
        clout_score += 10
    clout_score = max(10, min(95, clout_score))

    # 기간 분류
    date = post.get('postdate', '')
    if date < '20260312':
        period = '사전'
    elif date <= '20260315':
        period = '팝업기간'
    else:
        period = '팝업후'

    results.append({
        'date': date,
        'period': period,
        'title': title,
        'blogger': post.get('bloggername', ''),
        'link': post.get('link', ''),
        'word_count': word_count,
        # Content Layer
        'primary_topic': primary_topic,
        'topic_scores': dict(top_topics),
        'sentiment': sentiment,
        'pos_count': pos_count,
        'neg_count': neg_count,
        'rql': rql,
        'is_sponsored': is_sponsored,
        # Psyche Layer
        'first_person': first_person,
        'we_person': we_person,
        'place_ref': place_ref,
        'iga_count': iga_count,
        'eunneun_count': eunneun_count,
        'freshness_index': freshness,
        'emotion_diversity': emotion_diversity,
        'authenticity': auth_score,
        'clout': clout_score,
        'extreme_pos': extreme_pos,
        'exclamation': exclamation,
    })

print(f"분석 완료: {len(results)}건")

# ============================================================
# 3. 통계 출력
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: 분석 결과 통계")
print("=" * 60)

# 토픽 분포
print("\n--- 토픽 분포 ---")
topic_dist = Counter(r['primary_topic'] for r in results)
for t, c in topic_dist.most_common():
    bar = '█' * c
    print(f"  {t}: {bar} {c}건")

# 감성 분포
print("\n--- 감성 분포 ---")
sent_dist = Counter(r['sentiment'] for r in results)
for s, c in sent_dist.most_common():
    print(f"  {s}: {c}건 ({c/len(results)*100:.0f}%)")

# RQL 분포
print("\n--- 후기 깊이 (RQL) ---")
rql_dist = Counter(r['rql'] for r in results)
for q in ['Q5_서사형', 'Q4_분석형', 'Q3_경험형', 'Q2_감상형', 'Q1_간단형']:
    c = rql_dist.get(q, 0)
    bar = '█' * c
    print(f"  {q}: {bar} {c}건")

# 협찬 vs 자발적
print("\n--- 협찬 vs 자발적 ---")
sponsored = [r for r in results if r['is_sponsored']]
organic = [r for r in results if not r['is_sponsored']]
print(f"  자발적: {len(organic)}건")
print(f"  협찬: {len(sponsored)}건")

if sponsored:
    avg_auth_s = sum(r['authenticity'] for r in sponsored) / len(sponsored)
    avg_auth_o = sum(r['authenticity'] for r in organic) / len(organic) if organic else 0
    print(f"  자발적 평균 Authenticity: {avg_auth_o:.1f}")
    print(f"  협찬 평균 Authenticity: {avg_auth_s:.1f}")

# Psyche Layer 통계
print("\n--- Psyche Layer 평균 ---")
avg_auth = sum(r['authenticity'] for r in results) / len(results)
avg_clout = sum(r['clout'] for r in results) / len(results)
avg_fresh = sum(r['freshness_index'] for r in results) / len(results)
print(f"  Authenticity 평균: {avg_auth:.1f}")
print(f"  Clout 평균: {avg_clout:.1f}")
print(f"  Freshness Index 평균: {avg_fresh:.1f}")

# 기간별 비교
print("\n--- 기간별 Psyche 비교 ---")
for period in ['사전', '팝업기간', '팝업후']:
    subset = [r for r in results if r['period'] == period]
    if subset:
        a = sum(r['authenticity'] for r in subset) / len(subset)
        c = sum(r['clout'] for r in subset) / len(subset)
        f = sum(r['freshness_index'] for r in subset) / len(subset)
        print(f"  [{period}] N={len(subset)} | Auth={a:.1f} | Clout={c:.1f} | Fresh={f:.1f}")

# ============================================================
# 4. 저장
# ============================================================
out_path = BASE / 'eclipse-popup-2layer-results.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n저장 완료: {out_path}")
print(f"총 {len(results)}건 2-Layer 분석 완료")
