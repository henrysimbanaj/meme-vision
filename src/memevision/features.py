"""LandmarkResult -> vector de features de longitud fija (spec 003).

Todo se normaliza con el punto medio de los hombros como origen y la distancia entre hombros
como unidad, así el vector no depende de la distancia a la cámara ni de la posición.
"""

from __future__ import annotations

import numpy as np

from memevision.contracts import LandmarkResult

FEATURE_VERSION = "1.0"

# Índices de MediaPipe Pose
_POSE_POINTS = {
    "nose": 0,
    "left_eye": 2,
    "right_eye": 5,
    "left_ear": 7,
    "right_ear": 8,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
}
_POSE_MOUTH = (9, 10)
_FACE_LIPS = (13, 14)  # labio superior e inferior en FaceLandmarker (478 puntos)

# Índices de MediaPipe Hand: (base, punta) de cada dedo. El pulgar usa su MCP como base.
_FINGERS = {
    "thumb": (2, 4),
    "index": (5, 8),
    "middle": (9, 12),
    "ring": (13, 16),
    "pinky": (17, 20),
}
_HAND_WRIST, _INDEX_MCP, _INDEX_TIP, _MIDDLE_MCP, _PINKY_MCP = 0, 5, 8, 9, 17

BLENDSHAPES = (
    "jawOpen",
    "mouthSmileLeft",
    "mouthSmileRight",
    "mouthFrownLeft",
    "mouthFrownRight",
    "mouthPucker",
    "mouthFunnel",
    "mouthPressLeft",
    "mouthPressRight",
    "eyeBlinkLeft",
    "eyeBlinkRight",
    "eyeWideLeft",
    "eyeWideRight",
    "eyeSquintLeft",
    "eyeSquintRight",
    "browInnerUp",
    "browDownLeft",
    "browDownRight",
    "browOuterUpLeft",
    "browOuterUpRight",
    "cheekPuff",
)

# Umbrales de las relaciones, en unidades de "distancia entre hombros"
HAND_ON_FACE = 0.5
HANDS_TOGETHER = 0.35
ABOVE_HEAD = 0.2  # la muñeca está al menos esto por encima de la nariz
ARMS_UP = 0.5  # la muñeca está al menos esto por encima de la línea de hombros
MIN_SHOULDER_WIDTH = 1e-3
_EPS = 1e-9

_SIDES = ("left", "right")
_HAND_FIELDS = (
    "present",
    *(f"ext_{f}" for f in _FINGERS),
    "palm_normal_y",
    "palm_normal_z",
    "index_dir_x",
    "index_dir_y",
    "index_tip_mouth",
)

FEATURE_NAMES: tuple[str, ...] = (
    *(f"pose_{p}_{c}" for p in _POSE_POINTS for c in ("x", "y")),
    *(f"angle_elbow_{s}" for s in _SIDES),
    *(f"angle_shoulder_{s}" for s in _SIDES),
    "angle_shoulder_tilt",
    "angle_head_roll",
    "angle_head_yaw",
    *(f"dist_wrist_nose_{s}" for s in _SIDES),
    *(f"dist_wrist_mouth_{s}" for s in _SIDES),
    *(f"dist_wrist_opposite_shoulder_{s}" for s in _SIDES),
    "dist_wrists",
    "dist_head_pitch",
    *(f"depth_wrist_{s}" for s in _SIDES),
    *(f"rel_hand_above_head_{s}" for s in _SIDES),
    *(f"rel_hand_on_face_{s}" for s in _SIDES),
    "rel_hands_together",
    "rel_arms_crossed",
    "rel_both_arms_up",
    *(f"hand_{s}_{f}" for s in _SIDES for f in _HAND_FIELDS),
    "face_present",
    *(f"face_{b}" for b in BLENDSHAPES),
)


class NoPersonError(ValueError):
    """No hay una persona utilizable en el frame (sin pose, o de perfil)."""


def transform(lm: LandmarkResult) -> np.ndarray:
    if lm.pose is None:
        raise NoPersonError("No hay pose en el frame")
    pose = np.asarray(lm.pose, dtype=np.float64)
    ls, rs = pose[_POSE_POINTS["left_shoulder"]], pose[_POSE_POINTS["right_shoulder"]]
    origin = (ls + rs) / 2
    scale = float(np.linalg.norm(ls[:2] - rs[:2]))
    if scale < MIN_SHOULDER_WIDTH:
        raise NoPersonError("Distancia entre hombros ≈ 0 (¿persona de perfil?)")

    def norm(points: np.ndarray) -> np.ndarray:
        return (np.asarray(points, dtype=np.float64) - origin) / scale

    p = {name: norm(pose[idx]) for name, idx in _POSE_POINTS.items()}
    mouth = norm(_mouth(lm, pose))
    left_hand = None if lm.left_hand is None else norm(lm.left_hand)
    right_hand = None if lm.right_hand is None else norm(lm.right_hand)

    f: dict[str, float] = {}
    for name, xyz in p.items():
        f[f"pose_{name}_x"], f[f"pose_{name}_y"] = xyz[0], xyz[1]

    _add_angles(f, p)
    _add_distances(f, p, mouth)
    _add_relations(f, p, mouth, {"left": left_hand, "right": right_hand})
    for side, hand in (("left", left_hand), ("right", right_hand)):
        _add_hand(f, side, hand, mouth)
    _add_face(f, lm.face_blendshapes)

    return np.array([f[name] for name in FEATURE_NAMES], dtype=np.float32)


def _mouth(lm: LandmarkResult, pose: np.ndarray) -> np.ndarray:
    if lm.face is not None:
        face = np.asarray(lm.face, dtype=np.float64)
        return face[list(_FACE_LIPS)].mean(axis=0)
    return pose[list(_POSE_MOUTH)].mean(axis=0)


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a[:2] - b[:2]))


def _angle(a: np.ndarray, vertex: np.ndarray, b: np.ndarray) -> float:
    """Ángulo en `vertex` (radianes, 0..π) en el plano de la imagen."""
    u, v = a[:2] - vertex[:2], b[:2] - vertex[:2]
    cos = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + _EPS)
    return float(np.arccos(np.clip(cos, -1.0, 1.0)))


def _line_tilt(a: np.ndarray, b: np.ndarray) -> float:
    """Inclinación de la línea a–b en (-π/2, π/2], sin importar cuál punto queda a la izquierda."""
    v = b[:2] - a[:2]
    if v[0] < 0:
        v = -v
    return float(np.arctan2(v[1], v[0] + _EPS))


def _add_angles(f: dict[str, float], p: dict[str, np.ndarray]) -> None:
    for side, other in (("left", "right"), ("right", "left")):
        shoulder, elbow, wrist = p[f"{side}_shoulder"], p[f"{side}_elbow"], p[f"{side}_wrist"]
        f[f"angle_elbow_{side}"] = _angle(shoulder, elbow, wrist)
        f[f"angle_shoulder_{side}"] = _angle(elbow, shoulder, p[f"{other}_shoulder"])
    f["angle_shoulder_tilt"] = _line_tilt(p["left_shoulder"], p["right_shoulder"])
    f["angle_head_roll"] = _line_tilt(p["left_eye"], p["right_eye"])
    ears_mid = (p["left_ear"] + p["right_ear"]) / 2
    ears_width = _dist(p["left_ear"], p["right_ear"])
    f["angle_head_yaw"] = float((p["nose"][0] - ears_mid[0]) / (ears_width + _EPS))


def _add_distances(f: dict[str, float], p: dict[str, np.ndarray], mouth: np.ndarray) -> None:
    for side, other in (("left", "right"), ("right", "left")):
        wrist = p[f"{side}_wrist"]
        f[f"dist_wrist_nose_{side}"] = _dist(wrist, p["nose"])
        f[f"dist_wrist_mouth_{side}"] = _dist(wrist, mouth)
        f[f"dist_wrist_opposite_shoulder_{side}"] = _dist(wrist, p[f"{other}_shoulder"])
        f[f"depth_wrist_{side}"] = float(wrist[2])  # z relativa al punto medio de los hombros
    f["dist_wrists"] = _dist(p["left_wrist"], p["right_wrist"])
    ears_mid = (p["left_ear"] + p["right_ear"]) / 2
    f["dist_head_pitch"] = float(p["nose"][1] - ears_mid[1])


def _add_relations(
    f: dict[str, float],
    p: dict[str, np.ndarray],
    mouth: np.ndarray,
    hands: dict[str, np.ndarray | None],
) -> None:
    for side in _SIDES:
        wrist, hand = p[f"{side}_wrist"], hands[side]
        f[f"rel_hand_above_head_{side}"] = float(wrist[1] < p["nose"][1] - ABOVE_HEAD)
        touch_points = [wrist] if hand is None else [wrist, hand[_INDEX_TIP], hand[_MIDDLE_MCP]]
        near = min(min(_dist(t, mouth), _dist(t, p["nose"])) for t in touch_points)
        f[f"rel_hand_on_face_{side}"] = float(near < HAND_ON_FACE)
    f["rel_hands_together"] = float(f["dist_wrists"] < HANDS_TOGETHER)
    # Brazos cruzados: cada muñeca queda del lado del hombro contrario (x relativa al origen).
    lw, rw = p["left_wrist"][0], p["right_wrist"][0]
    ls, rs = p["left_shoulder"][0], p["right_shoulder"][0]
    f["rel_arms_crossed"] = float(np.sign(lw) == np.sign(rs) and np.sign(rw) == np.sign(ls))
    f["rel_both_arms_up"] = float(p["left_wrist"][1] < -ARMS_UP and p["right_wrist"][1] < -ARMS_UP)


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / n if n > _EPS else np.zeros_like(v)


def _add_hand(f: dict[str, float], side: str, hand: np.ndarray | None, mouth: np.ndarray) -> None:
    prefix = f"hand_{side}_"
    if hand is None:
        for field in _HAND_FIELDS:
            f[prefix + field] = 0.0
        return
    wrist = hand[_HAND_WRIST]
    f[prefix + "present"] = 1.0
    for finger, (base, tip) in _FINGERS.items():
        base_len = np.linalg.norm(hand[base] - wrist)
        f[prefix + f"ext_{finger}"] = float(np.linalg.norm(hand[tip] - wrist) / (base_len + _EPS))
    normal = _unit(np.cross(hand[_INDEX_MCP] - wrist, hand[_PINKY_MCP] - wrist))
    f[prefix + "palm_normal_y"], f[prefix + "palm_normal_z"] = normal[1], normal[2]
    direction = _unit(hand[_INDEX_TIP][:2] - hand[_INDEX_MCP][:2])
    f[prefix + "index_dir_x"], f[prefix + "index_dir_y"] = direction[0], direction[1]
    f[prefix + "index_tip_mouth"] = _dist(hand[_INDEX_TIP], mouth)


def _add_face(f: dict[str, float], blendshapes: dict[str, float] | None) -> None:
    f["face_present"] = float(blendshapes is not None)
    for name in BLENDSHAPES:
        f[f"face_{name}"] = float((blendshapes or {}).get(name, 0.0))
