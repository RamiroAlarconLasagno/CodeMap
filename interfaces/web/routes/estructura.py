# interfaces/web/routes/estructura.py
from typing import Optional

from fastapi import APIRouter, HTTPException

from core.queries import (
    q_carpetas,
    q_clases,
    q_funciones,
    q_imports,
    q_metodos,
    q_variables,
)
from core.state import get_indice

router = APIRouter()


@router.get("/carpetas")
def carpetas():
    return q_carpetas(get_indice())


@router.get("/clases")
def clases(archivo: Optional[str] = None):
    return q_clases(get_indice(), archivo)


@router.get("/metodos/{clase}")
def metodos(clase: str):
    resultado = q_metodos(get_indice(), clase)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Clase '{clase}' no encontrada")
    return resultado


@router.get("/funciones")
def funciones(archivo: Optional[str] = None):
    return q_funciones(get_indice(), archivo)


@router.get("/imports")
def imports(archivo: Optional[str] = None):
    return q_imports(get_indice(), archivo)


@router.get("/variables")
def variables(archivo: Optional[str] = None, scope: Optional[str] = None):
    return q_variables(get_indice(), archivo, scope)