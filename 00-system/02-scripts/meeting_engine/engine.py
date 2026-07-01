"""Meeting Engine core - 6종 리포트 생성 + 프로젝트 컨텍스트 수집.

1.0 process_meeting.py의 핵심 로직을 2.0 봇에서 async로 호출 가능하게 래핑.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from meeting_engine import client as mc
from meeting_engine.prompts import (
    meeting_report,
    todo_assignment,
    strategy_report,
)
from meeting_engine.prompts import decisions as decisions_prompt
from meeting_engine.prompts import progress_log as progress_prompt
from meeting_engine.prompts import master_sheet as master_prompt
from meeting_engine.source_detector import detect_source_type, SOURCE_LABELS

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_MAX_CONTEXT_CHARS = 8000

# 리포트 정의 (1.0 그대로)
BASIC_REPORTS = {
    "meeting": {
        "prompt_module": meeting_report,
        "template": "meeting_report.md.j2",
        "output_mode": "new_file",
    },
    "todo": {
        "prompt_module": todo_assignment,
        "template": "todo_assignment.md.j2",
        "output_mode": "append",
        "target_file": "03_todos.md",
    },
    "strategy": {
        "prompt_module": strategy_report,
        "template": "strategy_report.md.j2",
        "output_mode": "append",
        "target_file": "05_strategy_report.md",
    },
}

CONTEXT_REPORTS = {
    "decisions": {
        "prompt_module": decisions_prompt,
        "template": "decisions.md.j2",
        "output_mode": "append",
        "target_file": "02_decisions.md",
    },
    "progress": {
        "prompt_module": progress_prompt,
        "template": "progress_log.md.j2",
        "output_mode": "append",
        "target_file": "06_progress_log.md",
    },
    "master": {
        "prompt_module": master_prompt,
        "template": "master_sheet.md.j2",
        "output_mode": "overwrite",
        "target_file": "PROJECT_MASTER.md",
    },
}

ALL_REPORTS = {**BASIC_REPORTS, **CONTEXT_REPORTS}
REPORT_ORDER = ["meeting", "todo", "strategy", "decisions", "progress", "master"]


def _read_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "cp949"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ""


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _append_to_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if path.exists():
        existing = _read_file(path)
    combined = existing.rstrip() + "\n\n" + content.strip() + "\n"
    path.write_text(combined, encoding="utf-8")


def collect_project_context(project_dir: Path) -> str:
    """프로젝트의 이전 결정사항, Todo, 전략 리포트를 수집."""
    context_parts = []
    for filename, label in [
        ("02_decisions.md", "이전 결정사항"),
        ("03_todos.md", "이전 Todo"),
        ("05_strategy_report.md", "이전 전략 리포트"),
    ]:
        filepath = project_dir / filename
        if filepath.exists():
            content = _read_file(filepath)
            lines = content.split("\n")
            data_lines = [
                ln for ln in lines
                if not ln.strip().startswith("<!--")
                and not ln.strip().startswith("-->")
                and not ln.strip().startswith("프로젝트 전체")
                and not ln.strip().startswith("각 회의에서")
            ]
            cleaned = "\n".join(data_lines).strip()
            if cleaned and len(cleaned) > 50:
                context_parts.append(f"### {label}\n\n{cleaned}")

    combined = "\n\n".join(context_parts)
    if len(combined) > _MAX_CONTEXT_CHARS:
        combined = "...(이전 내용 생략)...\n" + combined[-_MAX_CONTEXT_CHARS:]
    return combined


def generate_single_report(
    report_type: str,
    meeting_text: str,
    source_file_name: str,
    project_dir: Path | None,
    today: str,
    project_context: str = "",
    source_type: str = "mtg",
) -> dict:
    """단일 리포트 생성. GPT 호출 + Jinja2 렌더 + 파일 저장. data dict 반환."""
    config = ALL_REPORTS[report_type]
    prompt_module = config["prompt_module"]

    needs_context = report_type in CONTEXT_REPORTS
    has_source_param = report_type in ("meeting", "todo")

    if needs_context and project_context:
        system_prompt, user_prompt = prompt_module.build_prompt(
            meeting_text, previous_context=project_context
        )
    elif needs_context:
        system_prompt, user_prompt = prompt_module.build_prompt(
            meeting_text, previous_context=""
        )
    elif has_source_param:
        system_prompt, user_prompt = prompt_module.build_prompt(
            meeting_text, source_type=source_type
        )
    else:
        system_prompt, user_prompt = prompt_module.build_prompt(meeting_text)

    data = mc.call_openai(system_prompt, user_prompt)
    if not data:
        logger.error(f"[meeting] {report_type} GPT returned empty")
        return {}

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
    template = env.get_template(config["template"])
    rendered = template.render(
        date=today,
        source_file=source_file_name,
        data=data,
    )

    if project_dir:
        if config["output_mode"] == "new_file":
            output_path = project_dir / "01_meeting_logs" / f"{today}_{report_type}-report.md"
            _write_file(output_path, rendered)
        elif config["output_mode"] == "overwrite":
            output_path = project_dir / config["target_file"]
            _write_file(output_path, rendered)
        else:
            output_path = project_dir / config["target_file"]
            _append_to_file(output_path, rendered)
        logger.info(f"[meeting] {report_type} saved: {output_path}")

    return data


def process_all_reports(
    meeting_text: str,
    project_dir: Path,
    source_file_name: str = "telegram",
) -> dict[str, dict]:
    """6종 리포트 전체 생성. {report_type: data_dict} 반환."""
    today = date.today().isoformat()
    source_type = detect_source_type(meeting_text)
    project_context = collect_project_context(project_dir)

    results = {}
    for report_type in REPORT_ORDER:
        try:
            data = generate_single_report(
                report_type, meeting_text, source_file_name,
                project_dir, today, project_context, source_type,
            )
            results[report_type] = data
        except Exception as e:
            logger.exception(f"[meeting] {report_type} failed: {e}")
            results[report_type] = {"error": str(e)}

    return {
        "source_type": source_type,
        "source_label": SOURCE_LABELS.get(source_type, source_type),
        "today": today,
        "project": project_dir.name,
        "context_chars": len(project_context),
        "reports": results,
    }


def format_meeting_summary(result: dict) -> str:
    """텔레그램에 보낼 요약 메시지 생성."""
    reports = result.get("reports", {})
    lines = [
        f"[ARISA Meeting Report]",
        f"{result.get('source_label', '')} | {result['today']} | {result['project']}",
        "",
    ]

    # Meeting Report 요약
    mr = reports.get("meeting", {})
    if mr.get("meeting_purpose"):
        lines.append(f"# {mr['meeting_purpose']}")
        lines.append("")

    discussions = mr.get("key_discussions", [])
    if discussions:
        lines.append("-- 핵심 논의 --")
        for d in discussions[:5]:
            conclusion = d.get("conclusion", "")
            lines.append(f"  {d.get('topic', '')}: {conclusion}")
        lines.append("")

    # Decisions 요약
    dec = reports.get("decisions", {})
    new_decs = dec.get("new_decisions", [])
    if new_decs:
        lines.append(f"-- 신규 결정 {len(new_decs)}건 --")
        for d in new_decs[:3]:
            lines.append(f"  {d.get('decision', '')}")
        lines.append("")

    # Todo 요약
    td = reports.get("todo", {})
    todos = td.get("todos", [])
    if todos:
        high = [t for t in todos if t.get("priority") == "high"]
        lines.append(f"-- Todo {len(todos)}건 (High {len(high)}건) --")
        for t in high[:3]:
            lines.append(f"  [{t.get('assignee', '?')}] {t.get('task', '')}")
        lines.append("")

    # Strategy 한줄
    sr = reports.get("strategy", {})
    if sr.get("strategic_significance"):
        lines.append(f"-- 전략 --")
        lines.append(f"  {sr['strategic_significance'][:200]}")
        lines.append("")

    # Progress health
    pr = reports.get("progress", {})
    health = pr.get("project_health", "")
    if health:
        icon = {"green": "G", "yellow": "Y", "red": "R"}.get(health, "?")
        lines.append(f"프로젝트 상태: [{icon}] {pr.get('health_reason', '')}")

    ctx = result.get("context_chars", 0)
    if ctx:
        lines.append(f"\n(이전 컨텍스트 {ctx}자 참조)")

    lines.append("\n6종 .md 리포트 저장 완료")
    return "\n".join(lines)
