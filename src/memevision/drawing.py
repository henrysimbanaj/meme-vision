"""Utilidades de dibujo sobre frames BGR: texto con tildes, esqueleto e imágenes."""

from __future__ import annotations

from functools import cache

import cv2
import numpy as np
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

from memevision.contracts import LandmarkResult

Color = tuple[int, int, int]  # BGR
WHITE: Color = (255, 255, 255)
BLACK: Color = (0, 0, 0)
YELLOW: Color = (0, 215, 255)
GREEN: Color = (80, 200, 60)
RED: Color = (60, 60, 230)
PINK: Color = (180, 105, 255)

POSE_EDGES = ((11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24))
HAND_EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
    (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19),
    (19, 20),
)  # fmt: skip


@cache
def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
    # DejaVu Sans viene dentro de matplotlib: igual en Kubuntu y en macOS
    prop = font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal")
    return ImageFont.truetype(font_manager.findfont(prop), size)


def text_size(text: str, size: int, bold: bool = False) -> tuple[int, int]:
    left, top, right, bottom = _font(size, bold).getbbox(text)
    return right - left, bottom - top


def put_text(
    img: np.ndarray,
    text: str,
    org: tuple[int, int],
    size: int = 28,
    color: Color = WHITE,
    bold: bool = False,
    outline: Color | None = BLACK,
    center: bool = False,
) -> None:
    """Escribe `text` (con tildes) en `img`, en su lugar. `org` es la esquina superior izquierda,
    o el centro si `center=True`."""
    font = _font(size, bold)
    w, h = text_size(text, size, bold)
    x, y = (org[0] - w // 2, org[1] - h // 2) if center else org
    pad = max(2, size // 8)
    x0, y0 = max(x - pad, 0), max(y - pad, 0)
    x1, y1 = min(x + w + 2 * pad, img.shape[1]), min(y + h + 3 * pad, img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    region = Image.fromarray(img[y0:y1, x0:x1, ::-1])  # BGR -> RGB
    draw = ImageDraw.Draw(region)
    stroke = max(1, size // 12) if outline is not None else 0
    draw.text(
        (x - x0, y - y0 - font.getbbox(text)[1]),
        text,
        font=font,
        fill=color[::-1],
        stroke_width=stroke,
        stroke_fill=None if outline is None else outline[::-1],
    )
    img[y0:y1, x0:x1] = np.asarray(region)[:, :, ::-1]


def draw_landmarks(img: np.ndarray, lm: LandmarkResult | None) -> None:
    if lm is None:
        return
    h, w = img.shape[:2]

    def px(points: np.ndarray) -> np.ndarray:
        return np.column_stack((points[:, 0] * w, points[:, 1] * h)).astype(int)

    if lm.pose is not None:
        pts = px(lm.pose)
        for a, b in POSE_EDGES:
            cv2.line(img, tuple(pts[a]), tuple(pts[b]), GREEN, 3, cv2.LINE_AA)
    for hand in (lm.left_hand, lm.right_hand):
        if hand is None:
            continue
        pts = px(hand)
        for a, b in HAND_EDGES:
            cv2.line(img, tuple(pts[a]), tuple(pts[b]), YELLOW, 2, cv2.LINE_AA)
        for p in pts:
            cv2.circle(img, tuple(p), 3, PINK, -1, cv2.LINE_AA)


def fit_image(src: np.ndarray, width: int, height: int, background: Color = BLACK) -> np.ndarray:
    """Escala `src` para que quepa en width×height sin deformarla, centrada sobre un fondo."""
    canvas = np.full((height, width, 3), background, dtype=np.uint8)
    scale = min(width / src.shape[1], height / src.shape[0])
    new_w, new_h = max(1, int(src.shape[1] * scale)), max(1, int(src.shape[0] * scale))
    resized = cv2.resize(src, (new_w, new_h), interpolation=cv2.INTER_AREA)
    x, y = (width - new_w) // 2, (height - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def darken(img: np.ndarray, top: int, bottom: int, alpha: float = 0.55) -> None:
    """Oscurece una franja horizontal para que el texto encima se lea bien."""
    img[top:bottom] = (img[top:bottom] * (1 - alpha)).astype(np.uint8)
