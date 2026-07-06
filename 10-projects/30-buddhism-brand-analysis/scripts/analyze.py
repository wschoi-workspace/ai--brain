# -*- coding: utf-8 -*-
"""3군 멘션 분석 — 토픽×감성·진정성·포지셔닝"""
import json, collections
BASE='/Users/choi_ai/do-better-workspace/10-projects/30-buddhism-brand-analysis'
data=json.load(open(BASE+'/data/naver-raw.json',encoding='utf-8'))

TOPICS={
 '수행·명상':['명상','수행','참선','마음챙김','108배','기도','선명상','템플'],
 '전통·역사':['전통','역사','문화재','단청','불상','고찰','천년','유물'],
 'F&B·웰니스':['사찰음식','발우','차','다도','비건','웰니스','힐링','채식','디톡스'],
 '공동체·위로':['위로','공동체','함께','관계','치유','평화','쉼','마음의','연결'],
 '힙·현대화':['힙','mz','뉴진','트렌디','감성','인스타','굿즈','핫플','요즘','젊'],
 '고루·접근성':['고루','올드','촌스','지루','어렵','딱딱','고리타분','문턱','낯설'],
 '불신·상업화':['상업','장사','논란','비판','실망','거부감','부담','돈벌'],
}
POS=['좋','행복','감동','위로','힐링','추천','평화','만족','편안','아름','뜻깊','감사','최고','매력','인생','진심','특별','새롭','설레','즐거']
NEG=['싫','별로','실망','지루','불편','어렵','거부','촌스','고루','논란','비판','부담','아쉽','낯설','지침']
EXP=['다녀','가봤','해봤','후기','체험','직접','경험','방문','참여','먹어','느꼈','했어','갔다','봤어']
PROMO=['문의','예약','신청','할인','이벤트','협찬','광고','공식','상담','수강','등록']

def analyze(items):
    n=len(items) or 1
    topic={k:0 for k in TOPICS}; pos=neg=neu=exp=promo=0
    for it in items:
        t=(it['title']+' '+it['desc']).lower()
        for k,kws in TOPICS.items():
            if any(w in t for w in kws): topic[k]+=1
        p=sum(w in t for w in POS); ng=sum(w in t for w in NEG)
        if p>ng: pos+=1
        elif ng>p: neg+=1
        else: neu+=1
        if any(w in t for w in EXP): exp+=1
        if any(w in t for w in PROMO): promo+=1
    tp={k:round(v/n*100,1) for k,v in topic.items()}
    # 포지셔닝 좌표
    modern=(tp['힙·현대화']+tp['F&B·웰니스'])
    trad=(tp['전통·역사']+tp['고루·접근성'])
    life=(tp['F&B·웰니스']+tp['힙·현대화'])
    relig=(tp['수행·명상']+tp['공동체·위로'])
    x_modern=round(modern/(modern+trad+0.01)*100,1)   # 0 전통 ~ 100 현대
    y_life=round(life/(life+relig+0.01)*100,1)         # 0 종교 ~ 100 라이프스타일
    return {'n':len(items),'topics':tp,
            'pos':round(pos/n*100,1),'neg':round(neg/n*100,1),'neu':round(neu/n*100,1),
            'exp':round(exp/n*100,1),'promo':round(promo/n*100,1),
            'auth':round((exp/n*100)*0.6 + (100-promo/n*100)*0.4,1),  # 진정성 근사
            'pos_neg_ratio':round(pos/(neg or 1),1),
            'x_modern':x_modern,'y_life':y_life}

res={g:analyze(v) for g,v in data.items()}
json.dump(res,open(BASE+'/data/analysis.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# 요약 출력
print('GROUP        N    긍정%  부정%  P/N   경험%  진정성  현대성  라이프')
for g,r in res.items():
    print(f"{g:10} {r['n']:5} {r['pos']:5}  {r['neg']:5}  {r['pos_neg_ratio']:4}  {r['exp']:5}  {r['auth']:5}  {r['x_modern']:5}  {r['y_life']:5}")
print('\n불교 토픽 분포:')
for k,v in sorted(res['불교']['topics'].items(),key=lambda x:-x[1]): print(f'  {k}: {v}%')
