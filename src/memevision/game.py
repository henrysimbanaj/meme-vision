"""Máquina de estados del juego de la feria, sin dibujo (spec 009)."""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from memevision.contracts import NEUTRAL, UNSURE, Prediction

_EPS = 1e-6


class Mode(StrEnum):
    CHALLENGE = "challenge"
    FREE = "free"
    LIVE = "live"


class Phase(StrEnum):
    SEARCHING = "searching"
    DETECTED = "detected"
    COUNTDOWN = "countdown"
    ANALYZING = "analyzing"
    RESULT = "result"
    LIVE = "live"
    SUMMARY = "summary"


ROUNDS_PER_GAME = 10


def points_for(prediction: Prediction, target: str | None) -> int:
    """0–100 según la probabilidad del meme que está en pantalla."""
    if not target:
        return 0
    raw = prediction.probabilities.get(target)
    if raw is None and prediction.meme == target:
        raw = prediction.confidence
    if raw is None:
        return 0
    return int(round(min(1.0, max(0.0, float(raw))) * 100))


@dataclass(frozen=True)
class Timings:
    detect_s: float = 1.0
    countdown_s: float = 3.0
    analyze_max_s: float = 3.0
    result_s: float = 5.0
    lost_s: float = 1.5


@dataclass(frozen=True)
class GameState:
    mode: Mode
    phase: Phase
    round: int
    target: str | None
    remaining_s: float = 0.0
    live: Prediction | None = None
    result: Prediction | None = None
    success: bool | None = None
    person_visible: bool = False
    score: int = 0
    round_points: int = 0
    total_rounds: int = ROUNDS_PER_GAME


class Game:
    def __init__(
        self,
        meme_ids: Sequence[str],
        mode: Mode = Mode.CHALLENGE,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.monotonic,
        timings: Timings | None = None,
        rounds: int = ROUNDS_PER_GAME,
    ):
        self._targets = [m for m in meme_ids if m != NEUTRAL]
        self._rng = rng or random.Random()
        self._clock = clock
        self.timings = timings or Timings()
        self.mode = mode
        self.rounds = rounds
        self._round = 0
        self._score = 0
        self._round_points = 0
        self._target: str | None = None
        self._live: Prediction | None = None
        self._deck: list[str] = []
        self._last_seen = clock()
        self._visible = False
        self._deck = self._make_deck()
        self.next_round()

    # --- API pública -------------------------------------------------------------------------

    def update(
        self, person_visible: bool, prediction: Prediction | None, stable: bool
    ) -> GameState:
        now = self._clock()
        self._visible = person_visible
        if person_visible:
            self._last_seen = now
        self._live = prediction
        if self.mode != Mode.LIVE:
            self._step(now, person_visible, prediction, stable)
        return self.state

    def set_mode(self, mode: Mode) -> GameState:
        self.mode = mode
        self._round = 0
        self._score = 0
        self._round_points = 0
        self._deck = self._make_deck()
        return self.next_round()

    def play_again(self) -> GameState:
        """Nueva partida de 10 memes, con el puntaje en cero."""
        self._round = 0
        self._score = 0
        self._round_points = 0
        self._deck = self._make_deck()
        return self.next_round()

    def next_round(self) -> GameState:
        self._round += 1
        self._result: Prediction | None = None
        self._last_prediction: Prediction | None = None
        self._round_points = 0
        self._target = self._pick_target() if self.mode == Mode.CHALLENGE else None
        self._enter(Phase.LIVE if self.mode == Mode.LIVE else Phase.SEARCHING)
        return self.state

    @property
    def state(self) -> GameState:
        durations = {
            Phase.DETECTED: self.timings.detect_s,
            Phase.COUNTDOWN: self.timings.countdown_s,
            Phase.ANALYZING: self.timings.analyze_max_s,
            Phase.RESULT: self.timings.result_s,
        }
        elapsed = self._clock() - self._phase_start
        remaining = max(durations.get(self._phase, 0.0) - elapsed, 0.0)
        success = None
        if self._result is not None and self.mode == Mode.CHALLENGE:
            success = self._result.meme == self._target
        return GameState(
            mode=self.mode,
            phase=self._phase,
            round=self._round,
            target=self._target,
            remaining_s=remaining,
            live=self._live,
            result=self._result,
            success=success,
            person_visible=self._visible,
            score=self._score,
            round_points=self._round_points,
            total_rounds=self.rounds,
        )

    # --- transiciones ------------------------------------------------------------------------

    def _step(self, now: float, visible: bool, prediction: Prediction | None, stable: bool) -> None:
        t = self.timings
        elapsed = now - self._phase_start
        phase = self._phase
        if phase in (Phase.DETECTED, Phase.COUNTDOWN, Phase.ANALYZING):
            if now - self._last_seen > t.lost_s:
                self._enter(Phase.SEARCHING)
                return

        if phase == Phase.SEARCHING and visible:
            self._enter(Phase.DETECTED)
        elif phase == Phase.DETECTED and elapsed >= t.detect_s - _EPS:
            self._enter(Phase.COUNTDOWN)
        elif phase == Phase.COUNTDOWN and elapsed >= t.countdown_s - _EPS:
            self._last_prediction = None
            self._enter(Phase.ANALYZING)
        elif phase == Phase.ANALYZING:
            if prediction is not None:
                self._last_prediction = prediction
            if elapsed >= t.analyze_max_s - _EPS:
                self._finish(self._last_prediction or Prediction(UNSURE, 0.0))
        elif phase == Phase.RESULT and elapsed >= t.result_s - _EPS:
            if self.mode == Mode.CHALLENGE and self._round >= self.rounds:
                self._enter(Phase.SUMMARY)
            else:
                self.next_round()

    def _finish(self, result: Prediction) -> None:
        self._result = result
        if self.mode == Mode.CHALLENGE:
            self._round_points = points_for(result, self._target)
            self._score += self._round_points
        self._enter(Phase.RESULT)

    def _enter(self, phase: Phase) -> None:
        self._phase = phase
        self._phase_start = self._clock()

    def _make_deck(self) -> list[str]:
        """10 memes de la partida. Si hay 10 o más, sin repetir; si hay menos, se rellenan."""
        pool = list(self._targets)
        if not pool:
            return []
        if len(pool) >= self.rounds:
            return self._rng.sample(pool, self.rounds)
        deck: list[str] = []
        while len(deck) < self.rounds:
            options = [m for m in pool if not deck or m != deck[-1]] or pool
            self._rng.shuffle(options)
            for meme in options:
                if deck and meme == deck[-1] and len(pool) > 1:
                    continue
                deck.append(meme)
                if len(deck) == self.rounds:
                    break
        return deck

    def _pick_target(self) -> str | None:
        if not self._targets:
            return None
        index = self._round - 1
        if 0 <= index < len(self._deck):
            return self._deck[index]
        options = [m for m in self._targets if m != self._target] or self._targets
        return self._rng.choice(options)
