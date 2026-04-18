# core/queries.py

from __future__ import annotations

from typing import Optional

from core.index import ProjectIndex


def q_carpetas(indice: ProjectIndex) -> dict[str, list[str]]:
    """Arbol carpeta -> lista de archivos."""
    resultado: dict[str, list[str]] = {}
    for ruta, info in indice.archivos.items():
        carpeta = info.carpeta or "."
        resultado.setdefault(carpeta, []).append(info.nombre)
    return resultado


def q_imports(
    indice: ProjectIndex,
    archivo: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Imports por archivo. Sin archivo devuelve todos."""
    archivos = _filtrar_archivo(indice, archivo)
    return {
        ruta: [
            {
                "modulo": imp.modulo,
                "nombres": imp.nombres,
                "es_from": imp.es_from,
            }
            for imp in info.imports
        ]
        for ruta, info in archivos.items()
    }


def q_clases(
    indice: ProjectIndex,
    archivo: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Clases sin metodos. Sin archivo devuelve todas."""
    archivos = _filtrar_archivo(indice, archivo)
    return {
        ruta: [
            {
                "nombre": c.nombre,
                "firma": c.firma,
                "docstring": c.docstring,
                "clases_base": c.clases_base,
                "total_metodos": len(c.metodos),
                "total_atributos": len(c.atributos),
                "linea": c.linea,
            }
            for c in info.clases
        ]
        for ruta, info in archivos.items()
    }


def q_metodos(indice: ProjectIndex, clase: str) -> Optional[dict]:
    """Metodos de una clase especifica por nombre exacto."""
    for ruta, info in indice.archivos.items():
        for c in info.clases:
            if c.nombre == clase:
                return {
                    "clase": clase,
                    "archivo": ruta,
                    "firma_clase": c.firma,
                    "clases_base": c.clases_base,
                    "docstring": c.docstring,
                    "metodos": [
                        {
                            "nombre": m.nombre,
                            "firma": m.firma,
                            "docstring": m.docstring,
                            "decoradores": m.decoradores,
                            "es_async": m.es_async,
                            "llamadas": [l.nombre for l in m.llamadas],
                            "linea": m.linea,
                        }
                        for m in c.metodos
                    ],
                    "atributos": [
                        {
                            "nombre": a.nombre,
                            "tipo": a.tipo,
                            "valor_inicial": a.valor_inicial,
                            "linea": a.linea,
                        }
                        for a in c.atributos
                    ],
                }
    return None


def q_funciones(
    indice: ProjectIndex,
    archivo: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Funciones sueltas. Sin archivo devuelve todas."""
    archivos = _filtrar_archivo(indice, archivo)
    return {
        ruta: [
            {
                "nombre": f.nombre,
                "firma": f.firma,
                "docstring": f.docstring,
                "decoradores": f.decoradores,
                "es_async": f.es_async,
                "llamadas": [l.nombre for l in f.llamadas],
                "linea": f.linea,
            }
            for f in info.funciones
        ]
        for ruta, info in archivos.items()
    }


def q_variables(
    indice: ProjectIndex,
    archivo: Optional[str] = None,
    scope: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Variables de modulo o de clase segun scope. scope: 'modulo'|'clase'|None."""
    archivos = _filtrar_archivo(indice, archivo)
    resultado = {}
    for ruta, info in archivos.items():
        vars_archivo = [
            {
                "nombre": v.nombre,
                "tipo": v.tipo,
                "valor_inicial": v.valor_inicial,
                "scope": v.scope,
                "linea": v.linea,
            }
            for v in info.variables
            if scope is None or v.scope == scope
        ]
        # Agregar atributos de clase si scope es 'clase' o None
        if scope in ("clase", None):
            for c in info.clases:
                for a in c.atributos:
                    if scope is None or a.scope == scope:
                        vars_archivo.append({
                            "nombre": f"{c.nombre}.{a.nombre}",
                            "tipo": a.tipo,
                            "valor_inicial": a.valor_inicial,
                            "scope": a.scope,
                            "linea": a.linea,
                        })
        if vars_archivo:
            resultado[ruta] = vars_archivo
    return resultado


def q_llamadas(indice: ProjectIndex, simbolo: str) -> Optional[dict]:
    """Llamadas de 'Clase.metodo' o 'funcion_suelta'."""
    # Formato: 'Clase.metodo'
    if "." in simbolo:
        nombre_clase, nombre_metodo = simbolo.split(".", 1)
        for ruta, info in indice.archivos.items():
            for c in info.clases:
                if c.nombre == nombre_clase:
                    for m in c.metodos:
                        if m.nombre == nombre_metodo:
                            return {
                                "simbolo": simbolo,
                                "archivo": ruta,
                                "llamadas": [l.nombre for l in m.llamadas],
                            }
    # Formato: funcion suelta
    else:
        for ruta, info in indice.archivos.items():
            for f in info.funciones:
                if f.nombre == simbolo:
                    return {
                        "simbolo": simbolo,
                        "archivo": ruta,
                        "llamadas": [l.nombre for l in f.llamadas],
                    }
    return None


def q_usos(indice: ProjectIndex, nombre: str) -> list[dict]:
    """Donde aparece un simbolo en llamadas (busqueda parcial)."""
    usos = []
    nombre_lower = nombre.lower()
    for ruta, info in indice.archivos.items():
        for c in info.clases:
            for m in c.metodos:
                for llamada in m.llamadas:
                    if nombre_lower in llamada.nombre.lower():
                        usos.append({
                            "archivo": ruta,
                            "contexto": f"{c.nombre}.{m.nombre}",
                            "llamada": llamada.nombre,
                        })
        for f in info.funciones:
            for llamada in f.llamadas:
                if nombre_lower in llamada.nombre.lower():
                    usos.append({
                        "archivo": ruta,
                        "contexto": f.nombre,
                        "llamada": llamada.nombre,
                    })
    return usos


def q_estado(indice: ProjectIndex) -> dict:
    """Totales, carpeta raiz, fecha de analisis, archivos con error."""
    archivos_con_error = [
        {"archivo": ruta, "error": info.error}
        for ruta, info in indice.archivos.items()
        if info.error is not None
    ]
    return {
        "carpeta_raiz": str(indice.carpeta_raiz),
        "ultimo_analisis": (
            indice.ultimo_analisis.isoformat() if indice.ultimo_analisis else None
        ),
        "total_archivos": indice.total_archivos(),
        "total_clases": indice.total_clases(),
        "total_metodos": indice.total_metodos(),
        "total_funciones": indice.total_funciones(),
        "total_variables": indice.total_variables(),
        "archivos_con_error": archivos_con_error,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _filtrar_archivo(
    indice: ProjectIndex,
    archivo: Optional[str],
) -> dict:
    """Devuelve el subconjunto de archivos del indice segun filtro."""
    if archivo is None:
        return indice.archivos
    return {k: v for k, v in indice.archivos.items() if k == archivo}