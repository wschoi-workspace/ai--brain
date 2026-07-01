#!/bin/bash
# 대시보드 빌드 — 템플릿·포트폴리오 재생성 + 서버 시드(_data) 갱신.
# 이관 가능: 스크립트 위치 기준으로 동작(어느 사용자/경로에서도 OK).
# 사용자(PIN)·시드 프로젝트를 바꾼 뒤 실행. 서버는 매 요청마다 파일을 읽으므로 재시작 불필요.
# (기존 _data/projects/*.json = PM이 수정한 실데이터는 보존됨)
set -e
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"          # .../00-system/02-scripts
cd "$SCRIPTS"
PY="$(command -v python3 || echo /usr/bin/python3)"
echo "▶ 기획 템플릿 생성..."
"$PY" generate-project-brief-template.py >/dev/null
echo "▶ 포트폴리오 + 서버 시드(_data) 생성..."
"$PY" generate-portfolio.py
echo "✅ 완료. 서버가 떠 있으면 직원들은 새로고침만 하면 반영됩니다."
echo "   데이터: ../01-templates/_data/  (★ 정기 백업 권장 — 실프로젝트 데이터)"
