# core/analyzer/dart_parser.py
"""Parser regex para archivos Dart (.dart).

Extrae imports, clases (con mixins y enums), metodos, atributos,
funciones sueltas y variables de modulo mediante multiples pasadas
sobre el texto. Usa regex_base para limpiar el codigo antes de aplicar
los patrones y para extraer bloques por llaves balanceadas.
"""

import re
from pathlib import Path
from typing import Optional

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
    limpiar_dart,
    mapa_scopes_llaves,
)

# ---------------------------------------------------------------------------
# Patrones compilados
# ---------------------------------------------------------------------------
_RE = {
    # import 'pkg' as alias show X, Y hide Z;
    "import": re.compile(
        r"^import\s+['\"]([^'\"]+)['\"]\s*(?:as\s+(\w+)\s*)?(?:show\s+([\w\s,]+?))?(?:hide\s+([\w\s,]+?))?\s*;",
        re.MULTILINE,
    ),
    # export 'pkg';
    "export_dir": re.compile(
        r"^export\s+['\"]([^'\"]+)['\"]\s*;",
        re.MULTILINE,
    ),
    # abstract/base/final/sealed/mixin class Nombre extends Base with Mixin
    "clase": re.compile(
        r"""^[ \t]*(?:abstract\s+|base\s+|final\s+|sealed\s+|interface\s+)?
            (?:mixin\s+)?class\s+(\w+)
            (?:\s+extends\s+([\w<>, ]+?))?
            (?:\s+with\s+([\w<>, ]+?))?
            (?:\s+implements\s+([\w<>, ]+?))?
            \s*\{""",
        re.VERBOSE | re.MULTILINE,
    ),
    # mixin LoggableMixin on Base { ... }
    "mixin": re.compile(
        r"""^[ \t]*mixin\s+(\w+)
            (?:\s+on\s+([\w<>, ]+?))?
            \s*\{""",
        re.VERBOSE | re.MULTILINE,
    ),
    # enum EstadoConexion { a, b, c }
    "enum": re.compile(
        r"""^[ \t]*enum\s+(\w+)\s*\{""",
        re.MULTILINE | re.VERBOSE,
    ),
    # extension NombreExt on Tipo { ... }
    "extension": re.compile(
        r"""^[ \t]*extension\s+(\w+)\s+on\s+([\w<>?]+)\s*\{""",
        re.MULTILINE | re.VERBOSE,
    ),
    # Metodo / funcion: tipo? nombre(params) [async] { o =>
    # Captura: (1)tipo_retorno  (2)nombre  (3)params  (4)async?
    "metodo": re.compile(
        r"^[ \t]*(?:([\w<>\[\]?,\s]+?)\s+)?(\w+)\s*(?:<[^>]*>\s*)?\(([^)]*)\)\s*(async\s*)?(?:\{|=>)",
        re.MULTILINE,
    ),
    # Constructor nombrado: Clase.nombre(params)
    "constructor_named": re.compile(
        r"""^[ \t]*(\w+)\.(\w+)\s*\(([^)]*)\)\s*
            (?::\s*[^{]+)?
            (?:\{|;)""",
        re.VERBOSE | re.MULTILINE,
    ),
    # Atributo de clase: [final|late|static|const] [tipo] nombre [= valor];
    "atributo": re.compile(
        r"""^[ \t]*(?:(?:final|late|static|const|override)\s+)*
            ([\w<>\[\]?]+(?:\s*\?)?)\s+
            (\w+)\s*
            (?:=\s*([^;]+?))?\s*;""",
        re.VERBOSE | re.MULTILINE,
    ),
    # Variable de modulo: [final|const|late|var] tipo? nombre = valor;
    "variable": re.compile(
        r"""^(?:final|const|late|var)\s+
            (?:([\w<>\[\]?]+)\s+)?
            (\w+)\s*=\s*([^;]+?)\s*;""",
        re.VERBOSE | re.MULTILINE,
    ),
    # Llamada a funcion: nombre(
    "llamada": re.compile(r"\b(\w+)\s*\("),
}

# Palabras que no son tipos ni nombres validos de metodos/atributos
_PALABRAS_CLAVE = frozenset({
    "if", "else", "for", "while", "do", "switch", "case", "default",
    "return", "break", "continue", "throw", "try", "catch", "finally",
    "new", "await", "yield", "assert", "in", "is", "as", "super",
    "this", "null", "true", "false", "void", "dynamic", "var", "final",
    "const", "late", "static", "abstract", "override", "async", "sync",
    "external", "factory", "get", "set", "import", "export", "library",
    "part", "class", "mixin", "enum", "extension", "typedef", "with",
    "implements", "extends", "on", "required", "covariant", "sealed",
    "base", "interface",
})


# ===========================================================================
# Punto de entrada publico
# ===========================================================================

def parsear_archivo(ruta: Path, raiz: Path) -> ArchivoInfo:
    """Lee un archivo .dart y devuelve su ArchivoInfo completo."""
    info = ArchivoInfo(
        ruta_relativa=str(ruta.relative_to(raiz)),
        carpeta=str(ruta.parent.relative_to(raiz)),
        nombre=ruta.name,
        lenguaje="dart",
    )

    try:
        codigo = ruta.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        info.error = str(exc)
        return info

    lineas = codigo.splitlines()
    codigo_limpio = limpiar_dart(codigo)
    lineas_limpias = codigo_limpio.splitlines()
    scopes = mapa_scopes_llaves(lineas_limpias)

    _pasada_imports(lineas, info)
    _pasada_clases(lineas, lineas_limpias, scopes, info)
    _pasada_funciones(lineas, lineas_limpias, scopes, info)
    _pasada_variables(lineas_limpias, scopes, info)

    return info


# ===========================================================================
# Pasadas internas
# ===========================================================================

def _pasada_imports(lineas: list[str], info: ArchivoInfo) -> None:
    """Extrae imports Dart sobre el codigo original (no limpiado).

    Los strings de los imports se eliminarian con limpiar_dart,
    por eso esta pasada trabaja sobre el texto sin modificar.
    """
    texto = "\n".join(lineas)

    for m in _RE["import"].finditer(texto):
        modulo = m.group(1)
        alias = m.group(2) or ""
        show_raw = m.group(3) or ""
        nombres = [n.strip() for n in show_raw.split(",") if n.strip()]
        es_from = bool(nombres)
        imp = ImportInfo(
            modulo=modulo,
            nombres=nombres,
            es_from=es_from,
        )
        info.imports.append(imp)

    for m in _RE["export_dir"].finditer(texto):
        info.imports.append(ImportInfo(
            modulo=f"export:{m.group(1)}",
            nombres=[],
            es_from=False,
        ))


def _pasada_clases(
    lineas: list[str],
    lineas_limpias: list[str],
    scopes: list[str],
    info: ArchivoInfo,
) -> None:
    """Detecta clases, mixins y enums; extrae sus metodos y atributos."""
    n = len(lineas_limpias)

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue

        # --- Enum ---
        m_enum = _RE["enum"].match(linea)
        if m_enum:
            nombre = m_enum.group(1)
            fin, _ = extraer_bloque_llaves(lineas_limpias, i)
            clase = ClaseInfo(
                nombre=nombre,
                firma=f"enum {nombre}",
                docstring="",
                clases_base=[],
                linea=i + 1,
            )
            info.clases.append(clase)
            continue

        # --- Mixin ---
        m_mixin = _RE["mixin"].match(linea)
        if m_mixin:
            nombre = m_mixin.group(1)
            base_raw = m_mixin.group(2) or ""
            bases = [b.strip() for b in base_raw.split(",") if b.strip()]
            fin, bloque = extraer_bloque_llaves(lineas_limpias, i)
            clase = ClaseInfo(
                nombre=nombre,
                firma=f"mixin {nombre}",
                docstring="",
                clases_base=bases,
                linea=i + 1,
            )
            _extraer_miembros_clase(
                nombre, lineas[i:fin+1], lineas_limpias[i:fin+1], clase
            )
            info.clases.append(clase)
            continue

        # --- Extension ---
        m_ext = _RE["extension"].match(linea)
        if m_ext:
            nombre = m_ext.group(1)
            sobre = m_ext.group(2)
            fin, bloque = extraer_bloque_llaves(lineas_limpias, i)
            clase = ClaseInfo(
                nombre=nombre,
                firma=f"extension {nombre} on {sobre}",
                docstring="",
                clases_base=[sobre],
                linea=i + 1,
            )
            _extraer_miembros_clase(
                nombre, lineas[i:fin+1], lineas_limpias[i:fin+1], clase
            )
            info.clases.append(clase)
            continue

        # --- Clase normal ---
        m_clase = _RE["clase"].match(linea)
        if m_clase:
            nombre = m_clase.group(1)
            extends_raw = m_clase.group(2) or ""
            with_raw = m_clase.group(3) or ""
            impl_raw = m_clase.group(4) or ""

            bases: list[str] = []
            if extends_raw:
                bases += [b.strip() for b in extends_raw.split(",") if b.strip()]
            if with_raw:
                bases += [b.strip() for b in with_raw.split(",") if b.strip()]
            if impl_raw:
                bases += [b.strip() for b in impl_raw.split(",") if b.strip()]

            fin, _ = extraer_bloque_llaves(lineas_limpias, i)
            clase = ClaseInfo(
                nombre=nombre,
                firma=_firma_clase(linea, nombre),
                docstring="",
                clases_base=bases,
                linea=i + 1,
            )
            _extraer_miembros_clase(
                nombre, lineas[i:fin+1], lineas_limpias[i:fin+1], clase
            )
            info.clases.append(clase)


def _extraer_miembros_clase(
    nombre_clase: str,
    lineas: list[str],
    lineas_limpias: list[str],
    clase: ClaseInfo,
) -> None:
    """Extrae metodos y atributos del bloque de una clase."""
    # Regex dinamico para el constructor: NombreClase(params)
    re_ctor = re.compile(
        rf"""^[ \t]*{re.escape(nombre_clase)}\s*
        (?:\.\w+)?\s*\(([^)]*)\)\s*
        (?::\s*[^{{]+)?
        (?:\{{|;)""",
        re.VERBOSE | re.MULTILINE,
    )

    profundidad = 0  # 0 = antes de abrir la clase, 1 = miembro directo
    nombres_metodos: set[str] = set()

    for i, linea in enumerate(lineas_limpias):
        stripped = linea.strip()

        # Actualizar profundidad antes de procesar
        abre = stripped.count("{")
        cierra = stripped.count("}")

        prof_antes = profundidad
        profundidad += abre - cierra

        # Solo procesar miembros directos (profundidad 1 antes de abrir/cerrar)
        # La linea de apertura de la clase esta en profundidad 0→1
        if prof_antes != 1:
            continue
        if not stripped or stripped in ("{", "}"):
            continue

        # Constructor
        m_ctor = re_ctor.match(linea)
        if m_ctor:
            params = m_ctor.group(1).strip()
            # Detectar si es nombrado (NombreClase.nombre)
            es_nombrado = "." in linea.split("(")[0].split(nombre_clase)[-1]
            nombre_ctor = "__init__"
            if es_nombrado:
                parte = linea.strip().split("(")[0]
                nombre_ctor = parte.split(".")[-1].strip()
            firma = f"{nombre_clase}({params})"
            metodo = MetodoInfo(
                nombre=nombre_ctor if es_nombrado else nombre_clase,
                firma=firma,
                docstring="",
                es_async=False,
                linea=i + 1,
            )
            _agregar_llamadas_metodo(i, lineas, lineas_limpias, metodo)
            clase.metodos.append(metodo)
            nombres_metodos.add(nombre_ctor if es_nombrado else nombre_clase)
            continue

        # Atributo: lineas que terminan en ; sin abrir bloque
        if not stripped.endswith("{") and stripped.endswith(";"):
            m_attr = _RE["atributo"].match(linea)
            if m_attr:
                tipo = m_attr.group(1)
                nombre_var = m_attr.group(2)
                valor = (m_attr.group(3) or "").strip()
                if nombre_var not in _PALABRAS_CLAVE and tipo not in _PALABRAS_CLAVE:
                    clase.atributos.append(VariableInfo(
                        nombre_var,
                        tipo,
                        valor or None,
                        "clase",
                        i + 1,
                    ))
                continue

        # Metodo
        m_met = _RE["metodo"].match(linea)
        if m_met:
            tipo_ret = (m_met.group(1) or "").strip()
            nombre_met = m_met.group(2).strip()
            params = (m_met.group(3) or "").strip()
            es_async = bool(m_met.group(4))

            if nombre_met in _PALABRAS_CLAVE or nombre_met == nombre_clase:
                continue
            if nombre_met in nombres_metodos:
                continue

            firma = f"{nombre_met}({params})"
            if tipo_ret and tipo_ret not in _PALABRAS_CLAVE:
                firma = f"{tipo_ret} {firma}"

            metodo = MetodoInfo(
                nombre=nombre_met,
                firma=firma,
                docstring="",
                es_async=es_async,
                linea=i + 1,
            )
            _agregar_llamadas_metodo(i, lineas, lineas_limpias, metodo)
            clase.metodos.append(metodo)
            nombres_metodos.add(nombre_met)


def _agregar_llamadas_metodo(
    linea_inicio: int,
    lineas: list[str],
    lineas_limpias: list[str],
    metodo: MetodoInfo,
) -> None:
    """Extrae las llamadas dentro del cuerpo de un metodo."""
    fin, bloque_limpio = extraer_bloque_llaves(lineas_limpias, linea_inicio)
    metodo.llamadas = extraer_llamadas_texto(bloque_limpio, _RE["llamada"])


def _pasada_funciones(
    lineas: list[str],
    lineas_limpias: list[str],
    scopes: list[str],
    info: ArchivoInfo,
) -> None:
    """Extrae funciones sueltas de nivel modulo."""
    nombres_vistos: set[str] = set()

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue

        m = _RE["metodo"].match(linea)
        if not m:
            continue

        tipo_ret = (m.group(1) or "").strip()
        nombre = m.group(2).strip()
        params = (m.group(3) or "").strip()
        es_async = bool(m.group(4))

        if nombre in _PALABRAS_CLAVE:
            continue
        # Evitar detectar clases como funciones
        if nombre[0].isupper():
            continue
        if nombre in nombres_vistos:
            continue

        firma = f"{nombre}({params})"
        if tipo_ret and tipo_ret not in _PALABRAS_CLAVE:
            firma = f"{tipo_ret} {firma}"

        _, bloque_limpio = extraer_bloque_llaves(lineas_limpias, i)
        llamadas = extraer_llamadas_texto(bloque_limpio, _RE["llamada"])

        info.funciones.append(FuncionInfo(
            nombre=nombre,
            firma=firma,
            docstring="",
            es_async=es_async,
            llamadas=llamadas,
            linea=i + 1,
        ))
        nombres_vistos.add(nombre)


def _pasada_variables(
    lineas_limpias: list[str],
    scopes: list[str],
    info: ArchivoInfo,
) -> None:
    """Extrae variables de nivel modulo (final, const, late, var)."""
    nombres_vistos: set[str] = set()
    texto_modulo_lineas = []

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] == "modulo":
            texto_modulo_lineas.append(linea)
        else:
            texto_modulo_lineas.append("")

    texto = "\n".join(texto_modulo_lineas)

    for m in _RE["variable"].finditer(texto):
        tipo = (m.group(1) or "").strip()
        nombre = m.group(2).strip()
        valor = m.group(3).strip()

        if nombre in _PALABRAS_CLAVE or nombre in nombres_vistos:
            continue

        # Calcular numero de linea aproximado
        linea_num = texto[:m.start()].count("\n") + 1

        info.variables.append(VariableInfo(
            nombre,
            tipo or None,
            valor or None,
            "modulo",
            linea_num,
        ))
        nombres_vistos.add(nombre)


# ===========================================================================
# Helpers
# ===========================================================================

def _firma_clase(linea: str, nombre: str) -> str:
    """Extrae la firma de la clase desde la linea de declaracion."""
    # Eliminar { al final y limpiar espacios extra
    firma = linea.strip().rstrip("{").strip()
    return firma