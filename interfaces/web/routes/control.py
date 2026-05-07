# interfaces/web/routes/control.py
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from core.analyzer import construir_indice, reanalizar
from core.queries import q_estado
from core.state import get_indice, set_indice
from shared.formatters import exportar_md

router = APIRouter()

_NIVELES_VALIDOS = {"estructura", "firmas", "completo"}


class CarpetaBody(BaseModel):
    carpeta: str


class ExportarBody(BaseModel):
    archivos: list[str] | None = None
    filtros: dict[str, bool] | None = None


@router.get("/estado")
def estado():
    return q_estado(get_indice())


@router.post("/reanalizar")
def post_reanalizar():
    set_indice(reanalizar(get_indice()))
    return q_estado(get_indice())


@router.get("/exportar/{nivel}", response_class=PlainTextResponse)
def exportar(nivel: str):
    if nivel not in _NIVELES_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"nivel invalido: '{nivel}'. Usar: estructura | firmas | completo",
        )
    return exportar_md(get_indice(), nivel)


@router.post("/exportar/{nivel}", response_class=PlainTextResponse)
def exportar_filtrado(nivel: str, body: ExportarBody):
    if nivel not in _NIVELES_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"nivel invalido: '{nivel}'. Usar: estructura | firmas | completo",
        )
    return exportar_md(
        get_indice(),
        nivel,
        archivos_activos=body.archivos,
        filtros=body.filtros,
    )


@router.post("/carpeta")
def cambiar_carpeta(body: CarpetaBody):
    ruta = Path(body.carpeta)
    if not ruta.exists():
        raise HTTPException(status_code=400, detail=f"Carpeta no existe: {body.carpeta}")
    set_indice(construir_indice(ruta))
    return q_estado(get_indice())