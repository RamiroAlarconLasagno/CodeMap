# core/state.py

from __future__ import annotations

from typing import Optional

from core.index import ProjectIndex

_indice: Optional[ProjectIndex] = None


def get_indice() -> ProjectIndex:
    """Devuelve el indice activo. Lanza RuntimeError si no fue inicializado."""
    if _indice is None:
        raise RuntimeError(
            "El indice no fue inicializado. "
            "Llama a set_indice() antes de usar get_indice()."
        )
    return _indice


def set_indice(indice: ProjectIndex) -> None:
    """Reemplaza el indice activo."""
    global _indice
    _indice = indice


def esta_inicializado() -> bool:
    """Verifica si el indice fue inicializado, sin lanzar excepcion."""
    return _indice is not None


def _reset() -> None:
    """Solo para tests — resetea el estado global."""
    global _indice
    _indice = None