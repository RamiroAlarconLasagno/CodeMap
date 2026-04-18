# core/analyzer/js_parser.py
"""Parser regex para archivos JS / JSX / TS / TSX.

TypeScript agrega tipos opcionales que el regex captura si estan presentes,
ignora si no. Un solo archivo para los cuatro lenguajes.

Estrategia de multiples pasadas:
    1. _pasada_imports   -> sobre lineas originales (strings = modulos)
    2. _pasada_clases    -> detecta class, extrae metodos y atributos TS
    3. _pasada_funciones -> function declarations y arrow functions const
    4. _pasada_variables -> const/let/var de modulo (excluye funciones/clases)
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
    limpiar_js_ts,
    mapa_scopes_llaves,
)

# ---------------------------------------------------------------------------
# Patrones compilados de modulo
# ---------------------------------------------------------------------------

def _extraer_cuerpo_metodo(lineas: list, k: int) -> tuple:
    """Extrae el cuerpo de un metodo/funcion cuya firma esta en lineas[k].

    A diferencia de extraer_bloque_llaves, ignora las llaves '{}' que estan
    dentro de parentesis '()' — por ejemplo default params como (x = {}).
    Esto evita que 'async get(endpoint, params = {}) {' cierre en el '}' del
    default param en lugar del '}' real de cierre del metodo.
    """
    prof_llaves = 0
    prof_parens = 0
    inicio = False
    resultado = []

    for i in range(k, len(lineas)):
        linea = lineas[i]
        resultado.append(linea)
        for ch in linea:
            if ch == "(":
                prof_parens += 1
            elif ch == ")":
                prof_parens = max(0, prof_parens - 1)
            elif ch == "{" and prof_parens == 0:
                prof_llaves += 1
                inicio = True
            elif ch == "}" and prof_parens == 0 and inicio:
                prof_llaves -= 1
                if prof_llaves == 0:
                    return i, "\n".join(resultado)

    return len(lineas) - 1, "\n".join(resultado)


RE_JS: dict = {
    # import { X, Y } from 'mod'  /  import X from 'mod'  /  import * as X from 'mod'
    # import X, { Y } from 'mod'  (mixed default + named)
    "import_from": re.compile(
        r"import\s+(?:type\s+)?"
        r"(?:\*\s+as\s+\w+|[\w$]+\s*,\s*\{[^}]*\}|\{[^}]*\}|[\w$]+)\s+from\s+['\"]([^'\"]+)['\"]"
    ),
    # import 'mod'  (side-effect)
    "import_bare": re.compile(r"""^import\s+['"]([^'"]+)['"]\s*;?\s*$"""),

    # [export] [default] [abstract] class X [extends Y] [implements Z] {
    "clase": re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?"
        r"class\s+([\w$]+)"
        r"(?:\s+extends\s+([\w$.]+))?"
        r"(?:\s+implements\s+[\w$,\s<>]+)?\s*\{"
    ),

    # [export] [async] function* nombre(params)
    "funcion": re.compile(
        r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?"
        r"function\*?\s+([\w$]+)\s*(\([^)]*\))"
    ),

    # const/let nombre = [async] ([params]) =>   (arrow function de modulo)
    "arrow_const": re.compile(
        r"^(?:export\s+)?(?:const|let)\s+([\w$]+)\s*="
        r"\s*(?:async\s+)?(?:\([^)]*\)|[\w$]+)\s*=>"
    ),

    # metodo dentro de clase: [modificadores] nombre(params) [: tipo] {
    "metodo": re.compile(
        r"^(?:(?:public|private|protected|static|async|override|abstract|"
        r"readonly|declare)\s+)*"
        r"(?:get\s+|set\s+)?"
        r"((?!if|for|while|switch|return|new|typeof|delete|void|throw)\b[\w$]+)\s*"
        r"(\([^)]*\))\s*(?::\s*[\w<>\[\]|&,\s?]+)?\s*\{"
    ),

    # atributo TS con al menos un modificador explicito:
    #   [readonly|static|public|private|protected|override|declare|abstract] nombre[?!]: tipo [= val];
    "atributo_ts": re.compile(
        r"^(?:(?:readonly|static|public|private|protected|override|declare|abstract)\s+)+"
        r"([\w$]+)\s*[?!]?\s*:\s*([\w<>\[\]|&,\s?]+?)"
        r"(?:\s*=\s*([^;]+))?\s*;"
    ),

    # [export] const|let|var nombre [: tipo] = val
    "variable": re.compile(
        r"^(?:export\s+)?(?:const|let|var)\s+([\w$]+)"
        r"(?:\s*:\s*([\w<>\[\]|&,\s?]+?))?\s*=\s*(.+)"
    ),

    # llamada: nombre(  o  obj.metodo(
    "llamada": re.compile(r"([\w$][\w$.]*)\s*\("),
}

# Keywords que no son nombres de metodos validos
_KW_JS = frozenset({
    "if", "for", "while", "switch", "catch", "function", "return",
    "new", "typeof", "instanceof", "delete", "void", "throw", "await",
    "import", "export", "class", "extends", "super", "this", "async",
    "yield", "debugger", "case", "default", "constructor",
})


# ---------------------------------------------------------------------------
# Pasadas internas
# ---------------------------------------------------------------------------

def _pasada_imports(lineas: list, info: ArchivoInfo) -> None:
    """Trabaja sobre lineas ORIGINALES: los strings son los modulos a importar."""
    for linea in lineas:
        texto = linea.strip()
        m = RE_JS["import_from"].search(texto)
        if m:
            modulo = m.group(1)
            nombres: list = []
            bloque = re.search(r"\{([^}]+)\}", texto)
            if bloque:
                nombres = [
                    n.strip().split(" as ")[0].strip()
                    for n in bloque.group(1).split(",")
                    if n.strip()
                ]
            info.imports.append(ImportInfo(modulo, nombres, True))
            continue
        m = RE_JS["import_bare"].match(texto)
        if m:
            info.imports.append(ImportInfo(m.group(1), [], False))


def _pasada_clases(
    lineas: list,
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue
        m = RE_JS["clase"].match(linea.strip())
        if not m:
            continue

        nombre_clase = m.group(1)
        bases = [m.group(2)] if m.group(2) else []

        # Localizar '{' de apertura (puede estar en las proximas lineas)
        inicio_bloque = i
        for j in range(i, min(i + 5, len(lineas_limpias))):
            if "{" in lineas_limpias[j]:
                inicio_bloque = j
                break

        fin_bloque, bloque_texto = extraer_bloque_llaves(lineas_limpias, inicio_bloque)
        bloque_limpias = limpiar_js_ts(bloque_texto).splitlines()

        metodos: list = []
        atributos: list = []

        # Profundidad inicial = 1: la apertura ya esta en bloque_limpias[0].
        # Saltamos k=0 (declaracion de clase) para no procesarla como contenido.
        profundidad = 1

        for k, bl in enumerate(bloque_limpias):
            if k == 0:
                continue
            bl_strip = bl.strip()
            if not bl_strip:
                continue

            # Actualizar profundidad ANTES del check para lineas que solo cierran
            aperturas = bl.count("{")
            cierres = bl.count("}")

            if profundidad != 1:
                profundidad += aperturas - cierres
                continue

            # Ahora estamos en nivel 1 (directo dentro de la clase)

            # --- Constructor ---
            if re.match(r"^constructor\s*\(", bl_strip):
                pm = re.search(r"\([^)]*\)", bl_strip)
                firma = f"constructor{pm.group() if pm else '()'}"
                metodos.insert(0, MetodoInfo(
                    nombre="constructor",
                    firma=firma,
                    docstring="",
                    es_async=False,
                    llamadas=[],
                    linea=i + k,
                ))
                # Extraer this.x = val del cuerpo del constructor
                if aperturas > 0:
                    _, cuerpo_ctor = _extraer_cuerpo_metodo(bloque_limpias, k)
                    for al in cuerpo_ctor.splitlines():
                        ma = re.match(r"^\s*this\.([\w$]+)\s*=\s*(.+?)\s*;?\s*$", al)
                        if ma:
                            atributos.append(VariableInfo(
                                ma.group(1), None, ma.group(2).strip()[:80],
                                "clase", i + k,
                            ))
                profundidad += aperturas - cierres
                continue

            # --- Atributos TS con modificador explicito ---
            ma = RE_JS["atributo_ts"].match(bl_strip)
            if ma:
                atributos.append(VariableInfo(
                    ma.group(1),
                    ma.group(2).strip() if ma.group(2) else None,
                    ma.group(3).strip() if ma.group(3) else None,
                    "clase",
                    i + k,
                ))
                profundidad += aperturas - cierres
                continue

            # --- Atributos JS planos: nombre; o nombre = val; (nivel 1, sin llaves) ---
            if aperturas == 0 and cierres == 0 and bl_strip.endswith(";"):
                ma2 = re.match(r"^(?:static\s+)?([\w$]+)(?:\s*=\s*([^;]+))?\s*;$", bl_strip)
                if ma2 and ma2.group(1) not in _KW_JS:
                    atributos.append(VariableInfo(
                        ma2.group(1), None,
                        ma2.group(2).strip() if ma2.group(2) else None,
                        "clase", i + k,
                    ))
                    continue

            # --- Metodos ---
            mm = RE_JS["metodo"].match(bl_strip)
            if mm:
                nombre_met = mm.group(1)
                if nombre_met in _KW_JS:
                    profundidad += aperturas - cierres
                    continue
                es_async = bool(re.match(
                    r"(?:(?:public|private|protected|static|override|abstract|declare)\s+)*async\s+",
                    bl_strip,
                ))
                firma = f"{nombre_met}{mm.group(2)}"
                llamadas: list = []
                if aperturas > 0:
                    _, cuerpo = _extraer_cuerpo_metodo(bloque_limpias, k)
                    llamadas = extraer_llamadas_texto(cuerpo, RE_JS["llamada"])
                metodos.append(MetodoInfo(
                    nombre=nombre_met,
                    firma=firma,
                    docstring="",
                    es_async=es_async,
                    llamadas=llamadas,
                    linea=i + k,
                ))

            profundidad += aperturas - cierres

        # Deduplicar atributos por nombre (el constructor puede repetir los de clase)
        vistos: set = set()
        atributos_unicos: list = []
        for a in atributos:
            if a.nombre not in vistos:
                vistos.add(a.nombre)
                atributos_unicos.append(a)

        info.clases.append(ClaseInfo(
            nombre=nombre_clase,
            firma=f"class {nombre_clase}" + (f" extends {bases[0]}" if bases else ""),
            docstring="",
            clases_base=bases,
            metodos=metodos,
            atributos=atributos_unicos,
            linea=i,
        ))


def _pasada_funciones(
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue
        texto = linea.strip()

        # function declaration
        m = RE_JS["funcion"].match(texto)
        if m:
            nombre = m.group(1)
            es_async = "async" in texto[: texto.index(nombre)]
            firma = f"{'async ' if es_async else ''}function {nombre}{m.group(2)}"
            llamadas: list = []
            if "{" in linea:
                _, cuerpo = _extraer_cuerpo_metodo(lineas_limpias, i)
                llamadas = extraer_llamadas_texto(cuerpo, RE_JS["llamada"])
            info.funciones.append(FuncionInfo(
                nombre=nombre, firma=firma, docstring="",
                es_async=es_async, llamadas=llamadas, linea=i,
            ))
            continue

        # arrow function  const f = () =>
        m = RE_JS["arrow_const"].match(texto)
        if m:
            nombre = m.group(1)
            es_async = "async" in texto[: max(0, texto.index("=>") - 1)]
            firma = texto.split("=>")[0].strip() + " =>"
            llamadas = []
            if "{" in linea:
                _, cuerpo = _extraer_cuerpo_metodo(lineas_limpias, i)
                llamadas = extraer_llamadas_texto(cuerpo, RE_JS["llamada"])
            info.funciones.append(FuncionInfo(
                nombre=nombre, firma=firma, docstring="",
                es_async=es_async, llamadas=llamadas, linea=i,
            ))


def _pasada_variables(
    lineas_limpias: list,
    scopes: list,
    info: ArchivoInfo,
) -> None:
    nombres_funciones = {f.nombre for f in info.funciones}
    nombres_clases = {c.nombre for c in info.clases}

    for i, linea in enumerate(lineas_limpias):
        if scopes[i] != "modulo":
            continue
        m = RE_JS["variable"].match(linea.strip())
        if not m:
            continue
        nombre = m.group(1)
        if nombre in nombres_funciones or nombre in nombres_clases:
            continue
        resto = m.group(3) or ""
        # Excluir arrow functions y clases inline
        if "=>" in resto or resto.strip().startswith(("function", "class")):
            continue
        info.variables.append(VariableInfo(
            nombre=nombre,
            tipo=m.group(2).strip() if m.group(2) else None,
            valor_inicial=resto.strip().rstrip(";")[:80],
            scope="modulo",
            linea=i,
        ))


# ---------------------------------------------------------------------------
# Punto de entrada publico
# ---------------------------------------------------------------------------

def parsear_archivo(ruta: Path, raiz: Path, lenguaje: str) -> ArchivoInfo:
    """Lee un archivo JS/JSX/TS/TSX y devuelve su ArchivoInfo completo."""
    info = ArchivoInfo(
        ruta_relativa=str(ruta.relative_to(raiz)),
        carpeta=str(ruta.parent.relative_to(raiz)),
        nombre=ruta.name,
        lenguaje=lenguaje,
    )
    try:
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        lineas = texto.splitlines()
        lineas_limpias = limpiar_js_ts(texto).splitlines()
        scopes = mapa_scopes_llaves(lineas_limpias)

        _pasada_imports(lineas, info)
        _pasada_clases(lineas, lineas_limpias, scopes, info)
        _pasada_funciones(lineas_limpias, scopes, info)
        _pasada_variables(lineas_limpias, scopes, info)
    except Exception as exc:
        info.error = str(exc)
    return info