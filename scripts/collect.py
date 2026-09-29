"""Graba vectores de features de una persona imitando un meme (spec 005).

Uso:
    python scripts/collect.py michi-fuerza --person P01
    python scripts/collect.py neutral --person P01 --seconds 30

No guarda imágenes: solo números en data/raw/ (que no va a git).
"""

from __future__ import annotations

import argparse

import cv2
import numpy as np

from memevision.camera import Camera
from memevision.catalog import load_catalog
from memevision.collector import CollectState, run_collection
from memevision.contracts import NEUTRAL
from memevision.dataset import DatasetError, SessionWriter
from memevision.drawing import GREEN, RED, YELLOW, darken, draw_landmarks, fit_image, put_text
from memevision.landmarks import LandmarkDetector

WINDOW = "Meme Vision - recolector"
PANEL_W = 400


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("label", help="id del meme (ver memes/catalog/) o 'neutral'")
    parser.add_argument("--person", required=True, help="ID anónimo: P01, P02, …")
    parser.add_argument("--camera", type=int, default=0, help="índice de la cámara")
    parser.add_argument("--countdown", type=float, default=3.0, help="segundos antes de grabar")
    parser.add_argument("--seconds", type=float, default=20.0, help="segundos de grabación")
    args = parser.parse_args()

    try:  # valida label y person antes de abrir la cámara
        writer = SessionWriter(args.label, args.person)
    except DatasetError as err:
        parser.error(str(err))
    panel = _reference_panel(args.label)

    def show(frame: np.ndarray | None, state: CollectState) -> bool:
        if frame is None:
            return cv2.waitKey(1) & 0xFF not in (ord("q"), 27)
        view = frame.copy()
        draw_landmarks(view, state.landmarks)
        _draw_status(view, args, state)
        panel_h = fit_image(panel, PANEL_W, view.shape[0]) if panel is not None else None
        canvas = view if panel_h is None else np.hstack((view, panel_h))
        cv2.imshow(WINDOW, canvas)
        key = cv2.waitKey(1) & 0xFF
        return (
            key not in (ord("q"), 27) and cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) >= 1
        )

    with Camera(args.camera) as camera, LandmarkDetector() as detector, writer:
        cv2.namedWindow(WINDOW)
        n = run_collection(camera, detector, writer, args.countdown, args.seconds, show)
    cv2.destroyAllWindows()

    if n:
        print(f"Guardadas {n} muestras en data/raw/sessions/{writer.session}.csv")
    else:
        print("No se guardó ninguna muestra.")


def _reference_panel(label: str) -> np.ndarray:
    panel = np.full((480, PANEL_W, 3), 30, dtype=np.uint8)
    if label == NEUTRAL:
        put_text(panel, "Neutral", (PANEL_W // 2, 180), 40, bold=True, center=True)
        put_text(panel, "Parado normal,", (PANEL_W // 2, 250), 24, center=True)
        put_text(panel, "sin imitar nada", (PANEL_W // 2, 285), 24, center=True)
        return panel
    meme = load_catalog()[label]
    image = cv2.imread(meme.image_path)
    panel = fit_image(image, PANEL_W, 480, background=(30, 30, 30))
    top = 480 - 34 * len(meme.traits)
    darken(panel, top, 480, alpha=0.7)
    for i, trait in enumerate(meme.traits):
        put_text(panel, f"• {trait}", (10, top + 34 * i + 5), 20)
    return panel


def _draw_status(view: np.ndarray, args: argparse.Namespace, state: CollectState) -> None:
    h, w = view.shape[:2]
    darken(view, 0, 44)
    put_text(view, f"{args.label} · {args.person}", (10, 8), 24, bold=True)
    put_text(view, "q: cancelar", (w - 140, 12), 18)
    if state.phase == "countdown":
        put_text(
            view, str(int(state.remaining_s) + 1), (w // 2, h // 2), 140, YELLOW, True, center=True
        )
        put_text(view, "¡Prepárate!", (w // 2, h // 2 + 110), 36, bold=True, center=True)
    else:
        darken(view, h - 44, h)
        cv2.circle(view, (22, h - 22), 9, RED, -1, cv2.LINE_AA)
        info = f"Grabando · {state.remaining_s:4.1f} s · {state.samples} muestras"
        put_text(view, info, (40, h - 36), 24, GREEN if state.person_visible else RED)
    if not state.person_visible:
        put_text(
            view, "No te veo: ponte frente a la cámara", (w // 2, 70), 26, RED, True, center=True
        )


if __name__ == "__main__":
    main()
