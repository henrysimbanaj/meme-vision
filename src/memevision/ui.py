"""Dibujo de la app de feria: un lienzo 1280x720 por cada GameState (spec 009)."""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache

import cv2
import numpy as np

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
BG = (45, 20, 40)  # morado oscuro (BGR)
PANEL_BG = (30, 12, 28)
ACCENT = (200, 120, 255)  # rosa

MODE_NAMES = {Mode.CHALLENGE: "Reto", Mode.FREE: "Libre", Mode.LIVE: "En vivo"}
CONTROLS = "m: modo · espacio: nueva ronda · f: pantalla completa · q: salir"
# Lienzo 1280x720. La demo traduce el clic de la ventana a estas coordenadas.
START_BUTTON = (440, 390, 400, 70)
RETRY_BUTTON = (440, 628, 400, 58)
GAME_TITLE = "Live WebCat"


def button_at(x: int, y: int) -> str | None:
    """Devuelve 'start' en «Jugar» o 'retry' en «Volver a intentar»."""
    for name, rect in (("start", START_BUTTON), ("retry", RETRY_BUTTON)):
        x0, y0, w, h = rect
        if x0 <= x < x0 + w and y0 <= y < y0 + h:
            return name
    return None


def render_start() -> np.ndarray:
    """Pantalla de inicio, sin cámara: solo el nombre del juego y «Jugar»."""
    canvas = np.full((HEIGHT, WIDTH, 3), BG, dtype=np.uint8)
    put_text(canvas, GAME_TITLE, (HALF, 250), 84, ACCENT, bold=True, center=True)
    x0, y0, w, h = START_BUTTON
    cv2.rectangle(canvas, (x0, y0), (x0 + w, y0 + h), ACCENT, -1)
    put_text(canvas, "Jugar", (x0 + w // 2, y0 + h // 2), 36, BG, bold=True, center=True)
    hint = "Enter o espacio para jugar · f: pantalla completa · q: salir"
    put_text(canvas, hint, (HALF, HEIGHT - 48), 20, (170,) * 3, center=True)
    return canvas


def render(
    frame: np.ndarray | None,
    state: GameState,
    catalog: dict[str, MemeSpec],
    landmarks: LandmarkResult | None = None,
    banner: str = "",
    draft_name: str = "",
    leaderboard: list[tuple[str, int]] | None = None,
) -> np.ndarray:
    canvas = np.full((HEIGHT, WIDTH, 3), BG, dtype=np.uint8)
    if state.phase == Phase.SUMMARY:
        _summary(canvas, state, draft_name, leaderboard or [])
        return canvas
    _header(canvas, state)
    _camera(canvas, frame, state, landmarks)
    _right_panel(canvas, state, catalog)
    _footer(canvas, state, catalog)
    if banner:
        cv2.rectangle(canvas, (0, HEADER), (WIDTH, HEADER + 34), RED, -1)
        put_text(canvas, banner, (HALF, HEADER + 17), 22, WHITE, True, outline=None, center=True)
    return canvas


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
    canvas: np.ndarray, frame: np.ndarray | None, state: GameState, lm: LandmarkResult | None
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
        put_text(view, number, center, 200, YELLOW, bold=True, center=True)
    elif state.phase == Phase.ANALYZING:
        dots = "." * (1 + int(state.remaining_s * 3) % 3)
        darken(view, BODY // 2 - 40, BODY // 2 + 40)
        put_text(view, f"Analizando{dots}", center, 44, WHITE, bold=True, center=True)
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


def _footer(canvas: np.ndarray, state: GameState, catalog: dict[str, MemeSpec]) -> None:
    y = FOOTER_Y + 40
    phase, mode = state.phase, state.mode
    if phase == Phase.DETECTED:
        _big(canvas, "¡Te veo! Prepárate…", y, YELLOW)
    elif phase == Phase.COUNTDOWN:
        msg = "¡Imita el meme!" if mode == Mode.CHALLENGE else "¡Imita un meme!"
        _big(canvas, msg, y, YELLOW)
    elif phase == Phase.ANALYZING:
        _big(canvas, "Calificando...", y - 10)
        _bars(canvas, state.live, catalog, y + 30)
    elif phase == Phase.RESULT and state.result is not None:
        _result(canvas, state, catalog, y)
    elif phase == Phase.LIVE:
        if state.live is None and state.person_visible:
            _big(canvas, "¡Te veo!", y, YELLOW)
        elif state.live is not None:
            _bars(canvas, state.live, catalog, y - 20, rows=3)
    put_text(canvas, CONTROLS, (WIDTH - 12 - _width(CONTROLS, 16), HEIGHT - 26), 16, (170,) * 3)


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
    return "Suerte en la próxima!"


def _result(canvas: np.ndarray, state: GameState, catalog: dict[str, MemeSpec], y: int) -> None:
    result = state.result
    if state.mode == Mode.CHALLENGE:
        _big(canvas, feedback_for(state.round_points), y, WHITE)
    elif result.meme == NEUTRAL:
        _big(canvas, "No estás imitando ningún meme", y, YELLOW)
    elif result.meme != UNSURE:
        _big(canvas, feedback_for(int(round(result.confidence * 100))), y, WHITE)
    if state.mode == Mode.CHALLENGE:
        score_y = y + 58
        put_text(
            canvas,
            f"+{state.round_points} pts por este meme · Total {state.score}",
            (WIDTH // 2, score_y),
            52,
            YELLOW,
            bold=True,
            center=True,
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
) -> None:
    if prediction is None:
        return
    rows_data = [(_name(meme, catalog), prob) for meme, prob in prediction.top(rows)]
    _draw_bars(canvas, y, rows_data)


def _draw_bars(canvas: np.ndarray, y: int, rows: Sequence[tuple[str, float]]) -> None:
    x0, bar_w, row_h = 260, 700, 38
    for i, (label, prob) in enumerate(rows):
        yy = y + i * row_h
        put_text(canvas, label, (x0 - 16 - _width(label, 24), yy), 24)
        cv2.rectangle(canvas, (x0, yy + 4), (x0 + bar_w, yy + 28), PANEL_BG, -1)
        color = ACCENT if i == 0 else (150, 110, 150)
        cv2.rectangle(canvas, (x0, yy + 4), (x0 + int(bar_w * prob), yy + 28), color, -1)
        put_text(canvas, f"{prob:.0%}", (x0 + bar_w + 14, yy), 24)


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
