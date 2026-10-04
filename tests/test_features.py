import json
from pathlib import Path

import numpy as np
import pytest
from factories import face, full_person, hand, person, pose, transformed

from memevision.contracts import LandmarkResult
from memevision.features import FEATURE_NAMES, FEATURE_VERSION, NoPersonError, transform

SNAPSHOT_DIR = Path(__file__).parent / "fixtures" / "features"


def as_dict(vec: np.ndarray) -> dict[str, float]:
    return dict(zip(FEATURE_NAMES, vec.tolist(), strict=True))


def test_FEAT_01_hombros_normalizados_al_origen_y_distancia_1():
    f = as_dict(transform(person(pose(l_shoulder=(0.4, 0.5), r_shoulder=(0.6, 0.5)))))
    mid = (
        (f["pose_left_shoulder_x"] + f["pose_right_shoulder_x"]) / 2,
        (f["pose_left_shoulder_y"] + f["pose_right_shoulder_y"]) / 2,
    )
    assert mid == pytest.approx((0.0, 0.0), abs=1e-6)
    dist = abs(f["pose_right_shoulder_x"] - f["pose_left_shoulder_x"])
    assert dist == pytest.approx(1.0, abs=1e-6)


@pytest.mark.parametrize("center", [(0.0, 0.0, 0.0), (0.5, 0.5, 0.0), (0.9, 0.1, 0.3)])
def test_FEAT_02_invariante_a_escala(center):
    lm = full_person()
    c = np.array(center)
    scaled = transformed(lm, lambda a: (a - c) * 2 + c)
    np.testing.assert_allclose(transform(scaled), transform(lm), atol=1e-5)


def test_FEAT_03_invariante_a_traslacion():
    lm = full_person()
    moved = transformed(lm, lambda a: a + np.array([0.13, -0.07, 0.05]))
    np.testing.assert_allclose(transform(moved), transform(lm), atol=1e-5)


def test_FEAT_04_codo_en_angulo_recto_mide_90_grados():
    p = pose(l_shoulder=(0.6, 0.5), l_elbow=(0.6, 0.7), l_wrist=(0.7, 0.7))
    f = as_dict(transform(person(p)))
    assert np.degrees(f["angle_elbow_left"]) == pytest.approx(90.0, abs=0.5)


@pytest.mark.parametrize(
    "lm",
    [
        person(),
        full_person(),
        person(left_hand=hand((0.5, 0.3))),
        person(face_arr=face(), blendshapes={}),
        person(pose(l_wrist=(0.6, 0.5), r_wrist=(0.6, 0.5))),  # muñeca sobre el hombro
    ],
)
def test_FEAT_05_longitud_fija_y_sin_nan(lm):
    vec = transform(lm)
    assert vec.shape == (len(FEATURE_NAMES),)
    assert vec.dtype == np.float32
    assert np.all(np.isfinite(vec))


def test_FEAT_06_mano_ausente_bloque_en_cero_y_flag_0():
    f = as_dict(transform(person(right_hand=hand((0.36, 0.8)))))
    left_block = {k: v for k, v in f.items() if k.startswith("hand_left_")}
    assert left_block and all(v == 0.0 for v in left_block.values())
    assert f["hand_right_present"] == 1.0


def test_FEAT_06_cara_ausente_bloque_en_cero_y_flag_0():
    f = as_dict(transform(person()))
    face_block = {k: v for k, v in f.items() if k.startswith("face_")}
    assert face_block and all(v == 0.0 for v in face_block.values())


def test_FEAT_07_nombres_coinciden_con_snapshot_de_la_version():
    snapshot = SNAPSHOT_DIR / f"v{FEATURE_VERSION}.json"
    assert snapshot.exists(), f"Falta el snapshot {snapshot.name}: créalo al subir FEATURE_VERSION"
    assert json.loads(snapshot.read_text()) == list(FEATURE_NAMES), (
        "FEATURE_NAMES cambió: sube FEATURE_VERSION, crea su snapshot, actualiza la spec 003 "
        "y escribe un ADR"
    )


def test_FEAT_08_sin_pose_lanza_no_person_error():
    with pytest.raises(NoPersonError):
        transform(LandmarkResult())


def test_FEAT_08_hombros_superpuestos_lanza_no_person_error():
    with pytest.raises(NoPersonError):
        transform(person(pose(l_shoulder=(0.5, 0.5), r_shoulder=(0.5, 0.5))))


def test_FEAT_09_solo_indice_extendido():
    only_index = hand((0.4, 0.5), extended=(False, True, False, False, False))
    f = as_dict(transform(person(right_hand=only_index)))
    idx = f["hand_right_ext_index"]
    for other in ("middle", "ring", "pinky"):
        assert idx > f[f"hand_right_ext_{other}"] + 0.3


def test_FEAT_10_indice_sobre_la_boca():
    # punta del índice (0.40, 0.5 - 0.08 * 2.05) ≈ (0.40, 0.336): sobre la boca en (0.40, 0.34)
    silence = hand((0.40, 0.50), extended=(False, True, False, False, False))
    p = pose(r_wrist=(0.40, 0.50), nose=(0.40, 0.30), mouth_l=(0.41, 0.34), mouth_r=(0.39, 0.34))
    f = as_dict(transform(person(p, right_hand=silence, face_arr=face(mouth=(0.40, 0.34)))))
    assert f["hand_right_index_tip_mouth"] < 0.2
    assert f["rel_hand_on_face_right"] == 1.0
    assert f["rel_hand_on_face_left"] == 0.0


def test_relacion_ambos_brazos_arriba():
    p = pose(l_elbow=(0.7, 0.4), r_elbow=(0.3, 0.4), l_wrist=(0.7, 0.2), r_wrist=(0.3, 0.2))
    f = as_dict(transform(person(p)))
    assert f["rel_both_arms_up"] == 1.0
    assert as_dict(transform(person()))["rel_both_arms_up"] == 0.0


def test_blendshapes_se_copian_y_los_ausentes_valen_0():
    f = as_dict(transform(person(face_arr=face(), blendshapes={"jawOpen": 0.8})))
    assert f["face_present"] == 1.0
    assert f["face_jawOpen"] == pytest.approx(0.8)
    assert f["face_cheekPuff"] == 0.0
