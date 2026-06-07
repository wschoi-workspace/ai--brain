#!/usr/bin/env python3
"""
Intaglio Filter — 사진을 요판화(凹版畫) 스타일로 변환
스타일: etching, engraving, mezzotint
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import math
import sys
import os


def load_image(path):
    """이미지 로드 및 전처리"""
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {path}")
    return img


def get_grayscale(img):
    """그레이스케일 변환 + CLAHE 대비 보정"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _draw_line_layer_fast(canvas, gray, angle_deg, spacing, min_radius=0.3,
                          max_radius_ratio=0.48, ink_strength=0.95):
    """
    지폐 인물화 수준의 라인 레이어.
    핵심 원칙: 라인이 사라지지 않는다. 밝은 곳에서도 최소 반경(min_radius)의
    가는 라인이 유지되며, 어두울수록 굵어진다.
    """
    h, w = canvas.shape
    angle_rad = math.radians(angle_deg)
    perp_x = -math.sin(angle_rad)
    perp_y = math.cos(angle_rad)

    # 모든 픽셀의 좌표
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)

    # 라인까지의 수직 거리
    proj = xs * perp_x + ys * perp_y
    nearest_line = np.round(proj / spacing) * spacing
    dist_to_line = np.abs(proj - nearest_line)

    # darkness 맵
    darkness = 1.0 - gray / 255.0

    # 라인 반경: 밝은 곳 = min_radius, 어두운 곳 = spacing * max_radius_ratio
    # 라인이 절대 사라지지 않음 — 지폐의 핵심
    max_radius = spacing * max_radius_ratio
    line_radius = min_radius + darkness * (max_radius - min_radius)

    # 라인 내부 판정
    inside = dist_to_line < line_radius

    # 가우시안 프로필
    dist_ratio = np.where(inside, dist_to_line / (line_radius + 1e-6), 1.0)
    falloff = np.exp(-2.5 * dist_ratio * dist_ratio)

    # 잉크 강도: darkness에 비례하되, 최소값 보장 (가는 선도 보여야 함)
    min_ink = 0.12  # 가장 밝은 곳에서도 이 정도 잉크
    ink = (min_ink + darkness * (ink_strength - min_ink)) * falloff

    # 라인 밖은 0
    ink = np.where(inside, ink, 0.0)

    # 캔버스에 적용
    result = canvas.astype(np.float64) * (1.0 - ink)
    return np.clip(result, 0, 255).astype(np.uint8)


def etching_style(img, line_density=8, edge_strength=1.5):
    """
    에칭 스타일 — 지폐 인물화 수준
    연속 라인이 이미지 전체를 관통하며 명암에 따라 굵기가 부드럽게 변조.
    다중 각도 레이어 중첩으로 풍부한 톤 표현.
    """
    h, w = img.shape[:2]
    gray = get_grayscale(img)

    # 부드러운 톤맵 (픽셀 단위 변조이므로 적당한 블러)
    gray_smooth = cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float64)

    # 콘트라스트 강화 — 지폐 인쇄의 명확한 톤 분리
    gray_norm = (gray_smooth - gray_smooth.min()) / (gray_smooth.max() - gray_smooth.min() + 1e-6)
    # 감마로 톤 커브 조정 — 중간톤 풍부하게
    gray_enhanced = np.power(gray_norm, 1.3) * 255.0

    # 캔버스 (종이 색)
    canvas = np.full((h, w), 252, dtype=np.uint8)

    # === 지폐 인물화 멀티 레이어 ===
    # 원칙: 모든 레이어에서 라인은 사라지지 않는다 (min_radius 보장)
    # 밝은 곳 = 가는 선, 어두운 곳 = 굵은 선 + 레이어 중첩

    # Layer 1: 주 해칭 (45도) — 전면, 가장 촘촘
    print("[intaglio] Layer 1/5: 45° primary")
    canvas = _draw_line_layer_fast(canvas, gray_enhanced, 45, spacing=3,
                                    min_radius=0.35, max_radius_ratio=0.48, ink_strength=0.9)

    # Layer 2: 교차 (135도) — 전면, 약간 연하게
    print("[intaglio] Layer 2/5: 135° cross")
    canvas = _draw_line_layer_fast(canvas, gray_enhanced, 135, spacing=3,
                                    min_radius=0.2, max_radius_ratio=0.45, ink_strength=0.8)

    # Layer 3: 수평 (0도) — 중간톤 보강
    print("[intaglio] Layer 3/5: 0° horizontal")
    canvas = _draw_line_layer_fast(canvas, gray_enhanced, 0, spacing=4,
                                    min_radius=0.1, max_radius_ratio=0.42, ink_strength=0.7)

    # Layer 4: 수직 (90도) — 어두운 영역 채움
    print("[intaglio] Layer 4/5: 90° vertical")
    canvas = _draw_line_layer_fast(canvas, gray_enhanced, 90, spacing=4,
                                    min_radius=0.05, max_radius_ratio=0.4, ink_strength=0.65)

    # Layer 5: 보조 대각 (22도) — 가장 어두운 곳
    print("[intaglio] Layer 5/5: 22° fill")
    canvas = _draw_line_layer_fast(canvas, gray_enhanced, 22, spacing=5,
                                    min_radius=0.0, max_radius_ratio=0.38, ink_strength=0.6)

    result = canvas.astype(np.float64)

    # 에지 강조 — 날카로운 윤곽선 (지폐 인물의 또렷한 경계)
    edges = cv2.Canny(gray_smooth.astype(np.uint8), 40, 130)
    edges_dilated = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    edge_mask = edges_dilated.astype(np.float64) / 255.0
    edge_mask = cv2.GaussianBlur(edge_mask, (3, 3), 0)
    result = result * (1.0 - edge_mask * 0.7)

    # 미세 노이즈 (동판 질감)
    noise = np.random.normal(0, 1.5, result.shape)
    result = np.clip(result + noise, 0, 255).astype(np.uint8)

    return result


def engraving_style(img, num_lines=300, line_weight_range=(1, 4)):
    """
    인그레이빙 스타일: 평행선 굵기 변조
    - 지폐/우표 스타일의 수평 평행선
    - 명암에 따라 선 굵기가 변함
    """
    h, w = img.shape[:2]
    gray = get_grayscale(img)

    # 부드러운 톤맵
    gray = cv2.GaussianBlur(gray, (7, 7), 0)

    canvas = np.full((h, w), 248, dtype=np.uint8)
    pil_canvas = Image.fromarray(canvas)
    draw = ImageDraw.Draw(pil_canvas)

    line_spacing = max(3, h // num_lines)
    min_w, max_w = line_weight_range

    for y_line in range(0, h, line_spacing):
        # 각 라인을 세그먼트로 나눠서 굵기/물결을 부드럽게 변조
        seg_width = 3  # 3px 단위로 샘플링
        points = []
        widths = []
        inks = []

        for x_pos in range(0, w, seg_width):
            tone = gray[min(y_line, h - 1), min(x_pos, w - 1)]
            darkness = 1.0 - (tone / 255.0)

            # 물결 진폭: 어두울수록 진폭 큼 (선이 부풀어오르는 느낌)
            wave_amp = darkness * line_spacing * 0.45
            # 주파수를 높여서 지폐 느낌의 촘촘한 물결
            wave = math.sin(x_pos * 0.03 + y_line * 0.1) * wave_amp

            points.append((x_pos, y_line + wave))

            # 굵기: 밝은 곳 1px, 어두운 곳 최대 4px
            w_val = max(min_w, int(min_w + (max_w - min_w) * (darkness ** 0.7)))
            widths.append(w_val)

            # 잉크 색: 어두울수록 진하게
            ink = max(20, int(140 - darkness * 120))
            inks.append(ink)

        # 세그먼트별로 그리기
        for i in range(len(points) - 1):
            # 밝은 곳에서도 가는 선은 유지 (지폐 특유의 연속 라인)
            draw.line([points[i], points[i + 1]], fill=inks[i], width=widths[i])

    result = np.array(pil_canvas)

    # 에지 오버레이 — 윤곽선 강조
    edges = cv2.Canny(gray, 60, 160)
    edges = cv2.dilate(edges, np.ones((1, 1), np.uint8), iterations=1)
    edge_inv = 255 - (edges * 0.6).astype(np.uint8)
    result = np.minimum(result, edge_inv)

    # 미세 질감
    noise = np.random.normal(0, 1.5, result.shape).astype(np.int16)
    result = np.clip(result.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return result


def mezzotint_style(img, dot_density=3):
    """
    메조틴트 스타일: 부드러운 톤 그라데이션 + 미세 그레인
    - 어두운 베이스에서 밝은 부분을 버니셔로 깎아내는 원리
    - 풍부하고 연속적인 톤 전환이 핵심
    """
    h, w = img.shape[:2]
    gray = get_grayscale(img)

    # 부드러운 톤맵 — 메조틴트는 연속 톤이 핵심, 강한 블러
    gray_smooth = cv2.GaussianBlur(gray, (15, 15), 0).astype(np.float64)

    # Step 1: 톤 매핑 — 콘트라스트 강화 + 어두운 기조
    normalized = gray_smooth / 255.0

    # 감마로 어두운 기조 만들기 (메조틴트는 기본적으로 어두운 매체)
    tone = np.power(normalized, 1.3)
    # 15(가장어둠) ~ 240(가장밝음) 범위
    base = tone * 225.0 + 15.0

    # Step 2: 멀티스케일 그레인 — 메조틴트 특유의 로커 자국
    # 미세 그레인 (1px 단위) — 강하게
    g1 = np.random.normal(0, 18, (h, w))
    # 중간 그레인 (2~3px 뭉치)
    g2_small = np.random.normal(0, 12, (h // 2, w // 2))
    g2 = cv2.resize(g2_small, (w, h), interpolation=cv2.INTER_LINEAR)
    # 거친 그레인 (큰 텍스처)
    g3_small = np.random.normal(0, 6, (h // 4, w // 4))
    g3 = cv2.resize(g3_small, (w, h), interpolation=cv2.INTER_LINEAR)

    grain = g1 * 0.5 + g2 * 0.3 + g3 * 0.2

    # Step 3: 그레인 강도 — 중간톤에서 가장 강하고, 밝은/어두운 극단에서 약함
    grain_strength = 4.0 * normalized * (1.0 - normalized)  # parabola
    grain_strength = np.clip(grain_strength, 0.15, 1.0)

    # 어두운 곳 그레인 더 강하게 (로커 자국 남아있는 느낌)
    grain_strength = grain_strength + (1.0 - normalized) * 0.3

    # Step 4: 합성 (float 전체에서 수행 — 계단 방지)
    result = base + grain * grain_strength
    result = np.clip(result, 0, 255)

    # Step 5: 에지 — 매우 미세하게만 (메조틴트는 선이 아닌 면 기법)
    edges = cv2.Canny(gray_smooth.astype(np.uint8), 30, 100)
    edges_soft = cv2.GaussianBlur(edges.astype(np.float64), (5, 5), 0)
    edge_darken = (edges_soft / 255.0) * 15  # 아주 약하게만
    result = result - edge_darken

    # Step 6: 최종 블러 — 부드러운 블렌딩
    result = np.clip(result, 0, 255).astype(np.uint8)
    result = cv2.GaussianBlur(result, (3, 3), 0)

    return result


def apply_plate_border(img, border_width=20):
    """동판 프레스 자국 (플레이트 마크) 추가"""
    h, w = img.shape
    bordered = np.full((h + border_width * 2, w + border_width * 2), 250, dtype=np.uint8)
    bordered[border_width:border_width + h, border_width:border_width + w] = img

    # 프레스 자국 — 안쪽 가장자리 약간 어둡게
    for i in range(3):
        offset = border_width - i - 1
        bordered[offset, border_width:border_width + w] = 200 - i * 20
        bordered[offset + h + 1 + i, border_width:border_width + w] = 200 - i * 20
        bordered[border_width:border_width + h, offset] = 200 - i * 20
        bordered[border_width:border_width + h, offset + w + 1 + i] = 200 - i * 20

    return bordered


def process_image(input_path, output_path=None, style="etching", add_border=True, **kwargs):
    """
    메인 처리 함수

    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 경로 (None이면 자동 생성)
        style: etching | engraving | mezzotint
        add_border: 플레이트 마크 추가 여부
    """
    img = load_image(input_path)

    style_map = {
        "etching": etching_style,
        "engraving": engraving_style,
        "mezzotint": mezzotint_style,
    }

    if style not in style_map:
        raise ValueError(f"지원하지 않는 스타일: {style}. 사용 가능: {list(style_map.keys())}")

    print(f"[intaglio] 스타일: {style} | 입력: {input_path}")
    print(f"[intaglio] 원본 크기: {img.shape[1]}x{img.shape[0]}")

    result = style_map[style](img, **kwargs)

    if add_border:
        result = apply_plate_border(result)

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-{style}.png"

    cv2.imwrite(output_path, result)
    print(f"[intaglio] 출력: {output_path}")
    print(f"[intaglio] 결과 크기: {result.shape[1]}x{result.shape[0]}")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 intaglio-filter.py <이미지경로> [스타일]")
        print("스타일: etching (기본), engraving, mezzotint")
        sys.exit(1)

    input_path = sys.argv[1]
    style = sys.argv[2] if len(sys.argv) > 2 else "etching"

    process_image(input_path, style=style)
