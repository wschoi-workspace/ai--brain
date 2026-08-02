"""ARISA 공유 코어 (Phase 1).

봇·배치가 각자 복붙하던 기능 배관을 단일 출처로 모은다.
도메인 로직(프롬프트·섹션 정의)은 절대 여기로 옮기지 않는다 — 각 봇의 차별성이므로.

모듈:
  logging   — TokenRedactingFilter, setup_logging
  normalize — normalize_name / team_of / normalize_date (+ DEFAULT_NAME_ALIASES)
  employee  — load_employees, EmployeeRegistry
  gws       — values_get(읽기), append_to_sheet(쓰기)
  llm       — LLMClient(call_json / call_text, 재시도 내장)
  telegram  — create_telegram_app, safe_error_handler
  decision  — save_decision_log (Engine D: Decision Log 축적)

이후 확장(Phase 1 이후 추가분 중 상태·완료 축):
  status      — 상태 어휘·전이 그래프·진행률(effective_progress/progress_band)·신호등
  assign_sheet— 주간분장 컬럼 SSOT (A~O 원본 + P~W 진행/완료 블록)
  completion  — 완료 5요소 게이트, grace→strict (report_score와 동형)
"""
