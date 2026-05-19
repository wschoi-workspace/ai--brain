"""새로중앙박물관 팝업 — 본문 크롤링 + 2-Layer 분석"""
import json, re, sys, urllib.request, time, html as html_mod
from collections import Counter
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
BASE = Path(r'C:\Users\insig\do-better-workspace\30-knowledge')

with open(BASE / 'saero-popup-naver-filtered.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

print(f"대상: {len(posts)}건")

# 본문 크롤링
def fetch_blog(url, max_len=5000):
    try:
        if 'blog.naver.com' in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        })
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8', errors='ignore')
        for pat in [
            r'class="se-main-container">(.*?)</div>\s*</div>\s*</div>',
            r'class="post[_-]?view.*?">(.*?)</div>\s*(?:</div>){2,}',
            r'class="se-component se-text.*?">(.*?)</div>',
        ]:
            matches = re.findall(pat, raw, re.DOTALL)
            if matches:
                text = re.sub(r'<[^>]+>', ' ', ' '.join(matches))
                text = html_mod.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 100:
                    return text[:max_len]
        match = re.search(r'<body.*?>(.*?)</body>', raw, re.DOTALL)
        if match:
            text = re.sub(r'<script.*?</script>', '', match.group(1), flags=re.DOTALL)
            text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = html_mod.unescape(text)
            return re.sub(r'\s+', ' ', text).strip()[:max_len]
        return ''
    except:
        return ''

print("본문 크롤링 시작...")
crawled = 0
for i, post in enumerate(posts):
    content = fetch_blog(post.get('link', ''))
    post['full_content'] = content
    if content and len(content) > 100:
        crawled += 1
    time.sleep(0.25)
    if (i + 1) % 30 == 0:
        print(f"  {i+1}/{len(posts)}건... (본문 {crawled}건)")
print(f"본문 크롤링 완료: {crawled}/{len(posts)}건")

# 토픽 사전 (새로중앙박물관 맞춤)
topics = {
    '공간/분위기': ['공간', '분위기', '인테리어', '예쁘', '포토존', '포토', '사진', '감성', '꾸며', '디자인', '박물관'],
    '방탈출/미션': ['방탈출', '미션', '탈출', '도난', '비법서', '사건', '추리', '단서', '퍼즐', '게임'],
    '제품/소주': ['소주', '새로', '맛', '마셔', '음료', '시음', '시식', '칵테일', '하이볼'],
    '굿즈/럭키드로우': ['굿즈', '럭키드로우', '뽑기', '한정판', '상품', '경품', '키링', '소장'],
    '포토부스': ['포토부스', '네컷', '부스', '스티커', '사진'],
    '웨이팅/예약': ['웨이팅', '예약', '사전예약', '줄', '대기', '오픈런', '현장'],
    '가격/혜택': ['무료', '공짜', '증정', '혜택', '이벤트', '선물'],
}

pos_words = ['좋았', '좋다', '좋아', '추천', '만족', '재미', '재밌', '예쁘', '예뻤', '귀엽', '귀여', '맛있', '대박', '최고',
             '행복', '즐거', '감동', '사랑', '완전', '꼭 가', '핫플', '인생', '꿀잼', '신나', '깔끔', '잘 만들', '몰입']
neg_words = ['별로', '실망', '아쉬', '불편', '짜증', '최악', '후회', '비싸', '비쌌', '웨이팅 길', '사람 많', '혼잡',
             '부족', '없었', '못 받', '아깝', '그냥 그', '기대 이하', '별거 없', '길어', '오래 걸']
sponsored_markers = ['제공받', '협찬', '원고료', '체험단', '소정의', '#광고', '#ad', '서포터즈', '지원받']

results = []
for post in posts:
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    desc = re.sub(r'<[^>]+>', '', post.get('description', ''))
    full = title + ' ' + desc + ' ' + text
    fl = full.lower()
    if len(full) < 50:
        continue

    # Content Layer
    topic_scores = {}
    for topic, kws in topics.items():
        score = sum(fl.count(kw) for kw in kws)
        if score > 0:
            topic_scores[topic] = score
    top_topics = sorted(topic_scores.items(), key=lambda x: -x[1])[:3]
    primary_topic = top_topics[0][0] if top_topics else '기타'

    pos_count = sum(1 for w in pos_words if w in fl)
    neg_count = sum(1 for w in neg_words if w in fl)
    if pos_count > neg_count + 2: sentiment = '긍정'
    elif neg_count > pos_count: sentiment = '부정'
    elif pos_count > 0 and neg_count > 0: sentiment = '혼합'
    else: sentiment = '중립'

    is_sponsored = any(m in fl for m in sponsored_markers)

    word_count = len(full.split())
    has_detail = sum(1 for w in ['시간', '분', '층', '구역', '메뉴', '코스', '가격', '잔', '종류'] if w in fl)
    has_personal = sum(1 for w in ['나는', '내가', '저는', '우리', '남자친구', '친구랑', '엄마', '같이 갔'] if w in fl)

    if word_count > 500 and has_detail >= 3 and has_personal >= 1: rql = 'Q5_서사형'
    elif word_count > 300 and has_detail >= 2: rql = 'Q4_분석형'
    elif word_count > 150 and (has_detail >= 1 or has_personal >= 1): rql = 'Q3_경험형'
    elif word_count > 50: rql = 'Q2_감상형'
    else: rql = 'Q1_간단형'

    # Psyche Layer
    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s', full))
    we_person = len(re.findall(r'우리|같이|함께|다같이', full))
    place_ref = len(re.findall(r'여기|이곳|이 공간|이 매장|이 팝업', full))
    iga = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', full))
    eunneun = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', full))
    total_p = iga + eunneun
    freshness = round(iga / max(total_p, 1) * 100, 1)

    extreme_pos = sum(fl.count(w) for w in ['진짜', '너무너무', '완전', '대박', '미쳤', '최고의', '인생'])
    excl = full.count('!') + full.count('ㅋㅋ')

    auth = 60
    if is_sponsored: auth -= 15
    if extreme_pos > 5: auth -= (extreme_pos - 5) * 3
    if excl > 10: auth -= (excl - 10) * 2
    if has_personal >= 2: auth += 10
    if has_detail >= 3: auth += 10
    if neg_count > 0 and pos_count > 0: auth += 8
    auth = max(10, min(95, auth))

    clout = 40
    rec = sum(1 for w in ['추천', '꼭 가', '강추', '가보세요', '가봐', '놓치지'] if w in fl)
    if rec > 0: clout += rec * 15
    if we_person > first_person: clout += 10
    clout = max(10, min(95, clout))

    date = post.get('postdate', '')
    period = post.get('period', '')

    results.append({
        'date': date, 'period': period, 'title': title,
        'blogger': post.get('bloggername', ''), 'link': post.get('link', ''),
        'word_count': word_count,
        'primary_topic': primary_topic, 'topic_scores': dict(top_topics),
        'sentiment': sentiment, 'pos_count': pos_count, 'neg_count': neg_count,
        'rql': rql, 'is_sponsored': is_sponsored,
        'first_person': first_person, 'we_person': we_person, 'place_ref': place_ref,
        'iga_count': iga, 'eunneun_count': eunneun, 'freshness_index': freshness,
        'authenticity': auth, 'clout': clout, 'extreme_pos': extreme_pos, 'exclamation': excl,
    })

print(f"\n분석 완료: {len(results)}건")

# 통계
print("\n" + "="*60)
print("--- 토픽 분포 ---")
for t, c in Counter(r['primary_topic'] for r in results).most_common():
    print(f"  {t}: {'█'*c} {c}건")

print("\n--- 감성 ---")
for s, c in Counter(r['sentiment'] for r in results).most_common():
    print(f"  {s}: {c}건 ({c/len(results)*100:.0f}%)")

print("\n--- RQL ---")
for q in ['Q5_서사형','Q4_분석형','Q3_경험형','Q2_감상형','Q1_간단형']:
    c = sum(1 for r in results if r['rql']==q)
    print(f"  {q}: {c}건")

print("\n--- 협찬 vs 자발적 ---")
spon = [r for r in results if r['is_sponsored']]
org = [r for r in results if not r['is_sponsored']]
print(f"  자발적: {len(org)}건 / 협찬: {len(spon)}건")
if org:
    print(f"  자발적 Auth: {sum(r['authenticity'] for r in org)/len(org):.1f}")
if spon:
    print(f"  협찬 Auth: {sum(r['authenticity'] for r in spon)/len(spon):.1f}")

print("\n--- Psyche 평균 ---")
avg_a = sum(r['authenticity'] for r in results)/len(results)
avg_c = sum(r['clout'] for r in results)/len(results)
avg_f = sum(r['freshness_index'] for r in results)/len(results)
print(f"  Auth: {avg_a:.1f} / Clout: {avg_c:.1f} / Freshness: {avg_f:.1f}")

print("\n--- 기간별 Psyche ---")
for period in ['이벤트전(~3/20)', '이벤트기간(3/21~4/5)', '이벤트후(4/6~)']:
    sub = [r for r in results if r['period']==period]
    if sub:
        a = sum(r['authenticity'] for r in sub)/len(sub)
        c = sum(r['clout'] for r in sub)/len(sub)
        f = sum(r['freshness_index'] for r in sub)/len(sub)
        print(f"  [{period}] N={len(sub)} | Auth={a:.1f} | Clout={c:.1f} | Fresh={f:.1f}")

# Sincerity Gate
print("\n--- Sincerity Gate ---")
g1 = results
g2 = [r for r in results if not r['is_sponsored']]
g3 = [r for r in g2 if r['authenticity'] >= 60]
for label, sub in [('Gate 1 전체', g1), ('Gate 2 협찬제외', g2), ('Gate 3 Auth60+', g3)]:
    n = len(sub)
    sent = Counter(r['sentiment'] for r in sub)
    pos = sent.get('긍정',0)/n*100 if n else 0
    avg_auth = sum(r['authenticity'] for r in sub)/n if n else 0
    print(f"  [{label}] N={n} | 긍정={pos:.0f}% | Auth={avg_auth:.1f}")

out = BASE / 'saero-popup-2layer-results.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved: {out}")
