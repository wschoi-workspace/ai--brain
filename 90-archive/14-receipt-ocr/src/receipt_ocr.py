#!/usr/bin/env python3
"""
Receipt OCR - Gemini 2.5 Flash로 영수증 이미지에서 필드 추출
"""

import os
import sys
import json
import base64
import re
from pathlib import Path
from typing import Callable, Optional

import requests
from dotenv import load_dotenv

# .env 로드 (실행 파일 기준)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

PROMPT = """이 영수증 이미지에서 다음 정보를 JSON으로 추출하세요.
값을 찾을 수 없으면 null을 사용하세요.

{
  "date": "YYYY-MM-DD 형식의 거래일자",
  "merchant": "상호명",
  "business_number": "사업자등록번호 (123-45-67890 형식)",
  "total_amount": 총 결제금액 (숫자, 단위 없이 정수),
  "payment_method": "카드" 또는 "현금" 또는 "기타",
  "address": "매장 주소"
}

JSON만 출력하세요. 코드블록이나 설명 없이 순수 JSON만.
"""

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
}


def _encode_image(image_path: Path) -> tuple[str, str]:
    """이미지를 base64로 인코딩. HEIC은 JPEG로 변환."""
    ext = image_path.suffix.lower()

    if ext == ".heic":
        # HEIC은 Pillow로 JPEG 변환 필요
        try:
            from PIL import Image
            import pillow_heif
            pillow_heif.register_heif_opener()

            import io
            img = Image.open(image_path).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            return base64.b64encode(buf.getvalue()).decode(), "image/jpeg"
        except ImportError:
            raise RuntimeError("HEIC 지원을 위해 pillow-heif 설치 필요: pip install pillow-heif")

    mime = MIME_TYPES.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


def _parse_json_response(text: str) -> dict:
    """Gemini 응답에서 JSON 추출. 코드블록이 섞여와도 파싱."""
    # 코드블록 제거
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    # { ... } 블록만 추출
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)

    return json.loads(text)


def process_single_receipt(image_path: Path) -> dict:
    """단일 영수증 처리. 실패해도 dict 반환."""
    result = {
        "date": None,
        "merchant": None,
        "business_number": None,
        "total_amount": None,
        "payment_method": None,
        "address": None,
        "filename": image_path.name,
        "error": None,
    }

    try:
        image_data, mime_type = _encode_image(image_path)

        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [
                        {"text": PROMPT},
                        {"inline_data": {"mime_type": mime_type, "data": image_data}},
                    ]
                }]
            },
            timeout=60,
        )

        if response.status_code != 200:
            result["error"] = f"API 오류 {response.status_code}"
            return result

        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _parse_json_response(text)

        result.update({k: parsed.get(k) for k in (
            "date", "merchant", "business_number",
            "total_amount", "payment_method", "address"
        )})

    except json.JSONDecodeError as e:
        result["error"] = f"JSON 파싱 실패: {e}"
    except requests.exceptions.Timeout:
        result["error"] = "API 타임아웃 (60초)"
    except requests.exceptions.ConnectionError:
        result["error"] = "네트워크 연결 실패"
    except Exception as e:
        result["error"] = f"처리 실패: {type(e).__name__}: {e}"

    return result


def scan_folder(folder_path: Path) -> list[Path]:
    """폴더에서 지원되는 이미지 파일 목록 반환 (정렬됨)."""
    images = [
        p for p in folder_path.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    ]
    return sorted(images)


def process_folder(
    folder_path: Path,
    progress_callback: Optional[Callable[[int, int, str, bool], None]] = None,
) -> list[dict]:
    """
    폴더 내 모든 영수증 처리.
    progress_callback(current, total, filename, success) 호출.
    """
    images = scan_folder(folder_path)
    total = len(images)
    results = []

    for i, image_path in enumerate(images, 1):
        result = process_single_receipt(image_path)
        results.append(result)
        success = result["error"] is None
        if progress_callback:
            progress_callback(i, total, image_path.name, success)

    return results


def check_api_key() -> bool:
    return bool(GEMINI_API_KEY)


# CLI 단독 테스트용
if __name__ == "__main__":
    if not check_api_key():
        print("ERROR: GEMINI_API_KEY가 .env에 없습니다.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("사용법: python receipt_ocr.py <이미지파일 또는 폴더>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"ERROR: 경로 없음: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_file():
        result = process_single_receipt(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        def _cb(cur, tot, name, ok):
            mark = "✓" if ok else "✗"
            print(f"[{cur}/{tot}] {mark} {name}")

        results = process_folder(target, _cb)
        print(f"\n총 {len(results)}건 처리 완료")
        print(json.dumps(results, ensure_ascii=False, indent=2))
