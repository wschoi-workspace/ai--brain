#!/usr/bin/env python3
"""완료 루프 단위 테스트 (vNext Phase 1, 2026-08).

실행: python3 00-system/02-scripts/tests/test_completion_loop.py
의존성 없음(표준 라이브러리만) — 맥미니 3.9.6에서 그대로 돌아간다.

가장 중요한 것은 §3 하위호환이다. 시트 컬럼을 O→W로 늘렸는데 기존 15칸 행이
깨지면 전 직원의 분장이 한 번에 죽는다. 마이그레이션 없이 확장한다는 설계의
전제가 바로 이 테스트다.

§6 회귀도 같은 무게다 — 상태 어휘·전이 테이블 불변이 Phase 1의 계약이므로,
진행률 층을 얹으면서 그것을 건드렸는지 여기서 잡는다.
"""
import os
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shared.assign_sheet as AS    # noqa: E402
import shared.completion as CP      # noqa: E402
import shared.status as ST          # noqa: E402

FAIL = []
N = 0


def ck(cond, label):
    global N
    N += 1
    if not cond:
        FAIL.append(label)
        print("  ✗ %s" % label)
    else:
        print("  ✓ %s" % label)


# 환경변수가 켜져 있으면 mode 테스트가 오염된다
os.environ.pop(CP.ENV_MODE_KEY, None)
os.environ.pop(ST.ENV_MODE_KEY, None)

BEFORE = date(2026, 11, 1)   # GRACE_END 이전
AFTER = date(2026, 12, 1)    # GRACE_END 이후


print("§1 effective_progress — 실입력이 상태 사다리보다 우선")
ck(ST.effective_progress({"status": "진행중"}) == 50,
   "① P열 비면 종전 사다리 그대로 (진행중=50) — 무마이그레이션 보장")
ck(ST.effective_progress({"status": "진행중", "progress": "60"}) == 60,
   "② 실입력 60%가 사다리 50을 이긴다")
ck(ST.effective_progress({"status": "미착수", "progress": "20"}) == 20,
   "③ 상태는 미착수여도 20% — 원안의 Planning을 상태 추가 없이 흡수")
ck(ST.effective_progress({"status": "완료", "progress": "70"}) == 100,
   "④ 완료는 실입력이 무엇이든 100 — 닫힌 업무가 롤업을 갉지 않게")
ck(ST.effective_progress({"status": "승인", "progress": ""}) == 100, "⑤ 승인도 100")
ck(ST.effective_progress({"status": "진행중", "progress": "0"}) == 0,
   "⑥ 명시적 0%는 미입력과 다르다 (0으로 뭉개지 않음)")
ck(ST.effective_progress({"status": "진행중", "progress": "abc"}) == 50,
   "⑦ 형식 오류는 미입력 취급 → 사다리 폴백 (fail-open)")
ck(ST.effective_progress({"status": "진행중", "progress": "150"}) == 100, "⑧ 상한 클램프")
ck(ST.effective_progress({"status": "진행중", "progress": "-5"}) == 0, "⑨ 하한 클램프")
ck(ST.effective_progress({}) == 0, "⑩ 빈 dict도 죽지 않는다")
ck(ST.effective_progress(None) == 0, "⑪ None도 죽지 않는다")
ck(ST.norm_progress("") is None and ST.norm_progress("0") == 0,
   "⑫ norm_progress는 None(미입력)과 0(입력됨)을 구분한다")
ck(ST.norm_progress("60%") == 60, "⑬ '%' 붙은 입력 허용 (사람이 그렇게 친다)")

print("\n§2 completion.check — grace 통과 / strict 차단 / 킬스위치")
DONE_BARE = {"status": "완료"}
DONE_FULL = {"status": "완료", "done_at": "2026-08-03", "done_by": "홍길동",
             "deliverable": "https://drive.google.com/x", "report_to": "윤혜정",
             "reported_at": "2026-08-03T10:00:00"}
ok, miss = CP.check(DONE_BARE, BEFORE)
ck(ok and miss, "① grace: 산출물 없어도 통과하되 사유는 남는다 (shadow 실측용)")
ok, miss = CP.check(DONE_BARE, AFTER)
ck((not ok) and "최종 산출물" in miss, "② strict: 산출물 없으면 차단")
ok, miss = CP.check(DONE_FULL, AFTER)
ck(ok and not miss, "③ strict: 5요소 갖추면 통과")
ok, _ = CP.check({"status": "완료", "result": "최종 제안서 PDF 전달"}, AFTER)
ck(ok, "④ strict: G열(결과물)만 있어도 통과 — 살아 있는 컬럼을 깨지 않는다")
os.environ[CP.ENV_MODE_KEY] = "off"
ok, _ = CP.check(DONE_BARE, AFTER)
ck(ok, "⑤ env=off 킬스위치 — plist 1줄로 즉시 롤백")
os.environ[CP.ENV_MODE_KEY] = "shadow"
ok, miss = CP.check(DONE_BARE, AFTER)
ck(ok and miss, "⑥ env=shadow — 통과시키고 사유만 기록")
os.environ.pop(CP.ENV_MODE_KEY, None)
ck(CP.current_mode(BEFORE) == "grace" and CP.current_mode(AFTER) == "strict",
   "⑦ 날짜 기반 자동 전환 (GRACE_END %s)" % CP.GRACE_END)
ck(CP.GRACE_END.month != ST.ENFORCE_FROM.month,
   "⑧ GRACE_END가 status.ENFORCE_FROM과 다른 달 — 같은 주에 두 규칙이 조여지면 원인 분리 불가")

print("\n§3 하위호환 — 15칸 구행이 안전하게 파싱되는가  ★ 가장 중요")
OLD_ROW = ["2026-07-01", "봉은사", "기획팀", "홍길동", "마스터플랜 검토",
           "2026-07-10", "", "진행중", "", "일반", "bongeunsa-2026-15", "최원석",
           "meeting", "bongeunsa-2026-15|20260701-120000", "기획"]
a = AS.parse_row(OLD_ROW, 2, ST)
ck(a["task"] == "마스터플랜 검토" and a["status"] == "진행중",
   "① 구행의 A~O가 종전과 동일하게 읽힌다")
ck(all(a[k] == "" for k in ("progress", "eta", "progress_at", "done_at",
                            "done_by", "deliverable", "report_to", "reported_at")),
   "② P~W 8칸이 전부 '' — 예외 없이")
ck(a["progress_pct"] == 50, "③ progress_pct가 상태 사다리로 채워진다")
ck(len(AS.parse_row([], 2, ST)) == len(a), "④ 완전 빈 행도 같은 키 집합을 반환")
ck(AS.parse_row(["2026-07-01", "x"], 2, ST)["status"] == "미착수",
   "⑤ 2칸짜리 극단 구행도 죽지 않는다")
NEW_ROW = OLD_ROW + ["60", "2026-08-08", "2026-08-03T09:00:00",
                     "", "", "", "", ""]
b = AS.parse_row(NEW_ROW, 3, ST)
ck(b["progress"] == "60" and b["eta"] == "2026-08-08", "⑥ 신행의 P·Q가 읽힌다")
ck(b["progress_pct"] == 60, "⑦ 신행은 실입력이 반영된다")
ck(AS.COLS == 23 and AS.READ_RANGE.endswith("A2:W5000"), "⑧ COLS·READ_RANGE 확장 확인")

print("\n§4 autofill — 폴백 순서와 '덮지 않기'")
f = CP.autofill({"status": "완료", "assignee": "홍길동"}, actor="김철수",
                now=datetime(2026, 8, 3, 14, 0), report_to="윤혜정")
ck(f["done_at"] == "2026-08-03", "① 완료일 = 오늘")
ck(f["done_by"] == "김철수", "② 완료자 = 버튼 누른 사람 (담당자와 다를 수 있다)")
ck(f["report_to"] == "윤혜정", "③ 보고 대상 = approval.next_step() 결과 주입")
f = CP.autofill({"status": "완료"}, actor="김철수", now=datetime(2026, 8, 3, 7, 30))
ck(f["done_at"] == "2026-08-02", "④ 09시 이전은 전날 귀속 — 봇 규칙과 동일")
f = CP.autofill({"status": "완료", "result": "G열 결과물"}, actor="김철수",
                report_output="보고 산출물")
ck(f["deliverable"] == "G열 결과물", "⑤ 산출물 폴백: G열이 보고 output보다 앞")
f = CP.autofill({"status": "완료"}, actor="김철수", report_output="보고 산출물")
ck(f["deliverable"] == "보고 산출물", "⑥ G열 없으면 일일보고 output")
f = CP.autofill({"status": "완료", "deliverable": "사람이 적은 링크", "result": "G"},
                actor="김철수", report_output="보고")
ck("deliverable" not in f, "⑦ 이미 있는 값은 건드리지 않는다 — 배치가 사람 입력을 덮지 않게")
f = CP.autofill({"status": "완료", "assignee": "홍길동"}, actor="")
ck(f["done_by"] == "홍길동", "⑧ actor 없으면 담당자로 폴백")

print("\n§5 progress_band 경계값")
for pct, want in ((0, "Not Started"), (1, "Planning"), (49, "Planning"),
                  (50, "In Progress"), (79, "In Progress"), (80, "Review"),
                  (99, "Review"), (100, "Done")):
    ck(ST.progress_band(pct) == want, "① %d%% → %s" % (pct, want))
ck(ST.progress_band("") == "Not Started", "② 미입력은 Not Started")

print("\n§6 회귀 — 상태 어휘·전이 테이블 불변이 Phase 1의 계약")
ck(ST.ASSIGN_STATES == ("미착수", "진행중", "검토중", "승인대기", "보류",
                        "완료", "승인", "패스", "취소", "미실행종료", "일정경과종료",
                        "다른업무로통합", "삭제"), "① ASSIGN_STATES 13종 불변")
ck(ST.ASSIGN_TO_PROGRESS == {"미착수": 0, "진행중": 50, "검토중": 70, "승인대기": 90,
                             "보류": 30, "완료": 100, "승인": 100},
   "② ASSIGN_TO_PROGRESS 값 불변 (P열이 비면 이 사다리가 그대로 쓰인다)")
ck(ST.can_transition("검토중", "진행중")[0], "③ 사람 반려 여전히 허용")
ck(not ST.can_transition("검토중", "진행중", "weekly-auto")[0], "④ 자동 되돌림 여전히 차단")
ck("report-followup" in ST.CONFIRMED_SOURCES and "report-sync" in ST.CONFIRMED_SOURCES,
   "⑤ followup은 verify_row 2회를 통과하므로 사람 취급")
ck(ST.source_class("report-followup") == "human", "⑥ followup이 auto로 분류되지 않는다")
ck(AS.REQUIRED_FIELDS == (("deadline", "마감일"), ("project", "프로젝트")),
   "⑦ 등록 시 필수 항목은 늘리지 않았다 — 입력 부담 불변")

print("\n§7 completion_missing_rows — 완료인데 근거 없는 행만 뜬다")
rows = [{"status": "완료", "assignee": "A", "row": 2},
        {"status": "진행중", "assignee": "A", "row": 3},
        {"status": "승인", "assignee": "B", "row": 4, "done_at": "2026-08-01",
         "done_by": "B", "result": "산출물", "report_to": "리더",
         "reported_at": "2026-08-01T10:00:00"},
        {"status": "삭제", "assignee": "A", "row": 5}]
q = AS.completion_missing_rows(rows, ST, CP)
ck([x["row"] for x in q] == [2], "① 완료·근거없음만 (진행중·완결·삭제 제외)")
ck("최종 산출물" in q[0]["missing"], "② 무엇이 비었는지 라벨로 알려준다")
ck([x["row"] for x in AS.completion_missing_rows(rows, ST, CP, assignee="B")] == [],
   "③ 담당자 필터 동작")

print("\n" + "=" * 60)
if FAIL:
    print("실패 %d / %d" % (len(FAIL), N))
    for f in FAIL:
        print("  - %s" % f)
    sys.exit(1)
print("전체 통과 %d / %d" % (N, N))
