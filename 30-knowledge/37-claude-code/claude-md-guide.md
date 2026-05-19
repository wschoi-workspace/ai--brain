# CLAUDE.md - Source of Truth

> **Source**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)
> **Updated**: 2026-04-04 (v2.1.92)
> **Purpose**: CLAUDE.md 작성 시 유일한 참조 문서

---

## 1. 개요

CLAUDE.md는 Claude Code가 세션 시작 시 자동 로드하는 설정 파일. 프로젝트 컨텍스트, 작업 규칙, 코드 스타일을 정의.

---

## 2. 전체 계층 구조 (Hierarchy)

Claude Code는 다음 순서로 메모리를 로드 (모두 병합됨):

| 우선순위 | 위치 | 용도 |
|---------|------|------|
| 1 (최상위) | Managed Policy | 조직 전사 강제 규칙 |
| 2 | `~/.claude/CLAUDE.md` | 개인 전역 설정 |
| 3 | `./CLAUDE.md` 또는 `./.claude/CLAUDE.md` | 프로젝트 설정 |
| 4 | `./.claude/rules/*.md` | 프로젝트 규칙 (자동 로드) |
| 5 | `~/.claude/rules/*.md` | 개인 전역 규칙 (자동 로드) |
| 6 | `./CLAUDE.local.md` | 로컬 전용 (gitignore 권장) |
| 7 | Auto Memory | 세션 간 자동 학습 기록 |

### Managed Policy (조직 전사)

조직 IT/DevOps가 관리하는 최상위 규칙. 개인 사용자가 변경 불가.

| OS | 경로 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/CLAUDE.md` |
| Linux | `/etc/claude-code/CLAUDE.md` |
| Windows | `C:\Program Files\ClaudeCode\CLAUDE.md` |

MDM, Group Policy, Ansible 등으로 배포.

---

## 3. Auto Memory (v2.1.32, 신규)

Claude가 세션 작업 중 자동으로 패턴, 명령어, 선호도를 기록하는 시스템.

### 저장 위치

```
~/.claude/projects/<project>/memory/
├── MEMORY.md           # 인덱스 (매 세션 첫 200줄 자동 로드)
├── debugging.md        # 토픽별 상세 노트
└── api-conventions.md  # Claude가 자동 생성
```

- `<project>`는 git 저장소 루트에서 파생
- git worktree는 별도 디렉토리
- git 외부는 작업 디렉토리 기준

### 동작

- **세션 시작**: `MEMORY.md` 첫 200줄만 자동 로드
- **토픽 파일**: startup 미로드, Claude가 필요할 때 on-demand 읽기
- **기록 방식**: Claude가 작업 중 자동 기록 또는 직접 지시 ("remember that we use pnpm")

### 제어

```bash
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1  # 비활성화
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0  # 활성화
```

`/memory` 커맨드로 파일 선택기 열기 가능 (CLAUDE.md + Auto Memory 포함).

### Worktree 간 공유 (v2.1.63)

프로젝트 설정과 auto memory가 같은 git 저장소의 모든 worktree에서 공유됨.

### 커스텀 메모리 디렉토리 (v2.1.74)

```json
{
  "autoMemoryDirectory": "/path/to/custom/memory"
}
```

`settings.json`에서 auto-memory 저장 위치를 변경 가능.

### 메모리 파일 타임스탬프 (v2.1.75)

메모리 파일에 last-modified 타임스탬프가 추가되어, Claude가 최신/오래된 메모리를 구분 가능.

### MEMORY.md 크기 제한 (v2.1.83)

`MEMORY.md` 인덱스가 200줄 제한에 더해 **25KB 크기 제한**도 추가됨. 둘 중 먼저 도달하는 기준으로 잘림.

---

## 4. @import 문법

외부 파일을 참조하여 CLAUDE.md를 모듈화:

```markdown
@30-knowledge/37-claude-code/skills-guide.md
@./docs/coding-standards.md
@~/.claude/my-project-instructions.md
```

### 규칙

- 상대 경로 또는 절대 경로 사용 가능
- 참조된 파일은 컨텍스트에 자동 포함
- Code span/code block 내 `@`는 import 처리 안 됨
- **Recursive import 최대 깊이: 5 hops**
- 외부 import 포함 프로젝트 첫 실행 시 **승인 다이얼로그** 표시
- 바이너리 파일(이미지, PDF)은 자동 제외

### HTML 주석 처리 (v2.1.72)

CLAUDE.md 내 HTML 주석(`<!-- ... -->`)은 자동 주입 시 Claude에게 숨겨짐. Read 도구로 직접 읽을 때는 보임. 내부 메모를 Claude에게 노출하지 않으면서 유지 가능.

### Worktree 환경 권장 패턴

```markdown
# CLAUDE.local.md에서 home directory import로 공유
@~/.claude/my-project-instructions.md
```

worktree마다 `CLAUDE.local.md`가 별도 존재하므로 home directory import 활용.

---

## 5. .claude/rules/ 자동 로드

`.claude/rules/` 내 모든 `.md` 파일 자동 로드. 서브디렉토리 재귀 탐색 지원.

```
.claude/
├── CLAUDE.md
├── rules/
│   ├── git.md
│   ├── security.md
│   ├── frontend/
│   │   └── react.md
│   └── backend/
│       └── api.md
└── settings.json
```

조건부 규칙은 [[rules-guide]] 참조.

---

## 6. --add-dir + CLAUDE.md 로딩 (v2.1.20)

`--add-dir`로 추가된 디렉토리의 CLAUDE.md와 rules도 로드 가능:

```bash
CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1 claude --add-dir ../shared-config
```

로드 대상: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`

기본값은 비활성화. 환경변수 설정 필요.

---

## 7. 권장 포함 내용

### 필수

1. **프로젝트 개요**: 목적, 기술 스택
2. **폴더 구조**: 주요 디렉토리 설명
3. **코딩 규칙**: 스타일 가이드, 네이밍 컨벤션
4. **작업 규칙**: 파일 작업, Git, 보안 규칙

### 선택

- 사용자 프로필 / 작업 스타일
- 도구 설정 (MCP, 외부 도구)
- 자주 쓰는 명령어

---

## 8. settings.json과의 관계

| 항목 | CLAUDE.md | settings.json |
|------|-----------|---------------|
| 프로젝트 지침 | O | X |
| 코딩 스타일 | O | X |
| 도구 권한 | X | O |
| 모델 설정 | X | O |
| 환경 변수 | X | O |

**원칙**: 지침은 CLAUDE.md, 설정은 settings.json

---

## 9. 작성 팁

### 간결하게 유지

- 목표: 150줄 이하
- 상세 내용은 @import 또는 rules/ 활용
- 반복 방지: 한 곳에만 정의

### 명확한 규칙

```markdown
# Good
- **커밋 전**: `npm test` 실행 필수

# Bad
- 커밋 전에 테스트를 실행하면 좋을 것 같아요
```

### 주의사항

1. 민감정보 제외 (API 키, 비밀번호 절대 금지)
2. 경로 일관성 (팀 공유 시 상대 경로 권장)
3. CLAUDE.local.md는 .gitignore에 추가
4. 정기적으로 프로젝트 변화에 맞춰 갱신

### 알려진 수정

- **(v2.1.90)** 도구 호출 중 CLAUDE.md 자동 로드 시 축소된 search/read 요약 배지가 fullscreen 스크롤백에서 여러 번 표시되던 버그 수정
- **(v2.1.88)** 긴 세션에서 중첩 CLAUDE.md 파일이 수십 번 재주입되는 버그 수정
- **(v2.1.86)** Read 도구가 compact line-number 포맷 사용 + 변경 없는 재읽기 중복 제거 (토큰 절약)

---

## Sources

- [Manage Claude's memory](https://code.claude.com/docs/en/memory)
- [Claude Code Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)

## Related

- [[rules-guide]] - .claude/rules/ 상세 가이드
- [[skills-guide]] - Skills 시스템 가이드
- [[subagents-guide]] - Subagent 가이드

---

## Update History

- **2026-04-04**: v2.1.90~2.1.92 변경사항 반영
  - CLAUDE.md 자동 로드 시 축소 배지 다중 표시 수정 (v2.1.90)
  - `forceRemoteSettingsRefresh` 정책: 원격 managed settings 강제 갱신, 실패 시 종료 (v2.1.92)
  - `managed-settings.d/` drop-in과 관련된 조직 정책 강화
- **2026-03-31**: v2.1.79~2.1.88 변경사항 반영
  - `MEMORY.md` 25KB 크기 제한 추가 (v2.1.83)
  - 중첩 CLAUDE.md 재주입 버그 수정 (v2.1.88)
  - Read 도구 compact format + 중복 제거 (v2.1.86)
- **2026-03-18**: v2.1.51~2.1.78 변경사항 반영
  - Worktree 간 프로젝트 설정/auto memory 공유 (v2.1.63)
  - `autoMemoryDirectory` 설정 (v2.1.74)
  - 메모리 파일 last-modified 타임스탬프 (v2.1.75)
  - HTML 주석 자동 주입 시 숨김 처리 (v2.1.72)
  - `InstructionsLoaded` 훅 이벤트 (v2.1.69)
- **2026-02-22**: 전면 갱신 (source of truth 목적)
  - Auto Memory 시스템 신규 섹션 (v2.1.32)
  - Managed Policy 계층 추가 (최상위)
  - Hierarchy 표 전면 수정 (7단계)
  - --add-dir + CLAUDE.md 로딩 (v2.1.20)
  - Import 안전 동작 (승인 다이얼로그, 5 hops 제한)
  - MCP 섹션 제거 (별도 문서로 분리)
- **2026-01-19**: 초기 작성
