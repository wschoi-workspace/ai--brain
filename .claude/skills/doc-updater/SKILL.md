---
name: doc-updater
description: Claude Code 공식 문서 업데이트 확인 및 자동 업데이트.
  "문서 업데이트", "CHANGELOG 확인", "doc update", "공식문서 업데이트",
  "Claude Code 변경사항" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebFetch
  - Task
context: fork
---

# Claude Code 공식 문서 자동 업데이트

GitHub CHANGELOG를 확인하고 로컬 문서 및 Skills/Subagents를 업데이트합니다.

## 경로 설정

```yaml
config:
  changelog_url: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
  cache_path: ~/.claude/cache/changelog.md
  version_tracker_path: ~/.claude/cache/doc-versions.json
  official_docs_path: /Users/rhim/Projects/pkm/30-knowledge/37-claude-code/37.00-official-docs/
  skills_path: ~/.claude/skills/
  agents_path: ~/.claude/agents/
```

## 핵심: 2단계 버전 추적

이 스킬은 **두 가지 버전**을 별도로 추적합니다:

1. **changelog_version**: 캐시된 CHANGELOG의 최신 버전 (GitHub와 비교)
2. **docs_synced_version**: 가이드 문서가 실제로 반영된 마지막 CHANGELOG 버전

**업데이트 필요 판단 기준**:
- `changelog_version < GitHub 최신` → 새 CHANGELOG 있음
- `docs_synced_version < changelog_version` → 가이드가 CHANGELOG에 뒤처짐
- 둘 중 하나라도 해당하면 업데이트 진행

## 버전 추적 파일

`~/.claude/cache/doc-versions.json`:
```json
{
  "changelog_version": "2.1.78",
  "docs_synced_version": "2.1.78",
  "last_checked": "2026-03-18",
  "docs": {
    "skills-guide.md": "2.1.78",
    "subagents-guide.md": "2.1.78",
    "claude-md-guide.md": "2.1.78",
    "rules-guide.md": "2.1.78",
    "plugins-guide.md": "2.1.78"
  }
}
```

## 작업 순서

### Step 1: 버전 상태 확인

1. **GitHub에서 최신 CHANGELOG 가져오기**
   ```
   WebFetch: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
   ```

2. **버전 추적 파일 읽기**
   - `~/.claude/cache/doc-versions.json` 읽기
   - 파일이 없으면 `docs_synced_version: "0.0.0"`으로 초기화

3. **업데이트 필요 여부 판단**
   - GitHub 최신 버전 파싱 (`## X.Y.Z` 첫 번째 항목)
   - `changelog_version`과 비교 → 새 CHANGELOG 여부
   - `docs_synced_version`과 비교 → 가이드 동기화 필요 여부
   - **둘 다 동일하면**: "이미 최신 버전입니다" 출력 후 종료
   - **하나라도 다르면**: 계속 진행

### Step 2: 변경사항 분석

`docs_synced_version` 이후의 모든 변경사항을 추출하고 분류:

| 카테고리 | 키워드 | 영향받는 문서 |
|----------|--------|---------------|
| Skills | skill, SKILL.md, allowed-tools, `${CLAUDE_SKILL_DIR}` | skills-guide.md |
| Subagents | agent, subagent, Task tool, SendMessage, worktree | subagents-guide.md |
| CLAUDE.md | memory, CLAUDE.md, @import, rules | claude-md-guide.md |
| Rules | rules/, paths, globs, conditional | rules-guide.md |
| Plugins | plugin, marketplace, `${CLAUDE_PLUGIN_ROOT}` | plugins-guide.md |
| Hooks | hook, PreToolUse, PostToolUse, Stop | 관련 전체 문서 |
| Breaking Changes | BREAKING, deprecated, removed | 모든 문서 |

### Step 3: 로컬 공식 문서 업데이트

업데이트 대상 파일:
- `skills-guide.md` - Skills 시스템
- `subagents-guide.md` - Subagent 가이드
- `claude-md-guide.md` - CLAUDE.md + Auto Memory
- `rules-guide.md` - Rules 가이드
- `plugins-guide.md` - Plugin 시스템

**업데이트 방식:**
1. 각 문서 상단의 `Updated` 날짜 갱신
2. 해당 섹션에 새 기능/변경사항 본문 반영
3. Update History 섹션에 변경 요약 추가
4. 예시 코드가 있으면 최신 문법으로 업데이트

### Step 4: 서브에이전트 호출

변경사항이 Skills 또는 Subagents에 영향을 미치면 서브에이전트 호출:

1. **skill-updater 호출** (Skills 관련 변경 시)
2. **agent-updater 호출** (Subagents 관련 변경 시)

**병렬 실행**: 두 서브에이전트가 독립적이면 병렬로 호출

### Step 5: 캐시 업데이트 및 결과 리포트

1. **CHANGELOG 캐시 갱신**
   - `~/.claude/cache/changelog.md`에 최신 CHANGELOG 저장

2. **버전 추적 파일 갱신**
   - `~/.claude/cache/doc-versions.json` 업데이트
   - `changelog_version` = GitHub 최신 버전
   - `docs_synced_version` = 업데이트 완료된 버전
   - 각 문서별 동기화 버전 기록

3. **결과 리포트 출력**
   ```markdown
   # Doc Updater 실행 완료

   ## 버전 정보
   - 캐시 버전: A.B.C
   - GitHub 최신 버전: X.Y.Z
   - 가이드 동기화 버전: (이전) P.Q.R → (현재) X.Y.Z
   - 확인 시간: YYYY-MM-DD

   ## 업데이트된 가이드 문서
   - [x] skills-guide.md (A.B.C → X.Y.Z)
   - [x] subagents-guide.md (A.B.C → X.Y.Z)
   - [ ] claude-md-guide.md (변경 없음)
   ...

   ## Skills/Agents 업데이트
   - [결과]

   ## 수동 확인 필요
   - [Breaking Changes 등]
   ```

## 에러 처리

| 상황 | 대응 |
|------|------|
| GitHub 접근 실패 | 오프라인 모드로 캐시만 표시 |
| 캐시 파일 없음 | 새로 생성 후 전체 동기화 |
| 버전 추적 파일 없음 | 초기화 (`docs_synced_version: "0.0.0"`) |
| 파싱 실패 | 원본 CHANGELOG 링크 제공 |
| 서브에이전트 실패 | 수동 업데이트 가이드 제공 |

## 주의사항

- 자동 업데이트는 기존 사용자 커스터마이징을 존중
- Breaking Changes는 반드시 사용자에게 알림
- 업데이트 전 현재 상태 백업 권장
- Git commit은 사용자 확인 후 진행
