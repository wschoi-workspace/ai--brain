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
"""
