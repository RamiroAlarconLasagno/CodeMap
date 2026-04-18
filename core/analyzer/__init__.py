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
    # Verificar que ninguna parte de la ruta relativa este excluida
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
        raise NotImplementedError("dart_parser no implementado aun (Fase 4)")

    elif lenguaje in ("js", "jsx", "ts", "tsx"):
        raise NotImplementedError("js_parser no implementado aun (Fase 4)")

    elif lenguaje in ("c", "cpp"):
        raise NotImplementedError("c_parser no implementado aun (Fase 4)")

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
        except NotImplementedError:
            # Parser no implementado aun — saltar silenciosamente
            pass
        except Exception as e:
            # Error inesperado — registrar en el indice pero continuar
            ruta_rel = str(ruta.relative_to(carpeta))
            archivos[ruta_rel] = ArchivoInfo(
                ruta_relativa=ruta_rel,
                carpeta=str(ruta.parent.relative_to(carpeta)),
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