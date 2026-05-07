# core/analyzer/regex_base.py
"""Utilidades compartidas para los parsers regex (Dart, JS/TS, C/C++)."""

import re
from typing import Optional
from core.index import LlamadaInfo
from shared.config import LLAMADAS_EXCLUIDAS

# ---------------------------------------------------------------------------
# Palabras clave de control de flujo que no son llamadas a funciones
# ---------------------------------------------------------------------------
_CONTROL_FLOW = frozenset({
    "if", "for", "while", "switch", "catch", "return", "throw",
    "new", "delete", "typeof", "instanceof", "in", "of", "await",
    "yield", "import", "export", "else", "do", "case", "default",
    "break", "continue", "void", "sizeof", "alignof", "static_assert",
})


# ===========================================================================
# Limpiadores de codigo
# ===========================================================================

def limpiar_dart(codigo: str) -> str:
    """Elimina strings y comentarios Dart para evitar falsos positivos en regex.

    Maneja: '', "", ''', \"\"\", comentarios // ///, /* */
    Preserva saltos de linea para mantener numeracion de lineas intacta.
    """
    resultado = []
    i = 0
    n = len(codigo)

    while i < n:
        # Comentario de bloque /* */
        if codigo[i:i+2] == "/*":
            fin = codigo.find("*/", i + 2)
            if fin == -1:
                # Consumir hasta el final preservando newlines
                bloque = codigo[i:]
                resultado.append("\n" * bloque.count("\n"))
                break
            bloque = codigo[i:fin + 2]
            resultado.append("\n" * bloque.count("\n"))
            i = fin + 2

        # Comentario de linea // o ///
        elif codigo[i:i+2] in ("//", "//"):
            fin = codigo.find("\n", i)
            if fin == -1:
                break
            resultado.append("\n")
            i = fin + 1

        # Triple comilla """ o '''
        elif codigo[i:i+3] in ('"""', "'''"):
            delim = codigo[i:i+3]
            fin = codigo.find(delim, i + 3)
            if fin == -1:
                bloque = codigo[i:]
                resultado.append("\n" * bloque.count("\n"))
                break
            bloque = codigo[i:fin + 3]
            resultado.append("\n" * bloque.count("\n"))
            i = fin + 3

        # String simple " o '
        elif codigo[i] in ('"', "'"):
            delim = codigo[i]
            i += 1
            while i < n:
                if codigo[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if codigo[i] == delim:
                    i += 1
                    break
                if codigo[i] == "\n":
                    resultado.append("\n")
                i += 1

        else:
            resultado.append(codigo[i])
            i += 1

    return "".join(resultado)


def limpiar_js_ts(codigo: str) -> str:
    """Elimina strings y comentarios JS/TS para evitar falsos positivos en regex.

    Maneja: '', "", `` (template literals), comentarios // y /* */
    Preserva saltos de linea.
    """
    resultado = []
    i = 0
    n = len(codigo)

    while i < n:
        # Comentario de bloque
        if codigo[i:i+2] == "/*":
            fin = codigo.find("*/", i + 2)
            if fin == -1:
                bloque = codigo[i:]
                resultado.append("\n" * bloque.count("\n"))
                break
            bloque = codigo[i:fin + 2]
            resultado.append("\n" * bloque.count("\n"))
            i = fin + 2

        # Comentario de linea
        elif codigo[i:i+2] == "//":
            fin = codigo.find("\n", i)
            if fin == -1:
                break
            resultado.append("\n")
            i = fin + 1

        # Template literal con backtick — puede ser multilinea
        elif codigo[i] == "`":
            i += 1
            while i < n:
                if codigo[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if codigo[i] == "`":
                    i += 1
                    break
                if codigo[i] == "\n":
                    resultado.append("\n")
                i += 1

        # String " o '
        elif codigo[i] in ('"', "'"):
            delim = codigo[i]
            i += 1
            while i < n:
                if codigo[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if codigo[i] == delim:
                    i += 1
                    break
                if codigo[i] == "\n":
                    resultado.append("\n")
                i += 1

        else:
            resultado.append(codigo[i])
            i += 1

    return "".join(resultado)


def limpiar_c_cpp(codigo: str) -> str:
    """Elimina strings y comentarios C/C++ para evitar falsos positivos en regex.

    Maneja: '', "", comentarios // y /* */
    Preserva saltos de linea.
    """
    resultado = []
    i = 0
    n = len(codigo)

    while i < n:
        # Comentario de bloque
        if codigo[i:i+2] == "/*":
            fin = codigo.find("*/", i + 2)
            if fin == -1:
                bloque = codigo[i:]
                resultado.append("\n" * bloque.count("\n"))
                break
            bloque = codigo[i:fin + 2]
            resultado.append("\n" * bloque.count("\n"))
            i = fin + 2

        # Comentario de linea
        elif codigo[i:i+2] == "//":
            fin = codigo.find("\n", i)
            if fin == -1:
                break
            resultado.append("\n")
            i = fin + 1

        # String caracter ' (puede ser 'a' o '\n')
        elif codigo[i] == "'":
            i += 1
            while i < n:
                if codigo[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if codigo[i] == "'":
                    i += 1
                    break
                i += 1

        # String "
        elif codigo[i] == '"':
            i += 1
            while i < n:
                if codigo[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                if codigo[i] == '"':
                    i += 1
                    break
                if codigo[i] == "\n":
                    resultado.append("\n")
                i += 1

        else:
            resultado.append(codigo[i])
            i += 1

    return "".join(resultado)


# ===========================================================================
# Mapa de scopes por llaves
# ===========================================================================

# Patrones para detectar que abre cada bloque {
_RE_CLASE = re.compile(
    r'\b(?:class|struct|interface|enum)\s+(\w+)', re.IGNORECASE
)
_RE_FUNCION = re.compile(
    r'\b(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)\s*(?:async\s*)?\{?\s*$'
)
_RE_NOMBRADO = re.compile(r'\b(\w+)\s*\{')


def mapa_scopes_llaves(lineas: list[str]) -> list[str]:
    """Devuelve lista paralela con el scope de cada linea.

    Valores posibles:
        'modulo'           → nivel 0, fuera de cualquier bloque
        'clase:Nombre'     → dentro del cuerpo de una clase
        'funcion:Nombre'   → dentro de una funcion o metodo
        'bloque'           → if, for, while, lambda, etc.
    """
    scopes: list[str] = []
    # Pila de (tipo, nombre) donde tipo es 'clase'|'funcion'|'bloque'
    pila: list[tuple[str, str]] = []
    profundidad = 0

    for linea in lineas:
        stripped = linea.strip()

        # Scope actual antes de procesar esta linea
        if not pila:
            scope_actual = "modulo"
        else:
            tipo, nombre = pila[-1]
            if tipo == "clase":
                scope_actual = f"clase:{nombre}"
            elif tipo == "funcion":
                scope_actual = f"funcion:{nombre}"
            else:
                scope_actual = "bloque"

        scopes.append(scope_actual)

        # Contar llaves que abren y cierran en esta linea
        abre = stripped.count("{")
        cierra = stripped.count("}")

        for _ in range(abre):
            profundidad += 1
            # Determinar que tipo de bloque abre
            m_clase = _RE_CLASE.search(stripped)
            if m_clase:
                pila.append(("clase", m_clase.group(1)))
            elif _RE_FUNCION.search(stripped):
                m_fn = _RE_FUNCION.search(stripped)
                nombre_fn = m_fn.group(1) if m_fn else "?"
                pila.append(("funcion", nombre_fn))
            else:
                pila.append(("bloque", ""))

        for _ in range(cierra):
            profundidad = max(0, profundidad - 1)
            if pila:
                pila.pop()

    return scopes


# ===========================================================================
# Extraccion de bloques y llamadas
# ===========================================================================

def extraer_bloque_llaves(lineas: list[str], linea_inicio: int) -> tuple[int, str]:
    """Extrae el texto de un bloque { } balanceado desde linea_inicio.

    Returns:
        (linea_fin, texto_completo_del_bloque)
    """
    profundidad = 0
    inicio_encontrado = False
    lineas_bloque = []
    i = linea_inicio

    while i < len(lineas):
        linea = lineas[i]
        lineas_bloque.append(linea)

        for ch in linea:
            if ch == "{":
                profundidad += 1
                inicio_encontrado = True
            elif ch == "}" and inicio_encontrado:
                profundidad -= 1
                if profundidad == 0:
                    return i, "\n".join(lineas_bloque)
        i += 1

    # Bloque no cerrado — devolver lo que hay
    return i - 1, "\n".join(lineas_bloque)


def extraer_llamadas_texto(texto: str, patron: re.Pattern) -> list[LlamadaInfo]:
    """Extrae llamadas unicas desde texto ya limpio.

    Args:
        texto:  Codigo fuente ya pasado por el limpiador correspondiente.
        patron: Regex con grupo 1 capturando el nombre de la llamada.

    Returns:
        Lista de LlamadaInfo unicas en orden de primera aparicion.
        Excluye LLAMADAS_EXCLUIDAS y palabras de control de flujo.
    """
    vistas: set[str] = set()
    resultado: list[LlamadaInfo] = []

    excluidas = set(LLAMADAS_EXCLUIDAS) | _CONTROL_FLOW

    for m in patron.finditer(texto):
        nombre = m.group(1).strip()
        if not nombre:
            continue
        if nombre in excluidas:
            continue
        if nombre[0].isupper():
            # Constructor o clase — incluir igual (pueden ser llamadas validas)
            pass
        if nombre not in vistas:
            vistas.add(nombre)
            resultado.append(LlamadaInfo(nombre=nombre))

    return resultado