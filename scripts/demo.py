"""La app de la casa abierta: imita un meme y Meme Vision adivina cuál es (spec 009).

Uso:
    python scripts/demo.py                  # modo reto
    python scripts/demo.py --mode free      # modo libre
    python scripts/demo.py --fullscreen

Arranca en la pantalla de inicio (Live WebCat). La cámara y el detector solo se
abren al pulsar Jugar. «Volver a intentar» regresa a esa pantalla y los suelta.

Teclas en el juego: m cambiar de modo · espacio nueva ronda · f pantalla completa · q/Esc salir.
No guarda fotos ni videos: todo se procesa en memoria.
"""

from __future__ import annotations

import argparse

import cv2

from memevision.audio import (
    BACKGROUND_MUSIC,
    CELEBRATION_MUSIC,
    AudioPlayer,
)
from memevision.camera import Camera
from memevision.catalog import load_catalog
from memevision.classifier import MemeClassifier, ModelError
from memevision.features import NoPersonError, transform
from memevision.game import Game, Mode, Phase
from memevision.landmarks import LandmarkDetector
from memevision.leaderboard import load_board, record
from memevision.smoothing import Smoother
from memevision.ui import HEIGHT, WIDTH, button_at, render, render_start

WINDOW = "Live WebCat"
MODES = (Mode.CHALLENGE, Mode.FREE, Mode.LIVE)
NO_MODEL = "Sin modelo: graba datos con scripts/collect.py y entrena con scripts/train.py"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=[m.value for m in MODES], default=Mode.CHALLENGE)
    parser.add_argument("--camera", type=int, default=0, help="índice de la cámara")
    parser.add_argument("--fullscreen", action="store_true")
    args = parser.parse_args()

    catalog = load_catalog()
    try:
        classifier: MemeClassifier | None = MemeClassifier.load()
        banner, mode = "", Mode(args.mode)
    except ModelError as err:
        print(err)
        classifier, banner, mode = None, NO_MODEL, Mode.LIVE

    global _fullscreen
    _fullscreen = args.fullscreen
    view = {"name": "menu"}
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(WINDOW, WIDTH, HEIGHT)
    _set_fullscreen(_fullscreen)

    audio = AudioPlayer()
    try:
        while view["name"] != "quit":
            if view["name"] == "menu":
                _menu_loop(view, audio)
                continue
            _play_loop(view, catalog, classifier, banner, mode, args.camera, audio)
    finally:
        audio.close()
    cv2.destroyAllWindows()


def _menu_loop(view: dict, audio: AudioPlayer) -> None:
    """Pantalla de inicio. No abre la cámara ni el detector."""
    cv2.setMouseCallback(WINDOW, lambda e, x, y, _f, _p: _on_menu_click(e, x, y, view))
    if not audio.is_playing:
        audio.play(BACKGROUND_MUSIC, loop=True)
    while view["name"] == "menu":
        cv2.imshow(WINDOW, render_start())
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            view["name"] = "quit"
        elif key in (13, 10, 32):
            view["name"] = "play"
        elif key == ord("f"):
            _toggle_fullscreen()


def _play_loop(
    view, catalog, classifier, banner, mode, camera_index: int, audio: AudioPlayer
) -> None:
    game = Game(list(catalog), mode=mode)
    smoother = Smoother()
    session = {"name": "", "saved": False, "board": load_board()}
    cv2.setMouseCallback(WINDOW, lambda e, x, y, _f, _p: _on_summary_click(e, x, y, game, view))
    with Camera(camera_index) as camera, LandmarkDetector() as detector:
        if not audio.is_playing:
            audio.play(BACKGROUND_MUSIC, loop=True)
        while view["name"] == "play":
            frame = camera.get_frame()
            landmarks = detector.extract(frame) if frame is not None else None
            visible = landmarks is not None and landmarks.has_person
            prediction = None
            if visible and classifier is not None:
                try:
                    prediction = smoother.update(classifier.predict(transform(landmarks)))
                except NoPersonError:
                    visible = False
            if prediction is None:
                smoother.update(None)

            before = game.state.phase
            state = game.update(visible, prediction, smoother.stable)
            if state.phase == Phase.SUMMARY and before != Phase.SUMMARY:
                audio.play(CELEBRATION_MUSIC)
            if state.phase == Phase.ANALYZING and before != Phase.ANALYZING:
                smoother.reset()  # el resultado mide la pose después de la cuenta, no antes

            cv2.imshow(
                WINDOW,
                render(
                    frame,
                    state,
                    catalog,
                    landmarks,
                    banner,
                    draft_name=session["name"],
                    leaderboard=session["board"],
                ),
            )
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                view["name"] = "quit"
                break
            elif state.phase == Phase.SUMMARY:
                _type_name(key, state.score, session)
            elif key == ord("m") and classifier is not None:
                game.set_mode(MODES[(MODES.index(game.mode) + 1) % len(MODES)])
                smoother.reset()
            elif key == ord(" "):
                game.next_round()
                smoother.reset()
            elif key == ord("f"):
                _toggle_fullscreen()
            if state.phase == Phase.SUMMARY and audio.finished:
                audio.stop()
                view["name"] = "menu"
                break
    if view["name"] != "menu":
        audio.stop()


def _on_menu_click(event: int, x: int, y: int, view: dict) -> None:
    if event == cv2.EVENT_LBUTTONDOWN and button_at(*_to_canvas(x, y)) == "start":
        view["name"] = "play"


def _on_summary_click(event: int, x: int, y: int, game: Game, view: dict) -> None:
    if event != cv2.EVENT_LBUTTONDOWN or game.state.phase != Phase.SUMMARY:
        return
    if button_at(*_to_canvas(x, y)) == "retry":
        view["name"] = "menu"


_fullscreen = False


def _toggle_fullscreen() -> None:
    global _fullscreen
    _fullscreen = not _fullscreen
    _set_fullscreen(_fullscreen)


def _to_canvas(x: int, y: int) -> tuple[int, int]:
    try:
        _x, _y, w, h = cv2.getWindowImageRect(WINDOW)
    except cv2.error:
        w, h = WIDTH, HEIGHT
    if w <= 0 or h <= 0:
        return x, y
    return int(x * WIDTH / w), int(y * HEIGHT / h)


def _type_name(key: int, score: int, session: dict) -> None:
    if session["saved"]:
        return
    if key in (13, 10):
        name = session["name"].strip()
        if name:
            session["board"] = record(name, score)
            session["saved"] = True
        return
    if key in (8, 127):
        session["name"] = session["name"][:-1]
    elif 32 <= key < 127 and len(session["name"]) < 16:
        session["name"] += chr(key)


def _set_fullscreen(on: bool) -> None:
    flag = cv2.WINDOW_FULLSCREEN if on else cv2.WINDOW_NORMAL
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, flag)


if __name__ == "__main__":
    main()
