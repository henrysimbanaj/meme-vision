"""La app de la casa abierta: imita un meme y Meme Vision adivina cuál es (spec 009).

Uso:
    python scripts/demo.py                  # modo reto
    python scripts/demo.py --mode free      # modo libre
    python scripts/demo.py --fullscreen

Teclas: m cambiar de modo · espacio nueva ronda · f pantalla completa · q/Esc salir.
No guarda fotos ni videos: todo se procesa en memoria.
"""

from __future__ import annotations

import argparse

import cv2

from memevision.camera import Camera
from memevision.catalog import load_catalog
from memevision.classifier import MemeClassifier, ModelError
from memevision.features import NoPersonError, transform
from memevision.game import Game, Mode, Phase
from memevision.landmarks import LandmarkDetector
from memevision.smoothing import Smoother
from memevision.ui import HEIGHT, WIDTH, render

WINDOW = "Meme Vision"
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

    game = Game(list(catalog), mode=mode)
    smoother = Smoother()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(WINDOW, WIDTH, HEIGHT)
    fullscreen = args.fullscreen
    _set_fullscreen(fullscreen)

    with Camera(args.camera) as camera, LandmarkDetector() as detector:
        while True:
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
            if state.phase == Phase.ANALYZING and before != Phase.ANALYZING:
                smoother.reset()  # el resultado mide la pose después de la cuenta, no antes

            cv2.imshow(WINDOW, render(frame, state, catalog, landmarks, banner))
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
            if key == ord("m") and classifier is not None:
                game.set_mode(MODES[(MODES.index(game.mode) + 1) % len(MODES)])
                smoother.reset()
            elif key == ord(" "):
                game.next_round()
                smoother.reset()
            elif key == ord("f"):
                fullscreen = not fullscreen
                _set_fullscreen(fullscreen)
    cv2.destroyAllWindows()


def _set_fullscreen(on: bool) -> None:
    flag = cv2.WINDOW_FULLSCREEN if on else cv2.WINDOW_NORMAL
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, flag)


if __name__ == "__main__":
    main()
