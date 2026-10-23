"""Dibujo de la app de feria: un lienzo 1280x720 por cada GameState (spec 009)."""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from functools import cache

import cv2
import numpy as np

from memevision.config import ROOT
from memevision.contracts import NEUTRAL, UNSURE, LandmarkResult, MemeSpec, Prediction
from memevision.drawing import (
    GREEN,
    RED,
    WHITE,
    YELLOW,
    darken,
    draw_landmarks,
    fit_image,
    put_text,
    text_size,
)
from memevision.game import GameState, Mode, Phase

WIDTH, HEIGHT = 1280, 720
HEADER, BODY = 80, 480  # alto del encabezado y de la zona de cámara/meme
FOOTER_Y = HEADER + BODY
HALF = WIDTH // 2
BG = (33, 26, 15)  # azul tinta (BGR)
PANEL_BG = (38, 39, 22)  # azul petróleo oscuro
ACCENT = (200, 120, 255)  # rosa
GAME_CYAN = (255, 225, 85)
GAME_MINT = (170, 255, 120)

MODE_NAMES = {Mode.CHALLENGE: "Reto", Mode.FREE: "Libre", Mode.LIVE: "En vivo"}
GAME_PROMPTS = {
    Phase.DETECTED: ("¿Listo?", GAME_CYAN),
    Phase.COUNTDOWN: ("¡Imita al gato!", GAME_MINT),
}
# Lienzo 1280x720. La demo traduce el clic de la ventana a estas coordenadas.
START_BUTTON = (440, 294, 400, 76)
RETRY_BUTTON = (440, 628, 400, 58)
START_LOGO_PATH = ROOT / "assets" / "images" / "logo-live-webcat.png"
START_MEME_IDS = (
    "michi-67",
    "michi-burla",
    "michi-de-hecho",
    "michi-fuerza",
    "michi-silencio",
    "michi-tirando-flow",
)


def button_at(x: int, y: int) -> str | None:
    """Devuelve 'start' en «Jugar» o 'retry' en «Volver a intentar»."""
    for name, rect in (("start", START_BUTTON), ("retry", RETRY_BUTTON)):
        x0, y0, w, h = rect
        if x0 <= x < x0 + w and y0 <= y < y0 + h:
            return name
    return None


def render_start(
    catalog: Mapping[str, MemeSpec] | None = None, time_s: float | None = None
) -> np.ndarray:
    """Menú arcade animado con botón de partida y seis memes de gato."""
    now = time.monotonic() if time_s is None else time_s
    canvas = _arcade_background(now)
    logo_y = int(4 * math.sin(now * 3.2))
    _draw_start_logo(canvas, logo_y)
    cat_x = 1015 + int(9 * math.sin(now * 2.3))
    cat_y = 66 + int(8 * abs(math.sin(now * 3.8)))
    _draw_pixel_cat(canvas, cat_x, cat_y, 1.0)
    x0, y0, w, h = START_BUTTON
    pulse = int(10 * (0.5 + 0.5 * math.sin(now * 4)))
    _rounded_rect(canvas, (x0 - 7, y0 - 6, w + 14, h + 12), (150 + pulse, 80, 255), 42)
    _rounded_rect(canvas, START_BUTTON, (220, 135, 255), 34)
    _rounded_rect(canvas, (x0 + 7, y0 + 6, w - 14, h - 20), (245, 195, 255), 27)
    put_text(canvas, "ELIGE TU POSE", (HALF, 392), 22, (190, 165, 255), bold=True, center=True)
    _draw_start_memes(canvas, catalog or {}, now)
    put_text(
        canvas,
        "Enter o espacio para jugar  ·  f: pantalla completa  ·  q: salir",
        (HALF, 681),
        18,
        (190, 180, 205),
        center=True,
    )
    # Dibujar la etiqueta al final para que siempre quede encima de todas las capas del botón.
    put_text(
        canvas,
        "Jugar  ▶",
        (x0 + w // 2, y0 + h // 2 + 1),
        36,
        WHITE,
        bold=True,
        outline=(115, 115, 115),
        center=True,
    )
    return canvas


def _arcade_background(time_s: float) -> np.ndarray:
    top = np.array((48, 18, 48), dtype=np.float32)
    bottom = np.array((18, 10, 35), dtype=np.float32)
    blend = np.linspace(0, 1, HEIGHT, dtype=np.float32)[:, None, None]
    rows = top[None, None, :] * (1 - blend) + bottom[None, None, :] * blend
    canvas = np.broadcast_to(rows, (HEIGHT, WIDTH, 3)).astype(np.uint8).copy()
    for i in range(38):
        x = (i * 197 + 31) % WIDTH
        y = (i * 83 + 19) % 330
        twinkle = 0.45 + 0.55 * abs(math.sin(time_s * 2.5 + i))
        color = tuple(int(v * twinkle) for v in (190, 115, 255))
        size = 2 if i % 5 else 4
        cv2.circle(canvas, (x, y), size, color, -1, cv2.LINE_AA)
    horizon = 614
    for i in range(9):
        y = horizon + i * i * 2
        cv2.line(canvas, (0, y), (WIDTH, y), (67, 40, 91), 1, cv2.LINE_AA)
    shift = int((time_s * 34) % 100)
    for x in range(-WIDTH, 2 * WIDTH, 100):
        cv2.line(canvas, (HALF + (x - HALF) // 4, horizon), (x - shift, HEIGHT), (62, 38, 83), 1)
    return canvas


@cache
def _start_logo() -> np.ndarray:
    logo = cv2.imread(str(START_LOGO_PATH), cv2.IMREAD_UNCHANGED)
    if logo is None or logo.ndim != 3 or logo.shape[2] != 4:
        return np.zeros((1, 1, 4), dtype=np.uint8)
    return logo


def _draw_start_logo(canvas: np.ndarray, y: int) -> None:
    logo = _start_logo()
    max_w, max_h = 540, 246
    scale = min(max_w / logo.shape[1], max_h / logo.shape[0])
    width = max(1, int(logo.shape[1] * scale))
    height = max(1, int(logo.shape[0] * scale))
    resized = cv2.resize(logo, (width, height), interpolation=cv2.INTER_AREA)
    x = (WIDTH - width) // 2
    y = max(0, y)
    roi = canvas[y : y + height, x : x + width]
    alpha = resized[:, :, 3:4].astype(np.float32) / 255
    roi[:] = (resized[:, :, :3] * alpha + roi * (1 - alpha)).astype(np.uint8)


def _draw_start_memes(canvas: np.ndarray, catalog: Mapping[str, MemeSpec], time_s: float) -> None:
    card_w, card_h, gap = 180, 194, 20
    total_w = len(START_MEME_IDS) * card_w + (len(START_MEME_IDS) - 1) * gap
    left = (WIDTH - total_w) // 2
    for index, meme_id in enumerate(START_MEME_IDS):
        meme = catalog.get(meme_id)
        x = left + index * (card_w + gap)
        bob = int(3 * math.sin(time_s * 3 + index * 0.8))
        y = 409 + bob
        _rounded_rect(canvas, (x, y, card_w, card_h), (75, 48, 100), 18)
        _rounded_rect(canvas, (x + 2, y + 2, card_w - 4, card_h - 4), (38, 20, 55), 16)
        if meme is not None:
            thumbnail = fit_image(_reference(meme.image_path), card_w - 24, 128, (28, 14, 41))
            canvas[y + 10 : y + 138, x + 12 : x + card_w - 12] = thumbnail
            labels = {
                "michi-67": "Michi 6 7",
                "michi-burla": "Michi Burla",
                "michi-de-hecho": "De Hecho",
                "michi-fuerza": "Michi Fuerza",
                "michi-silencio": "Michi Silencio",
                "michi-tirando-flow": "Michi Flow",
            }
            put_text(
                canvas,
                labels[meme_id],
                (x + card_w // 2, y + 163),
                17,
                WHITE,
                bold=True,
                center=True,
            )
        else:
            put_text(canvas, "Michi", (x + card_w // 2, y + card_h // 2), 22, WHITE, center=True)


def _draw_pixel_cat(canvas: np.ndarray, x: int, y: int, scale: float) -> None:
    unit = max(2, int(8 * scale))
    gold, shade, pink = (60, 185, 255), (30, 105, 190), (170, 120, 255)
    head = (x, y, unit * 7, unit * 5)
    cv2.rectangle(canvas, (head[0], head[1]), (head[0] + head[2], head[1] + head[3]), gold, -1)
    left_ear = np.array([(x, y + unit * 2), (x + unit, y), (x + unit * 2, y + unit * 3)])
    right_ear = np.array(
        [(x + unit * 5, y + unit * 3), (x + unit * 6, y), (x + unit * 7, y + unit * 2)]
    )
    cv2.fillPoly(canvas, [left_ear], gold)
    cv2.fillPoly(canvas, [right_ear], gold)
    cv2.rectangle(canvas, (x + unit, y + unit * 2), (x + unit * 2, y + unit * 3), shade, -1)
    cv2.rectangle(canvas, (x + unit * 5, y + unit * 2), (x + unit * 6, y + unit * 3), shade, -1)
    cv2.circle(canvas, (x + unit * 2, y + unit * 3), max(2, unit // 5), (35, 28, 30), -1)
    cv2.circle(canvas, (x + unit * 5, y + unit * 3), max(2, unit // 5), (35, 28, 30), -1)
    cv2.circle(canvas, (x + unit * 4, y + unit * 4), max(2, unit // 4), pink, -1)
    body_y = y + unit * 5
    cv2.rectangle(canvas, (x + unit, body_y), (x + unit * 6, body_y + unit * 3), gold, -1)
    leg_offset = unit if int(y / max(unit, 1)) % 2 else 0
    for leg_x in (x + unit * 2, x + unit * 5):
        cv2.rectangle(
            canvas,
            (leg_x, body_y + unit * 3),
            (leg_x + unit, body_y + unit * 4 + leg_offset),
            shade,
            -1,
        )
    cv2.ellipse(
        canvas,
        (x + unit * 7, body_y + unit),
        (unit * 2, unit),
        0,
        190,
        510,
        gold,
        unit // 2 + 1,
    )


def _rounded_rect(
    image: np.ndarray, rect: tuple[int, int, int, int], color: tuple[int, int, int], radius: int
) -> None:
    x, y, width, height = rect
    radius = min(radius, width // 2, height // 2)
    cv2.rectangle(image, (x + radius, y), (x + width - radius, y + height), color, -1)
    cv2.rectangle(image, (x, y + radius), (x + width, y + height - radius), color, -1)
    for center in (
        (x + radius, y + radius),
        (x + width - radius, y + radius),
        (x + radius, y + height - radius),
        (x + width - radius, y + height - radius),
    ):
        cv2.circle(image, center, radius, color, -1, cv2.LINE_AA)


def render(
    frame: np.ndarray | None,
    state: GameState,
    catalog: dict[str, MemeSpec],
    landmarks: LandmarkResult | None = None,
    banner: str = "",
    draft_name: str = "",
    leaderboard: list[tuple[str, int]] | None = None,
    time_s: float | None = None,
) -> np.ndarray:
    now = time.monotonic() if time_s is None else time_s
    canvas = _game_background(now)
    if state.phase == Phase.SUMMARY:
        _summary(canvas, state, draft_name, leaderboard or [])
        _draw_game_mascot(canvas, now)
        return canvas
    _header(canvas, state)
    _draw_game_mascot(canvas, now)
    _camera(canvas, frame, state, landmarks, now)
    _right_panel(canvas, state, catalog)
    _footer(canvas, state, catalog, now)
    if banner:
        cv2.rectangle(canvas, (0, HEADER), (WIDTH, HEADER + 34), RED, -1)
        put_text(canvas, banner, (HALF, HEADER + 17), 22, WHITE, True, outline=None, center=True)
    return canvas


def _game_background(time_s: float) -> np.ndarray:
    """Fondo oceánico animado con ondas y burbujas, en colores distintos al menú."""
    top = np.array((33, 26, 15), dtype=np.float32)  # azul tinta (BGR)
    bottom = np.array((62, 48, 29), dtype=np.float32)  # azul petróleo
    blend = np.linspace(0, 1, HEIGHT, dtype=np.float32)[:, None, None]
    rows = top[None, None, :] * (1 - blend) + bottom[None, None, :] * blend
    canvas = np.broadcast_to(rows, (HEIGHT, WIDTH, 3)).astype(np.uint8).copy()

    for index in range(24):
        x = (index * 173 + 41 + int(time_s * (12 + index % 5))) % WIDTH
        travel = (time_s * (18 + index % 7) + index * 37) % (HEIGHT + 48)
        y = HEIGHT - int(travel)
        radius = 3 + index % 6
        color = (112, 133, 145) if index % 4 else (112, 142, 198)
        cv2.circle(canvas, (x, y), radius, color, 1 if index % 3 else 2, cv2.LINE_AA)
        if index % 5 == 0:
            cv2.circle(canvas, (x - 2, y - 2), 1, (176, 159, 145), -1, cv2.LINE_AA)
    return canvas


def _draw_game_mascot(canvas: np.ndarray, time_s: float) -> None:
    """Dibuja el mismo gato pixelado del menú, con un pequeño salto animado."""
    x = 30 + int(4 * math.sin(time_s * 2.1))
    y = 6 + int(3 * abs(math.sin(time_s * 3.4)))
    _draw_pixel_cat(canvas, x, y, 0.65)


# --- zonas -------------------------------------------------------------------------------------


def _header(canvas: np.ndarray, state: GameState) -> None:
    if state.mode == Mode.CHALLENGE:
        mode = f"{state.round}/{state.total_rounds} · {state.score} pts"
    elif state.mode == Mode.LIVE:
        mode = f"Modo {MODE_NAMES[state.mode]}"
    else:
        mode = f"Modo {MODE_NAMES[state.mode]} · Ronda {state.round}"
    put_text(canvas, mode, (WIDTH - 24 - _width(mode, 26), 26), 26)


def _camera(
    canvas: np.ndarray,
    frame: np.ndarray | None,
    state: GameState,
    lm: LandmarkResult | None,
    time_s: float,
) -> None:
    if frame is None:
        view = np.full((BODY, HALF, 3), PANEL_BG, dtype=np.uint8)
        put_text(view, "Sin cámara", (HALF // 2, BODY // 2), 32, center=True)
    else:
        view = fit_image(frame, HALF, BODY)
        if lm is not None:
            h, w = frame.shape[:2]
            scale = min(HALF / w, BODY / h)
            ox, oy = (HALF - int(w * scale)) // 2, (BODY - int(h * scale)) // 2
            inner = view[oy : oy + int(h * scale), ox : ox + int(w * scale)]
            draw_landmarks(inner, lm)

    center = (HALF // 2, BODY // 2)
    if state.phase == Phase.COUNTDOWN:
        number = str(int(state.remaining_s) + 1)
        pulse = int(8 * (0.5 + 0.5 * math.sin(time_s * 11)))
        overlay = view.copy()
        cv2.circle(overlay, center, 112, (22, 15, 35), -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.78, view, 0.22, 0, view)
        cv2.circle(view, center, 106 + pulse // 2, GAME_CYAN, 3, cv2.LINE_AA)
        put_text(view, number, center, 190 + pulse, GAME_CYAN, bold=True, center=True)
    elif state.phase == Phase.ANALYZING:
        dots = "." * (1 + int(state.remaining_s * 3) % 3)
        darken(view, BODY // 2 - 40, BODY // 2 + 40)
        pulse = int(5 * (0.5 + 0.5 * math.sin(time_s * 9)))
        for index in range(3):
            x = center[0] - 30 + index * 30
            cv2.circle(
                view,
                (x, center[1]),
                7 + pulse // 2 if index == len(dots) - 1 else 7,
                GAME_CYAN,
                -1,
                cv2.LINE_AA,
            )
    canvas[HEADER:FOOTER_Y, :HALF] = view


def _right_panel(canvas: np.ndarray, state: GameState, catalog: dict[str, MemeSpec]) -> None:
    panel = np.full((BODY, HALF, 3), PANEL_BG, dtype=np.uint8)
    if state.phase == Phase.RESULT and state.result is not None:
        _meme_card(panel, catalog.get(state.result.meme), title=None, show_traits=False)
    elif state.mode == Mode.CHALLENGE:
        _meme_card(panel, catalog.get(state.target or ""), title=None, show_traits=False)
    elif state.mode == Mode.FREE:
        _meme_grid(panel, list(catalog.values()))
    else:
        live = state.live
        meme = catalog.get(live.meme) if live is not None and live.meme in catalog else None
        _meme_card(panel, meme, title="Se parece a:" if meme else None, show_traits=False)
    canvas[HEADER:FOOTER_Y, HALF:] = panel


def _footer(
    canvas: np.ndarray, state: GameState, catalog: dict[str, MemeSpec], time_s: float
) -> None:
    y = FOOTER_Y + 40
    phase, mode = state.phase, state.mode
    if phase in GAME_PROMPTS:
        text, color = GAME_PROMPTS[phase]
        _game_prompt(canvas, text, y, color, time_s)
    elif phase == Phase.ANALYZING:
        _bars(
            canvas,
            state.live,
            catalog,
            y + 30,
            rows=1 if mode == Mode.CHALLENGE else 2,
            target=state.target if mode == Mode.CHALLENGE else None,
        )
    elif phase == Phase.RESULT and state.result is not None:
        _result(canvas, state, catalog, y)
    elif phase == Phase.LIVE:
        if state.live is None and state.person_visible:
            _big(canvas, "¡Te veo!", y, YELLOW)
        elif state.live is not None:
            _bars(canvas, state.live, catalog, y - 20, rows=3)


def _game_prompt(
    canvas: np.ndarray, text: str, y: int, color: tuple[int, int, int], time_s: float
) -> None:
    pulse = 0.5 + 0.5 * math.sin(time_s * 9)
    bob = int(4 * math.sin(time_s * 7))
    width, height = 510, 60 + int(pulse * 4)
    x, top = (WIDTH - width) // 2, y - height // 2 + bob
    _rounded_rect(canvas, (x - 5, top - 4, width + 10, height + 8), color, 30)
    _rounded_rect(canvas, (x, top, width, height), PANEL_BG, 26)
    size = 34 + int(pulse * 4)
    put_text(canvas, text, (WIDTH // 2, top + height // 2), size, color, bold=True, center=True)
    sparkle_y = top + height // 2
    sparkle_x = x + 28 + int(pulse * 8)
    cv2.drawMarker(canvas, (sparkle_x, sparkle_y), color, cv2.MARKER_DIAMOND, 13, 2, cv2.LINE_AA)
    cv2.drawMarker(
        canvas,
        (x + width - 28 - int(pulse * 8), sparkle_y),
        color,
        cv2.MARKER_DIAMOND,
        13,
        2,
        cv2.LINE_AA,
    )


def _summary(
    canvas: np.ndarray,
    state: GameState,
    draft_name: str,
    leaderboard: list[tuple[str, int]],
) -> None:
    _big(canvas, f"Tu puntaje: {state.score}", 110, WHITE)
    _small(canvas, "¿Quieres guardar tu nombre y puntaje?", 170, (210, 210, 210), 28)
    shown = draft_name if draft_name else "escribe tu nombre y pulsa Enter"
    color = WHITE if draft_name else (150, 150, 150)
    cv2.rectangle(canvas, (340, 200), (940, 260), PANEL_BG, -1)
    cv2.rectangle(canvas, (340, 200), (940, 260), ACCENT, 2)
    put_text(canvas, shown, (640, 230), 32, color, bold=True, center=True)

    put_text(canvas, "Leaderboard", (640, 300), 32, ACCENT, bold=True, center=True)
    if not leaderboard:
        _small(canvas, "Todavía no hay puntajes guardados", 360)
    for i, (name, score) in enumerate(leaderboard[:8]):
        line = f"{i + 1}.  {name}    {score}"
        put_text(canvas, line, (640, 350 + i * 32), 26, WHITE, center=True)

    x0, y0, w, h = RETRY_BUTTON
    cv2.rectangle(canvas, (x0, y0), (x0 + w, y0 + h), ACCENT, -1)
    put_text(
        canvas, "Volver a intentar", (x0 + w // 2, y0 + h // 2), 28, BG, bold=True, center=True
    )


def feedback_for(points: int) -> str:
    """Mensaje del resultado según los puntos de la ronda, de 0 a 100."""
    if points >= 80:
        return "Excelente"
    if points >= 55:
        return "Buen Trabajo"
    if points >= 30:
        return "Casi"
    return "¡Sigue intentando!"


def _result(canvas: np.ndarray, state: GameState, catalog: dict[str, MemeSpec], y: int) -> None:
    result = state.result
    if state.mode == Mode.CHALLENGE:
        message = feedback_for(state.round_points)
        message_color = GAME_MINT if state.round_points < 30 else GAME_CYAN
        box_w = max(390, min(700, _width(message, 40) + 80))
        _rounded_rect(canvas, (WIDTH // 2 - box_w // 2, y - 30, box_w, 58), PANEL_BG, 24)
        _rounded_rect(canvas, (WIDTH // 2 - box_w // 2, y - 30, box_w, 4), message_color, 2)
        put_text(canvas, message, (WIDTH // 2, y), 38, message_color, bold=True, center=True)
    elif result.meme == NEUTRAL:
        _big(canvas, "No estás imitando ningún meme", y, YELLOW)
    elif result.meme != UNSURE:
        _big(canvas, feedback_for(int(round(result.confidence * 100))), y, WHITE)
    if state.mode == Mode.CHALLENGE:
        card_y, card_h, card_w, gap = y + 36, 72, 330, 24
        left_x = WIDTH // 2 - gap // 2 - card_w
        right_x = WIDTH // 2 + gap // 2
        for x, label, value, color in (
            (left_x, "PUNTOS DE ESTE MICHI", f"+{state.round_points}", GAME_MINT),
            (right_x, "PUNTAJE TOTAL", str(state.score), GAME_CYAN),
        ):
            _rounded_rect(canvas, (x, card_y, card_w, card_h), PANEL_BG, 18)
            _rounded_rect(canvas, (x, card_y, 5, card_h), color, 2)
            put_text(
                canvas, label, (x + card_w // 2, card_y + 22), 16, WHITE, bold=True, center=True
            )
            put_text(
                canvas, value, (x + card_w // 2, card_y + 55), 29, color, bold=True, center=True
            )
    elif state.success is True:
        _small(canvas, "¡Reto superado!", y + 56, GREEN, size=34)
    elif state.success is False:
        _small(canvas, f"¡Casi! Tu reto era {_name(state.target, catalog)}", y + 56, ACCENT, 30)


# --- piezas ------------------------------------------------------------------------------------


def _meme_card(
    panel: np.ndarray, meme: MemeSpec | None, title: str | None, show_traits: bool
) -> None:
    if meme is None:
        put_text(panel, "?", (HALF // 2, BODY // 2), 160, (120,) * 3, True, center=True)
        return
    traits = meme.traits if show_traits else ()
    top = 50 if title else 10
    bottom = BODY - 56 - 30 * len(traits)
    image = _reference(meme.image_path)
    panel[top:bottom] = fit_image(image, HALF, bottom - top, background=PANEL_BG)
    if title:
        put_text(panel, title, (HALF // 2, 25), 28, (200,) * 3, center=True)
    put_text(panel, meme.name, (HALF // 2, bottom + 26), 36, ACCENT, bold=True, center=True)
    for i, trait in enumerate(traits):
        put_text(panel, f"• {trait}", (40, bottom + 52 + 30 * i), 22)


def _meme_grid(panel: np.ndarray, memes: list[MemeSpec]) -> None:
    put_text(panel, "Imita cualquiera de estos:", (HALF // 2, 25), 28, (200,) * 3, center=True)
    if not memes:
        return
    cols = 3 if len(memes) > 4 else 2
    rows = -(-len(memes) // cols)
    cell_w, cell_h = HALF // cols, (BODY - 60) // rows
    for i, meme in enumerate(memes):
        x, y = (i % cols) * cell_w, 55 + (i // cols) * cell_h
        thumb = fit_image(_reference(meme.image_path), cell_w - 16, cell_h - 40, PANEL_BG)
        panel[y : y + thumb.shape[0], x + 8 : x + 8 + thumb.shape[1]] = thumb
        put_text(panel, meme.name, (x + cell_w // 2, y + cell_h - 22), 20, center=True)


def _bars(
    canvas: np.ndarray,
    prediction: Prediction | None,
    catalog: dict[str, MemeSpec],
    y: int,
    rows: int = 2,
    target: str | None = None,
) -> None:
    if prediction is None:
        return
    probabilities = prediction.probabilities or {prediction.meme: prediction.confidence}
    rows_data: list[tuple[str, float, bool]] = []
    row_limit = rows
    if target is not None:
        row_limit = max(rows, 1)
        target_prob = probabilities.get(
            target, prediction.confidence if prediction.meme == target else 0.0
        )
        rows_data.append(("", target_prob, True))
    for meme, prob in prediction.top(row_limit + int(target is not None)):
        if len(rows_data) >= row_limit:
            break
        if meme != target:
            rows_data.append((_name(meme, catalog), prob, False))
    _draw_bars(canvas, y, rows_data)


def _draw_bars(canvas: np.ndarray, y: int, rows: Sequence[tuple[str, float, bool]]) -> None:
    x0, bar_w, row_h = 260, 700, 38
    for i, (label, raw_prob, is_target) in enumerate(rows):
        prob = float(np.clip(raw_prob, 0.0, 1.0))
        yy = y + i * row_h
        font_size = 20 if is_target else 24
        if label:
            put_text(canvas, label, (x0 - 16 - _width(label, font_size), yy), font_size)
        cv2.rectangle(canvas, (x0, yy + 4), (x0 + bar_w, yy + 28), PANEL_BG, -1)
        color = _progress_color(prob) if is_target else (150, 110, 150)
        fill_w = int(bar_w * prob)
        if fill_w:
            cv2.rectangle(canvas, (x0, yy + 4), (x0 + fill_w - 1, yy + 27), color, -1)
        cv2.rectangle(canvas, (x0, yy + 4), (x0 + bar_w, yy + 28), color, 1)
        value_color = color if is_target else WHITE
        value_size = 32 if is_target else 24
        put_text(
            canvas,
            f"{prob:.0%}",
            (x0 + bar_w + 14, yy),
            value_size,
            value_color,
            bold=True,
        )


def _progress_color(progress: float) -> tuple[int, int, int]:
    """Interpola en BGR de rojo a amarillo y verde sin saltos de color."""
    value = float(np.clip(progress, 0.0, 1.0))
    red, yellow, green = (45, 55, 235), (0, 215, 255), (70, 210, 65)
    if value <= 0.5:
        start, end, amount = red, yellow, value * 2
    else:
        start, end, amount = yellow, green, (value - 0.5) * 2
    return tuple(round(a + (b - a) * amount) for a, b in zip(start, end, strict=True))


def _big(canvas: np.ndarray, text: str, y: int, color=WHITE) -> None:
    put_text(canvas, text, (WIDTH // 2, y), 42, color, bold=True, center=True)


def _small(canvas: np.ndarray, text: str, y: int, color=(200, 200, 200), size: int = 26) -> None:
    put_text(canvas, text, (WIDTH // 2, y), size, color, center=True)


def _name(meme_id: str | None, catalog: dict[str, MemeSpec]) -> str:
    if meme_id in catalog:
        return catalog[meme_id].name
    return {NEUTRAL: "Neutral", UNSURE: "No sé"}.get(meme_id or "", meme_id or "?")


def _width(text: str, size: int) -> int:
    return text_size(text, size)[0]


@cache
def _reference(path: str) -> np.ndarray:
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    return image if image is not None else np.zeros((10, 10, 3), dtype=np.uint8)
