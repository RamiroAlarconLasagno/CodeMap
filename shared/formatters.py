# shared/formatters.py

from __future__ import annotations

from core.index import ArchivoInfo, ProjectIndex

NIVELES = ("estructura", "firmas", "completo")


def exportar_txt(indice: ProjectIndex, nivel: str = "firmas") -> str:
    """Exporta el indice como texto plano. nivel: estructura|firmas|completo."""
    _validar_nivel(nivel)
    lineas = [
        f"# CodeMap — {indice.carpeta_raiz}",
        f"# Nivel: {nivel}",
        f"# Archivos: {indice.total_archivos()} | "
        f"Clases: {indice.total_clases()} | "
        f"Metodos: {indice.total_metodos()} | "
        f"Funciones: {indice.total_funciones()}",
        "",
    ]
    for ruta in sorted(indice.archivos):
        info = indice.archivos[ruta]
        lineas.append(f"[{ruta}]")
        lineas.extend(_bloque_archivo(info, nivel, prefijo="  "))
        lineas.append("")
    return "\n".join(lineas)


def exportar_md(
    indice: ProjectIndex,
    nivel: str = "firmas",
    archivos_activos: list[str] | None = None,
    filtros: dict[str, bool] | None = None,
) -> str:
    """Exporta el indice como Markdown.

    archivos_activos: lista de rutas a incluir (None = todos).
    filtros: dict con claves firmas/docstrings/llamadas/imports/clases_base/variables.
    """
    _validar_nivel(nivel)
    filtros = filtros or {}

    rutas = sorted(indice.archivos)
    if archivos_activos is not None:
        activos_set = set(archivos_activos)
        rutas = [r for r in rutas if r in activos_set]

    n_archivos = len(rutas)
    n_clases   = sum(len(indice.archivos[r].clases)    for r in rutas)
    n_metodos  = sum(
        sum(len(c.metodos) for c in indice.archivos[r].clases) for r in rutas
    )
    n_funciones = sum(len(indice.archivos[r].funciones) for r in rutas)

    lineas = [
        f"# CodeMap — `{indice.carpeta_raiz}`",
        "",
        f"**Nivel:** {nivel} | "
        f"**Archivos:** {n_archivos} | "
        f"**Clases:** {n_clases} | "
        f"**Metodos:** {n_metodos} | "
        f"**Funciones:** {n_funciones}",
        "",
    ]
    for ruta in rutas:
        info = indice.archivos[ruta]
        lineas.append(f"## `{ruta}`")
        if info.error:
            lineas.append(f"> ⚠ Error: {info.error}")
        lineas.extend(_bloque_archivo(info, nivel, prefijo="", filtros=filtros))
        lineas.append("")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Funcion interna compartida
# ---------------------------------------------------------------------------

def _bloque_archivo(
    info: ArchivoInfo,
    nivel: str,
    prefijo: str = "",
    filtros: dict[str, bool] | None = None,
) -> list[str]:
    filtros = filtros or {}
    con_detalle = nivel != "estructura"

    show_firmas      = con_detalle and filtros.get("firmas",      True)
    show_docstrings  = con_detalle and filtros.get("docstrings",  True)
    show_llamadas    = nivel == "completo" and filtros.get("llamadas",    True)
    show_imports     = con_detalle and filtros.get("imports",     True)
    show_variables   = filtros.get("variables",   True)
    show_clases_base = con_detalle and filtros.get("clases_base", True)

    lineas: list[str] = []

    # Imports
    if info.imports and show_imports:
        lineas.append(f"{prefijo}imports: {len(info.imports)}")

    # Variables de modulo
    if show_variables:
        for v in info.variables:
            if not show_firmas:
                lineas.append(f"{prefijo}var {v.nombre}")
            else:
                tipo  = f": {v.tipo}"          if v.tipo          else ""
                valor = f" = {v.valor_inicial}" if v.valor_inicial else ""
                lineas.append(f"{prefijo}var {v.nombre}{tipo}{valor}")

    # Clases
    for c in info.clases:
        if not show_firmas:
            lineas.append(f"{prefijo}class {c.nombre}")
        else:
            bases = (
                f"({', '.join(c.clases_base)})"
                if c.clases_base and show_clases_base
                else ""
            )
            lineas.append(f"{prefijo}class {c.nombre}{bases}")
            if c.docstring and show_docstrings:
                lineas.append(f'{prefijo}  "{c.docstring}"')

        # Atributos de clase
        for a in c.atributos:
            if not show_firmas:
                lineas.append(f"{prefijo}  .{a.nombre}")
            else:
                tipo  = f": {a.tipo}"          if a.tipo          else ""
                valor = f" = {a.valor_inicial}" if a.valor_inicial else ""
                lineas.append(f"{prefijo}  .{a.nombre}{tipo}{valor}")

        # Metodos
        for m in c.metodos:
            if not show_firmas:
                pfx = "async " if m.es_async else ""
                lineas.append(f"{prefijo}  {pfx}{m.nombre}()")
            else:
                lineas.append(f"{prefijo}  {m.firma}")
                if m.docstring and show_docstrings:
                    lineas.append(f'{prefijo}    "{m.docstring}"')
                if show_llamadas and m.llamadas:
                    nombres = ", ".join(l.nombre for l in m.llamadas)
                    lineas.append(f"{prefijo}    -> llama: {nombres}")

    # Funciones sueltas
    for f in info.funciones:
        if not show_firmas:
            pfx = "async " if f.es_async else ""
            lineas.append(f"{prefijo}fn {pfx}{f.nombre}()")
        else:
            lineas.append(f"{prefijo}fn {f.firma}")
            if f.docstring and show_docstrings:
                lineas.append(f'{prefijo}   "{f.docstring}"')
            if show_llamadas and f.llamadas:
                nombres = ", ".join(l.nombre for l in f.llamadas)
                lineas.append(f"{prefijo}   -> llama: {nombres}")

    return lineas


def _validar_nivel(nivel: str) -> None:
    if nivel not in NIVELES:
        raise ValueError(f"nivel debe ser uno de {NIVELES}, recibido: '{nivel}'")
