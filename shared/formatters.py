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


def exportar_md(indice: ProjectIndex, nivel: str = "firmas") -> str:
    """Exporta el indice como Markdown. nivel: estructura|firmas|completo."""
    _validar_nivel(nivel)
    lineas = [
        f"# CodeMap — `{indice.carpeta_raiz}`",
        "",
        f"**Nivel:** {nivel} | "
        f"**Archivos:** {indice.total_archivos()} | "
        f"**Clases:** {indice.total_clases()} | "
        f"**Metodos:** {indice.total_metodos()} | "
        f"**Funciones:** {indice.total_funciones()}",
        "",
    ]
    for ruta in sorted(indice.archivos):
        info = indice.archivos[ruta]
        lineas.append(f"## `{ruta}`")
        if info.error:
            lineas.append(f"> ⚠ Error: {info.error}")
        lineas.extend(_bloque_archivo(info, nivel, prefijo=""))
        lineas.append("")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Funcion interna compartida
# ---------------------------------------------------------------------------

def _bloque_archivo(
    info: ArchivoInfo,
    nivel: str,
    prefijo: str = "",
) -> list[str]:
    """Genera las lineas de un archivo dado el nivel de detalle."""
    lineas: list[str] = []

    # Imports
    if info.imports and nivel in ("firmas", "completo"):
        lineas.append(f"{prefijo}imports: {len(info.imports)}")

    # Variables de modulo
    for v in info.variables:
        if nivel == "estructura":
            lineas.append(f"{prefijo}var {v.nombre}")
        else:
            tipo = f": {v.tipo}" if v.tipo else ""
            valor = f" = {v.valor_inicial}" if v.valor_inicial else ""
            lineas.append(f"{prefijo}var {v.nombre}{tipo}{valor}")

    # Clases
    for c in info.clases:
        if nivel == "estructura":
            lineas.append(f"{prefijo}class {c.nombre}")
        else:
            bases = f"({', '.join(c.clases_base)})" if c.clases_base else ""
            lineas.append(f"{prefijo}class {c.nombre}{bases}")
            if c.docstring and nivel in ("firmas", "completo"):
                lineas.append(f"{prefijo}  \"{c.docstring}\"")

        # Atributos de clase
        for a in c.atributos:
            if nivel == "estructura":
                lineas.append(f"{prefijo}  .{a.nombre}")
            else:
                tipo = f": {a.tipo}" if a.tipo else ""
                valor = f" = {a.valor_inicial}" if a.valor_inicial else ""
                lineas.append(f"{prefijo}  .{a.nombre}{tipo}{valor}")

        # Metodos
        for m in c.metodos:
            if nivel == "estructura":
                prefijo_async = "async " if m.es_async else ""
                lineas.append(f"{prefijo}  {prefijo_async}{m.nombre}()")
            else:
                lineas.append(f"{prefijo}  {m.firma}")
                if m.docstring and nivel in ("firmas", "completo"):
                    lineas.append(f"{prefijo}    \"{m.docstring}\"")
                if nivel == "completo" and m.llamadas:
                    nombres = ", ".join(l.nombre for l in m.llamadas)
                    lineas.append(f"{prefijo}    -> llama: {nombres}")

    # Funciones sueltas
    for f in info.funciones:
        if nivel == "estructura":
            prefijo_async = "async " if f.es_async else ""
            lineas.append(f"{prefijo}fn {prefijo_async}{f.nombre}()")
        else:
            lineas.append(f"{prefijo}fn {f.firma}")
            if f.docstring and nivel in ("firmas", "completo"):
                lineas.append(f"{prefijo}   \"{f.docstring}\"")
            if nivel == "completo" and f.llamadas:
                nombres = ", ".join(l.nombre for l in f.llamadas)
                lineas.append(f"{prefijo}   -> llama: {nombres}")

    return lineas


def _validar_nivel(nivel: str) -> None:
    if nivel not in NIVELES:
        raise ValueError(f"nivel debe ser uno de {NIVELES}, recibido: '{nivel}'")