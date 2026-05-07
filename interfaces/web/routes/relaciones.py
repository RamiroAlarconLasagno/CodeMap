# interfaces/web/routes/relaciones.py
from fastapi import APIRouter, HTTPException

from core.filters import f_buscar, f_idioma, f_libreria
from core.queries import q_llamadas, q_usos
from core.state import get_indice

router = APIRouter()


@router.get("/llamadas/{simbolo:path}")
def llamadas(simbolo: str):
    resultado = q_llamadas(get_indice(), simbolo)
    if resultado is None:
        raise HTTPException(status_code=404, detail=f"Simbolo '{simbolo}' no encontrado")
    return resultado


@router.get("/usos/{nombre}")
def usos(nombre: str):
    return q_usos(get_indice(), nombre)


@router.get("/libreria/{nombre}")
def libreria(nombre: str):
    return f_libreria(get_indice(), nombre)


@router.get("/buscar")
def buscar(patron: str):
    return f_buscar(get_indice(), patron)


@router.get("/idioma")
def idioma():
    return f_idioma(get_indice())