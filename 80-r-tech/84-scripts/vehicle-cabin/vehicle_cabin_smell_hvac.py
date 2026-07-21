"""
냄새 + 공조 멘션 세부 분석 (미세먼지·새차냄새 제외)
Gate4 clean 중 KEEP 8토픽 대상 → 냄새유형/공조불편/트리거/원인/대처/감정/브랜드 교차 → smell_hvac_deep.json
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
DATA = Path(__file__).parent.parent.parent.parent / '10-projects' / '37-hyundai-rxr-cabin-air' / 'data' / '2026-07-17'
results = json.loads((DATA / 'analysis-results.json').read_text(encoding='utf-8'))

# --- 광고필터 (adfilter/deep와 동일) ---
STRONG_AD = ['디테일링','출장세차','실내크리닝','특수크리닝','에바크리닝','에어컨 클리닝','에어컨클리닝','썬팅','틴팅','ppf','랩핑','폴리싱','전문점','전문 업체','상담 문의','견적 문의','인사드립니다','매장에 입고','입고되었','입고 되었','작업 입니다','작업입니다','시공 후기','시공했','시공 완료','방문 예약','예약 문의','카톡 문의','전화 주세요','네이버 예약','플레이스','제공받','협찬','원고료','체험단','소정의','지원받아','무상 제공','무상제공','대가를 받','수수료를 지급','수수료를 제공','파트너스','쿠팡파트너스','쇼핑커넥트','일환으로 작성','일환으로 수수료','공동구매','공구 진행','스마트스토어','초특가','재입고','최저가','할인 찬스','할인찬스','구매링크','구매 링크','내돈내산 아니','업체로부터','제품을 제공','디퓨저','방향제 추천','방향제추천','무향탈취제','탈취제 추천','탈취제추천','석고 방향제','디퓨저 추천','카테리어','발향력','방향제 후기','제품을 소개','소개하고 싶었']
WEAK_AD = ['할인','고객님','차주분','의뢰','매장','샵','구매','판매','링크','정가','세일','포인트 적립','쿠폰','이벤트','증정']
VEHICLE_CONFIRM = ['자동차','차량','차 안','차안','차량용','신차','중고차','전기차','내 차','제 차','운전석','뒷좌석','트렁크','에바','에바포레이터','공조기','시동','주행','엔진','에어컨 필터','에어컨필터','캐빈필터','디포그','오토에어컨','ev3','ev6','ev9','아이오닉','캐스퍼','그랜저','쏘렌토','카니발','싼타페','투싼','코나','아반떼','쏘나타','제네시스','gv70','gv80','테슬라','모델y','모델3','bmw','벤츠','아우디','볼보','폭스바겐','스포티지','셀토스']
NON_VEHICLE_NOISE = ['입주청소','이사청소','입주 청소','아파트','오피스텔','분양','부동산','리첸시아','파밀리에','전용면적','평형','거실','침실','주방','싱크대','베란다','에어프라이어','제습기','반려동물','강아지','고양이','냥이','원룸','신축','청약','세대수','발코니','입주민','집 냄새','집냄새','실내 인테리어','정부세종청사','국회']
def is_ad(post):
    t=(post.get('title','')+' '+(post.get('full_content','') or '')).lower()
    if any(m.lower() in t for m in STRONG_AD): return True
    if not any(v.lower() in t for v in VEHICLE_CONFIRM): return True
    if len([n for n in NON_VEHICLE_NOISE if n.lower() in t])>=2: return True
    if len([m for m in WEAK_AD if m.lower() in t])>=2: return True
    return False

valid=[r for r in results if r.get('content_class') in ('A','B')]
gate4=[r for r in valid if r.get('authenticity',0)>=60 and not is_ad(r)]

# 대상: 냄새(새차 제외) + 공조 + 환기/건강. 미세먼지·필터 제외
KEEP=['냄새_곰팡이_에어컨','냄새_외부유입_흡연','공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림','공기질_환기_내외기','공기질_건강_민감']
target=[r for r in gate4 if r.get('primary_topic') in KEEP]
print(f"Gate4 clean 전체 {len(gate4)} → 대상(냄새+공조+환기/건강) {len(target)}건")

def txt(r): return (r.get('title','')+' '+(r.get('full_content','') or '')).lower()

# --- 서브 사전 (멘션 단위 등장 여부) ---
SMELL_TYPE={
 '곰팡이·쉰내':['곰팡이','쿰쿰','퀴퀴','쉰내','쉬내','꿉꿉','퀘퀘','쾌쾌','시큼','걸레냄새','꼬릿'],
 '담배·흡연':['담배','흡연','니코틴','찌든 담배'],
 '매연·외부유입':['매연','배기가스','터널','외부 냄새','바깥 냄새','매캐','도로 냄새'],
 '발·음식·생활':['발냄새','음식냄새','고기냄새','치킨','땀냄새','생활 냄새','찌든'],
 '히터·전자제품(작동)':['히터 냄새','탄 냄새','타는 냄새','전자제품 냄새','먼지냄새','메탈','기름 냄새'],
}
HVAC_ISSUE={
 '냉방 부족(안시원)':['안 시원','안시원','시원하지 않','미지근','냉방 부족','안 차가','더워','에어컨 약'],
 '난방 부족(안따뜻)':['안 따뜻','안따뜻','미지근','히터 약','안 데워','추워','난방 부족'],
 '풍량 약함':['바람 약','풍량 약','바람이 약','약한 바람','풍량이','바람 세기'],
 '온도·좌우 편차':['온도 편차','온도차','좌우 온도','토출 온도','설정 온도','일정하지','들쭉날쭉'],
 '성에·김서림':['성에','김서림','김 서','서리','앞유리 흐림','뿌옇','디포그','습기 제거'],
 '답답·환기부족':['답답','텁텁','탁한','묵직','환기','내기순환','졸','머리 무겁'],
}
TRIGGER={
 '에어컨 켤 때':['에어컨 켜','에어컨을 켜','에어컨 틀','ac 켜','냉방 켜'],
 '히터 켤 때':['히터 켜','히터 틀','난방 켜','난방 틀'],
 '시동 초기':['시동 걸','시동 켜','처음 켜','초반','타자마자','문 열자마자'],
 '장마·여름':['장마','여름','습한 날','비 오','장맛비','무더위'],
 '겨울·환절기':['겨울','추운 날','환절기','아침에'],
 '지하·밀폐주차':['지하주차','지하 주차','밀폐','실내주차'],
}
CAUSE={
 '에바(증발기)':['에바','에바포레이터','증발기','에바쪽'],
 '에어컨필터':['에어컨 필터','에어컨필터','캐빈필터','필터 교체','필터 갈'],
 '매트·시트':['매트','시트','카펫','바닥'],
 '습기·물기':['습기','물기','물끼','축축','눅눅','응축수'],
 '내외기 설정':['내기순환','내기','외기','내외기'],
 '냉매·가스':['냉매','가스','충전','가스 부족'],
}
REMEDY={
 '에바크리닝(업체)':['에바크리닝','에바 클리닝','에바청소'],
 '애프터블로우':['애프터블로우','에프터블로우','after blow','블로워'],
 '필터 교체(셀프)':['필터 교체','필터 갈','필터를 갈','셀프 교체'],
 '히터로 건조':['히터로 말','히터 틀어 말','건조','물기 말'],
 '환기·외기 주행':['환기','창문 열','외기로','문 열'],
 '탈취제·방향제':['탈취제','방향제','스프레이','뿌리'],
 '디포그·성에제거':['디포그','성에 제거','앞유리 버튼','defog'],
}
EMOTION={
 '건강·두통 호소':['두통','머리 아프','머리아프','어지럽','메스꺼','속이','건강','유해','아기','자녀','임산부','호흡기'],
 '체면·민망':['민망','부끄','신경 쓰','창피','손님','조수석','동승','남이 타','태우'],
 '불쾌·스트레스':['불쾌','스트레스','짜증','찝찝','인상','괴로','싫'],
 '체념·포기':['포기','그냥 타','어쩔 수 없','안 틀','그러려니','적응'],
}

def crosscount(dic):
    out=Counter()
    for r in target:
        t=txt(r)
        for k,kws in dic.items():
            if any(w in t for w in kws): out[k]+=1
    return out

def cross_sent(dic):
    out=defaultdict(lambda:Counter())
    for r in target:
        t=txt(r); s=r.get('sentiment','중립')
        for k,kws in dic.items():
            if any(w in t for w in kws): out[k][s]+=1
    return out

dims={'smell_type':SMELL_TYPE,'hvac_issue':HVAC_ISSUE,'trigger':TRIGGER,'cause':CAUSE,'remedy':REMEDY,'emotion':EMOTION}
agg={}
for name,dic in dims.items():
    c=crosscount(dic); cs=cross_sent(dic)
    agg[name]={k:{'n':c[k],'sent':dict(cs[k])} for k in dic}
    print(f"\n=== {name} ===")
    for k in sorted(dic,key=lambda x:-c[x]):
        d=cs[k]; tot=max(sum(d.values()),1)
        print(f"  {k}: {c[k]}건 (부정 {d['부정']/tot*100:.0f}%)")

# 토픽별 감성 (대상 8개)
topic_sent=defaultdict(lambda:Counter())
for r in target: topic_sent[r['primary_topic']][r.get('sentiment','중립')]+=1
agg['topic_sentiment']={t:dict(topic_sent[t]) for t in topic_sent}

# 브랜드 교차
brand_sent=defaultdict(lambda:Counter())
for r in target:
    b=r.get('brand','미상')
    if b!='미상': brand_sent[b][r.get('sentiment','중립')]+=1
agg['brand_sentiment']={b:dict(brand_sent[b]) for b in brand_sent}
agg['target_n']=len(target)

# 대표 인용 (냄새 유형별 + 공조 이슈별)
def reps_for(dic, topics=None):
    out={}
    for k,kws in dic.items():
        cands=[r for r in target if any(w in txt(r) for w in kws)
               and r.get('sentiment') in ('부정','혼합') and len(r.get('full_content','') or '')>150]
        cands.sort(key=lambda r:(r.get('authenticity',0),r.get('word_count',0)),reverse=True)
        out[k]=[{'brand':r.get('brand','미상'),'sentiment':r.get('sentiment'),'auth':r.get('authenticity'),
                 'title':r['title'],'link':r.get('link'),
                 'excerpt':re.sub(r'\s+',' ',r.get('full_content','') or '').strip()[:240]} for r in cands[:4]]
    return out
agg['reps_smell']=reps_for(SMELL_TYPE)
agg['reps_hvac']=reps_for(HVAC_ISSUE)

(DATA/'smell_hvac_deep.json').write_text(json.dumps(agg,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"\n=== 토픽별 감성 (대상) ===")
for t in KEEP:
    d=topic_sent[t]; tot=max(sum(d.values()),1)
    print(f"  {t} (n={sum(d.values())}): 부정 {d['부정']/tot*100:.0f}% / 혼합 {d['혼합']/tot*100:.0f}% / 긍정 {d['긍정']/tot*100:.0f}%")
print(f"\n저장: {DATA/'smell_hvac_deep.json'}")
