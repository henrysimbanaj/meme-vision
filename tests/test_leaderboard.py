from memevision.leaderboard import load_board, record


def test_UX_14_guardar_nombre_y_puntaje_ordena_de_mayor_a_menor(tmp_path):
    path = tmp_path / "leaderboard.json"
    record("Ana", 40, path)
    board = record("Luis", 90, path)
    assert board == [("Luis", 90), ("Ana", 40)]
    assert load_board(path) == board


def test_UX_14_un_nombre_vacio_no_se_guarda(tmp_path):
    path = tmp_path / "leaderboard.json"
    record("Ana", 40, path)
    assert record("   ", 100, path) == [("Ana", 40)]
    assert load_board(path) == [("Ana", 40)]
