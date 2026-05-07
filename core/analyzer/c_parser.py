# core/analyzer/c_parser.py
"""Parser regex para archivos C / C++ (.c .h .cpp .cc .cxx .hpp).

Un solo archivo para C y C++ porque comparten la misma base sintactica.
C++ agrega clases, templates y namespaces que el regex captura si estan presentes.

Estrategia de multiples pasadas:
    1. _pasada_defines_includes -> sobre lineas ORIGINALES (#include/#define)
    2. _pasada_clases           -> class / struct / enum con llaves
    3. _pasada_funciones        -> funciones sueltas de modulo
    4. _pasada_variables        -> variables globales (static/extern/const/tipo)
"""

import re
from pathlib import Path

from core.index import (
    ArchivoInfo,
    ClaseInfo,
    FuncionInfo,
    ImportInfo,
    LlamadaInfo,
    MetodoInfo,
    VariableInfo,
)
from core.analyzer.regex_base import (
    extraer_bloque_llaves,
    extraer_llamadas_texto,
    limpiar_c_cpp,
    mapa_scopes_llaves,
)

# ---------------------------------------------------------------------------
# Patrones compilados de modulo
# ---------------------------------------------------------------------------

RE_C: dict = {
    # #include <lib.h>  o  #include "lib.h"
    "include": re.compile(r'^#include\s+[<"]([^>"]+)[>"]'),

    # #define NOMBRE [valor]
    "define": re.compile(r'^#define\s+(\w+)(?:\s+(.+))?$'),

    # [template<...>] [class|struct] Nombre [: [public] Base] {
    "clase_cpp": re.compile(
        r"^(?:template\s*<[^>]*>\s*)?"
        r"(?:class|struct)\s+(\w+)"
        r"(?:\s*:\s*(?:public|protected|private)?\s*([\w:]+))?"
        r"\s*\{"
    ),

    # enum [class] Nombre [: tipo] {
    "enum": re.compile(
        r"^enum(?:\s+class)?\s+(\w+)"
        r"(?:\s*:\s*[\w:]+)?"
        r"\s*\{"
    ),

    # tipo [*&] nombre(params) [const] [override] [noexcept] {
    # Captura: (1)tipo  (2)nombre  (3)params
    "funcion": re.compile(
        r"^(?:(?:static|inline|virtual|explicit|constexpr|extern)\s+)*"
        r"((?:const\s+)?[\w:*&<>]+(?:\s*[*&]+)?)\s+"
        r"(\w+)\s*\(([^)]*)\)"
        r"(?:\s*const)?(?:\s*override)?(?:\s*noexcept)?"
        r"\s*\{"
    ),

    # [static|extern|const|constexpr] tipo nombre [= val];
    "variable": re.compile(
        r"^(?:(?:static|extern|const|constexpr|volatile)\s+)+"
        r"([\w:*&<>]+(?:\s*[*&]+)?)\s+"
        r"(\w+)\s*(?:=\s*([^;]+))?\s*;"
    ),

    # llamada: nombre(
    "llamada": re.compile(r"\b(\w[\w:]*)\s*\("),
}

# Palabras clave que no son tipos ni nombres validos
_KW_C = frozenset({
    "if", "else", "for", "while", "do", "switch", "case", "default",
    "return", "break", "continue", "goto", "sizeof", "alignof",
    "typedef", "struct", "class", "enum", "union", "template",
    "namespace", "using", "public", "private", "protected", "virtual",
    "static", "extern", "inline", "const", "constexpr", "volatile",
    "override", "final", "new", "delete", "throw", "try", "catch",
    "nullptr", "true", "false", "this",
})

# Tipos basicos que no son nombres de funcion validos
_TIPOS_BASE = frozenset({
    "void", "int", "float", "double", "char", "bool", "long", "short",
    "unsigned", "signed", "auto", "size_t", "uint8_t", "uint16_t",
    "uint32_t", "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t",
    "String", "byte",
})


# ---------------------------------------------------------------------------
# Pasadas internas
# ---------------------------------------------------------------------------

def _pasada_defines_includes(lineas: list, info: ArchivoInfo) -> None:
    """Trabaja sobre lineas ORIGINALES: los strings son los modulos a incluir."""
    for linea in lineas:
        texto = linea.strip()
        # #include
        m = RE_C["include"].match(texto)
        if m:
            modulo = m.group(1)
            info.imports.append(ImportInfo(modulo, [], False))
            continue
        # #define
        m = RE_C["define"].match(texto)
        if m:
            nombre = m.group(1)
            valor = (m.group(2) or "").strip()
            info.variables.append(VariableInfo(
                nombre=nombre,
                tipo="#define",
                valor_inicial=valor[:80] if valor else None,
                scope="modulo",
                linea=0,
            ))


def _pasada_clases(
    lineas: list,
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue

        # Detectar class / struct
        m = RE_C["clase_cpp"].match(linea.strip())
        es_enum = False
        if not m:
            m = RE_C["enum"].match(linea.strip())
            es_enum = bool(m)
        if not m:
            continue

        nombre_clase = m.group(1)
        bases = []
        if not es_enum and m.lastindex and m.lastindex >= 2 and m.group(2):
            bases = [m.group(2).strip()]

        inicio_bloque = i
        for j in range(i, min(i + 5, len(lineas_limpias))):
            if "{" in lineas_limpias[j]:
                inicio_bloque = j
                break

        fin_bloque, bloque_texto = extraer_bloque_llaves(lineas_limpias, inicio_bloque)
        bloque_limpias = limpiar_c_cpp(bloque_texto).splitlines()

        metodos: list = []
        atributos: list = []

        # Constructor dinamico: evita confundir SensorADE9000 con metodo E9000
        RE_CTOR = re.compile(
            rf"^(?:(?:explicit|inline)\s+)?{re.escape(nombre_clase)}\s*\(([^)]*)\)"
            rf"(?:\s*:[^{{]+)?\s*\{{"
        )

        profundidad = 1

        for k, bl in enumerate(bloque_limpias):
            if k == 0:
                continue
            bl_strip = bl.strip()
            if not bl_strip:
                continue

            aperturas = bl.count("{")
            cierres = bl.count("}")

            if profundidad != 1:
                profundidad += aperturas - cierres
                continue

            # --- Constructor ---
            mc = RE_CTOR.match(bl_strip)
            if mc:
                firma = f"{nombre_clase}({mc.group(1)})"
                llamadas: list = []
                if aperturas > 0:
                    _, cuerpo = extraer_bloque_llaves(bloque_limpias, k)
                    llamadas = extraer_llamadas_texto(cuerpo, RE_C["llamada"])
                metodos.insert(0, MetodoInfo(
                    nombre=nombre_clase,
                    firma=firma,
                    docstring="",
                    llamadas=llamadas,
                    linea=i + k,
                ))
                profundidad += aperturas - cierres
                continue

            # --- Atributo: tipo nombre; (sin llaves en la linea) ---
            if aperturas == 0 and cierres == 0 and bl_strip.endswith(";"):
                ma = re.match(
                    r"^(?:(?:static|const|mutable|volatile)\s+)*"
                    r"([\w:*&<>]+(?:\s*[*&]+)?)\s+(\w+)\s*(?:=\s*([^;]+))?\s*;$",
                    bl_strip,
                )
                if ma and ma.group(2) not in _KW_C and ma.group(1) not in _KW_C:
                    atributos.append(VariableInfo(
                        nombre=ma.group(2),
                        tipo=ma.group(1),
                        valor_inicial=ma.group(3).strip() if ma.group(3) else None,
                        scope="clase",
                        linea=i + k,
                    ))
                    continue

            # --- Metodo ---
            mm = RE_C["funcion"].match(bl_strip)
            if mm:
                tipo_ret = mm.group(1).strip()
                nombre_met = mm.group(2)
                params = mm.group(3)
                if nombre_met in _KW_C or nombre_met in _TIPOS_BASE:
                    profundidad += aperturas - cierres
                    continue
                es_virtual = "virtual" in bl_strip[: bl_strip.index(nombre_met)]
                firma = f"{tipo_ret} {nombre_met}({params})"
                llamadas = []
                if aperturas > 0:
                    _, cuerpo = extraer_bloque_llaves(bloque_limpias, k)
                    llamadas = extraer_llamadas_texto(cuerpo, RE_C["llamada"])
                metodos.append(MetodoInfo(
                    nombre=nombre_met,
                    firma=firma,
                    docstring="",
                    llamadas=llamadas,
                    linea=i + k,
                ))

            profundidad += aperturas - cierres

        info.clases.append(ClaseInfo(
            nombre=nombre_clase,
            firma=f"{'enum ' if es_enum else ''}"
                  f"{'struct ' if 'struct' in linea else 'class '}"
                  f"{nombre_clase}"
                  + (f" : {bases[0]}" if bases else ""),
            docstring="",
            clases_base=bases,
            metodos=metodos,
            atributos=atributos,
            linea=i,
        ))


def _pasada_funciones(
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    nombres_clases = {c.nombre for c in info.clases}

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue
        texto = linea.strip()
        m = RE_C["funcion"].match(texto)
        if not m:
            continue
        tipo_ret = m.group(1).strip()
        nombre = m.group(2)
        params = m.group(3)
        if nombre in _KW_C or nombre in _TIPOS_BASE or nombre in nombres_clases:
            continue
        firma = f"{tipo_ret} {nombre}({params})"
        llamadas: list = []
        if "{" in linea:
            _, cuerpo = extraer_bloque_llaves(lineas_limpias, i)
            llamadas = extraer_llamadas_texto(cuerpo, RE_C["llamada"])
        info.funciones.append(FuncionInfo(
            nombre=nombre,
            firma=firma,
            docstring="",
            llamadas=llamadas,
            linea=i,
        ))


def _pasada_variables(
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    # Ya tenemos los #define del paso 1; evitar duplicar
    nombres_defines = {v.nombre for v in info.variables if v.tipo == "#define"}
    nombres_clases = {c.nombre for c in info.clases}
    nombres_funciones = {f.nombre for f in info.funciones}

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue
        m = RE_C["variable"].match(linea.strip())
        if not m:
            continue
        tipo = m.group(1).strip()
        nombre = m.group(2)
        if (nombre in nombres_defines or nombre in nombres_clases
                or nombre in nombres_funciones or nombre in _KW_C):
            continue
        info.variables.append(VariableInfo(
            nombre=nombre,
            tipo=tipo,
            valor_inicial=m.group(3).strip().rstrip(";")[:80] if m.group(3) else None,
            scope="modulo",
            linea=i,
        ))


# ---------------------------------------------------------------------------
# Punto de entrada publico
# ---------------------------------------------------------------------------

def parsear_archivo(ruta: Path, raiz: Path, lenguaje: str) -> ArchivoInfo:
    """Lee un archivo C/C++ y devuelve su ArchivoInfo completo."""
    info = ArchivoInfo(
        ruta_relativa=ruta.relative_to(raiz).as_posix(),
        carpeta=ruta.parent.relative_to(raiz).as_posix(),
        nombre=ruta.name,
        lenguaje=lenguaje,
    )
    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        lineas = texto.splitlines()
        lineas_limpias = limpiar_c_cpp(texto).splitlines()
        scopes = mapa_scopes_llaves(lineas_limpias)

        _pasada_defines_includes(lineas, info)
        _pasada_clases(lineas, lineas_limpias, scopes, info)
        _pasada_funciones(lineas_limpias, scopes, info)
        _pasada_variables(lineas_limpias, scopes, info)
    except Exception as exc:
        info.error = str(exc)
    return info