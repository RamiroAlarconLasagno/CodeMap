# tests/test_state.py

from pathlib import Path

import pytest

import core.state as state
from core.index import ProjectIndex


# ---------------------------------------------------------------------------
# Fixture: resetea el estado global antes de cada test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    state._reset()
    yield
    state._reset()


def _indice_prueba() -> ProjectIndex:
    return ProjectIndex(carpeta_raiz=Path("/tmp/prueba"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_inicializado_por_defecto():
    assert state.esta_inicializado() is False


def test_get_indice_sin_inicializar_lanza_error():
    with pytest.raises(RuntimeError, match="no fue inicializado"):
        state.get_indice()


def test_set_indice_inicializa():
    idx = _indice_prueba()
    state.set_indice(idx)
    assert state.esta_inicializado() is True


def test_get_indice_devuelve_el_mismo_objeto():
    idx = _indice_prueba()
    state.set_indice(idx)
    recuperado = state.get_indice()
    assert recuperado is idx


def test_set_indice_reemplaza_el_anterior():
    idx1 = ProjectIndex(carpeta_raiz=Path("/tmp/uno"))
    idx2 = ProjectIndex(carpeta_raiz=Path("/tmp/dos"))

    state.set_indice(idx1)
    state.set_indice(idx2)

    recuperado = state.get_indice()
    assert recuperado is idx2
    assert recuperado.carpeta_raiz == Path("/tmp/dos")


def test_reset_limpia_el_estado():
    state.set_indice(_indice_prueba())
    assert state.esta_inicializado() is True

    state._reset()
    assert state.esta_inicializado() is False


def test_esta_inicializado_false_despues_de_reset():
    state.set_indice(_indice_prueba())
    state._reset()
    assert state.esta_inicializado() is False


def test_get_indice_despues_de_reset_lanza_error():
    state.set_indice(_indice_prueba())
    state._reset()
    with pytest.raises(RuntimeError):
        state.get_indice()