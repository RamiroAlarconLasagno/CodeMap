# core/analyzer/__init__.py

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.index import ArchivoInfo, ProjectIndex
from shared.config import CARPETAS_EXCLUIDAS, EXTENSIONES_SOPORTADAS


def _lenguaje(ruta: Path) -> str | None:
    """Devuelve el lenguaje segun la extension, o None si no esta soportada."""
    return EXTENSIONES_SOPORTADAS.get(ruta.suffix.lower())


def _es_valido(ruta: Path, raiz: Path) -> bool:
    """Verifica que el archivo sea soportado y no este en carpeta excluida."""
    if not ruta.is_file():
        return False
    if _lenguaje(ruta) is None:
        return False
    try:
        partes = ruta.relative_to(raiz).parts
    except ValueError:
        return False
    return not any(parte in CARPETAS_EXCLUIDAS for parte in partes)


def _parsear(ruta: Path, raiz: Path) -> ArchivoInfo:
    """Dispatcher: envia el archivo al parser correcto segun lenguaje."""
    lenguaje = _lenguaje(ruta)

    if lenguaje == "python":
        from core.analyzer.python_parser import parsear_archivo
        return parsear_archivo(ruta, raiz)

    elif lenguaje == "dart":
        from core.analyzer.dart_parser import parsear_archivo
        return parsear_archivo(ruta, raiz)

    elif lenguaje in ("js", "jsx", "ts", "tsx"):
        from core.analyzer.js_parser import parsear_archivo
        return parsear_archivo(ruta, raiz, lenguaje)

    elif lenguaje in ("c", "cpp"):
        from core.analyzer.c_parser import parsear_archivo
        return parsear_archivo(ruta, raiz, lenguaje)

    else:
        raise NotImplementedError(f"Lenguaje no soportado: {lenguaje}")


def construir_indice(carpeta: Path) -> ProjectIndex:
    """Recorre la carpeta recursivamente y construye el indice en memoria."""
    carpeta = carpeta.resolve()
    archivos: dict[str, ArchivoInfo] = {}

    for ruta in carpeta.rglob("*"):
        if not _es_valido(ruta, carpeta):
            continue
        try:
            info = _parsear(ruta, carpeta)
            archivos[info.ruta_relativa] = info
        except Exception as e:
            ruta_rel = ruta.relative_to(carpeta).as_posix()
            archivos[ruta_rel] = ArchivoInfo(
                ruta_relativa=ruta_rel,
                carpeta=ruta.parent.relative_to(carpeta).as_posix(),
                nombre=ruta.name,
                lenguaje=_lenguaje(ruta) or "desconocido",
                error=str(e),
            )

    return ProjectIndex(
        carpeta_raiz=carpeta,
        archivos=archivos,
        ultimo_analisis=datetime.now(),
    )


def reanalizar(indice: ProjectIndex) -> ProjectIndex:
    """Reconstruye el indice completo desde cero. No hace merge."""
    return construir_indice(indice.carpeta_raiz)