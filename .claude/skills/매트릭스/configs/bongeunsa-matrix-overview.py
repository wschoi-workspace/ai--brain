# -*- coding: utf-8 -*-
"""봉은문화센터 전략 매트릭스 — 6열 개요본

  python3 ../scripts/matrix_gen.py bongeunsa-matrix-overview.py

9열 상세본(bongeunsa-matrix.py)과 **같은 축 판정**을 쓴다. 다른 것은 열 배치뿐이다.

  법적 검토 → Target → Direction → 서비스·컨텐츠 → 비즈니스 모델 → Concept

상세 열(C-1 서비스 116건 · D-1 수익 항목 77개)과 수익모델 10유형을 빼서 한 장에 담는다.
법을 맨 앞에 두는 것이 이 판의 요지다 — 무엇이 가능한지가 먼저 정해지고 나머지가 그 안에서 움직인다.
(9열본은 반대로 법을 맨 뒤 옵션 필터로 뺐다. 파고드는 용도라 법이 흐름을 끊으면 안 되기 때문이다.)

⚠️ 축 판정을 여기서 새로 쓰지 않는다. 고칠 일이 있으면 bongeunsa-matrix.py를 고친다 —
   그러면 두 장이 같이 갱신된다.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# 9열 상세본의 축 판정을 그대로 빌려온다 (SSOT는 저쪽이다)
_M = _load('bg_matrix_axes', os.path.join(HERE, 'bongeunsa-matrix.py'))

NAME = 'strategy-matrix-overview'
OUT = _M.OUT
load = _M.load
ATOM = _M.ATOM

# Direction 블록에는 Target 이름을 멤버로 단다 — 바로 앞 열이 Target이므로 선의 도착점이 된다
_TARGET_LABELS = [t['label'] for t in _M.TARGET_NODES]
_DIRECTION_NODES = [dict(d, members=_TARGET_LABELS) for d in _M.DIRECTION_NODES]

STAGES = [
    dict(id='s1', label='Segment A · 법적 검토', order=0, role='origin', axis='legal',
         note='무엇이 가능한지가 먼저 정해진다 — 유권해석이 수익 천장을 정한다',
         nodes=_M.LEGAL_NODES, kind='item'),
    dict(id='s2', label='Segment B · 조건부 생존군', order=1, role='structure', axis='target',
         note='어떤 전략 선택 아래에서 살아남는가 — 전략 선택축에서 역산한 값이며 방문객 속성이 '
              '아니다. 실측 기반 타겟은 demand-matrix.html',
         nodes=_M.TARGET_NODES, pick=('rare', 2)),
    dict(id='s3', label='Segment C · Direction', order=2, role='structure', axis='dir',
         note='어떤 시설로 규정하는가', nodes=_DIRECTION_NODES, pick='first', kind='group'),
    dict(id='s4', label='Segment D · 서비스·컨텐츠', order=3, role='structure', axis='cat',
         note='116건을 10개 군으로 그룹핑', nodes_fn=_M._cat_nodes, kind='group'),
    dict(id='s5', label='Segment E · 비즈니스 모델', order=4, role='synthesis', axis='biz',
         note='돈 버는 구조로 묶는다', nodes=_M.BIZ_NODES, kind='group', pick='first'),
    dict(id='s6', label='Concept', order=5, role='conclusion', axis='concept',
         note='2026-07-29 대표 확정', nodes=_M.CONCEPT_NODES, kind='card'),
]

# 슬롯은 이 판에 있는 열에만 붙인다 (9열본의 stage id와 다르므로 다시 건다)
# ⚠️ 예전에는 _M.SLOTS[0] / [1:5] 처럼 위치로 참조했다. 9열본의 SLOTS 순서가 바뀌면
#    조용히 엉뚱한 열에 슬롯이 붙었다. id로 찾고, 없으면 즉시 실패한다. (2026-08-02)
def _slot(sid):
    hit = [s for s in _M.SLOTS if s['id'] == sid]
    if not hit:
        raise KeyError(f"SLOTS에 '{sid}'가 없다 — bongeunsa-matrix.py의 SLOTS를 확인할 것")
    return hit[0]

SLOTS = [
    dict(_slot('slot-o2e'), stage='s2'),                # 기업·VIP 세분 → Target
    *[dict(_slot(i), stage='s3')                        # 방향 축 4종 → Direction
      for i in ('slot-c1', 'slot-c5', 'slot-c4', 'slot-loc')],
]

CONCLUSIONS = _M.CONCLUSIONS
WHITESPACE = _M.WHITESPACE

META = dict(
    title='봉은문화센터 — 전략 매트릭스 (개요)',
    subtitle=f'서비스·컨텐츠 {len(_M._SV)}건을 법률·타깃·방향·그룹·BM 축으로 엮어 3대 컨셉까지 · '
             f'배제 7건 제외 · ◻︎ 표시는 자료가 없어 비워둔 슬롯 · 상세는 strategy-matrix.html',
    source=f'{_M.SRC} · BM 10유형은 {_M.RPT} · 3대 컨셉은 {_M.PROG}',
    generated_at='2026-07-31', axis='topic', mode='structure',
    value_note='관계 표시 — 선 굵기에 양의 뜻 없음')
