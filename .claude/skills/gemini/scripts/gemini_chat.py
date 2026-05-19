#!/usr/bin/env python3
"""
Gemini API Chat Script
- chat 모드: Gemini에게 프롬프트를 보내고 응답을 받아 파일로 저장
- review 모드: 기존 파일을 Gemini에게 보내서 피드백 요청
"""

import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# .env 로드
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print(json.dumps({"error": "GEMINI_API_KEY not set"}))
    sys.exit(1)

SAVE_DIR = Path(__file__).parent.parent.parent.parent.parent / "50-resources" / "gemini-feedback"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def call_gemini(prompt: str, system_instruction: str = None) -> dict:
    """Gemini API 호출"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        }
    }

    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return {"success": True, "response": text}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_response(prompt: str, response: str, mode: str, source_file: str = None) -> str:
    """응답을 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"gemini-{mode}-{timestamp}.md"
    filepath = SAVE_DIR / filename

    content = f"""# Gemini {mode.upper()} - {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 모드
{mode}

"""
    if source_file:
        content += f"""## 원본 파일
`{source_file}`

"""

    content += f"""## 프롬프트
{prompt}

## Gemini 응답
{response}
"""

    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: gemini_chat.py <mode> <prompt_or_filepath> [additional_prompt]"}))
        sys.exit(1)

    mode = sys.argv[1]  # "chat" or "review"
    target = sys.argv[2]  # prompt text or file path

    if mode == "chat":
        # 직접 Gemini에게 질문
        result = call_gemini(target)
        if result["success"]:
            saved = save_response(target, result["response"], mode)
            print(json.dumps({
                "success": True,
                "response": result["response"],
                "saved_to": saved
            }, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)

    elif mode == "review":
        # 기존 파일을 Gemini에게 보내서 피드백 요청
        file_path = Path(target)
        if not file_path.exists():
            print(json.dumps({"error": f"File not found: {target}"}))
            sys.exit(1)

        file_content = file_path.read_text(encoding="utf-8")
        additional_prompt = sys.argv[3] if len(sys.argv) > 3 else "이 내용에 대해 전문가 관점에서 상세한 피드백을 주세요."

        prompt = f"""다음 문서를 검토하고 피드백해주세요.

---
{file_content}
---

{additional_prompt}"""

        system_instruction = "당신은 마케팅, 비즈니스 기획, 공간 디자인 분야의 전문 컨설턴트입니다. 구체적이고 실행 가능한 피드백을 제공하세요."

        result = call_gemini(prompt, system_instruction)
        if result["success"]:
            saved = save_response(additional_prompt, result["response"], mode, str(file_path))
            print(json.dumps({
                "success": True,
                "response": result["response"],
                "saved_to": saved,
                "source_file": str(file_path)
            }, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)

    elif mode == "conversation":
        # 기존 Gemini 대화 내용(복사된 텍스트)을 파일에서 읽어와서 분석
        file_path = Path(target)
        if not file_path.exists():
            print(json.dumps({"error": f"File not found: {target}"}))
            sys.exit(1)

        file_content = file_path.read_text(encoding="utf-8")
        additional_prompt = sys.argv[3] if len(sys.argv) > 3 else ""

        # 대화 내용만 반환 (Claude에서 직접 분석)
        print(json.dumps({
            "success": True,
            "conversation": file_content,
            "source_file": str(file_path),
            "additional_prompt": additional_prompt
        }, ensure_ascii=False))

    else:
        print(json.dumps({"error": f"Unknown mode: {mode}. Use 'chat', 'review', or 'conversation'"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
