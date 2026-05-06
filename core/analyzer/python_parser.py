# core/analyzer/python_parser.py

from __future__ import annotations

import ast
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
from shared.config import LLAMADAS_EXCLUIDAS


# ---------------------------------------------------------------------------
# Punto de entrada publico
# ---------------------------------------------------------------------------

def parsear_archivo(ruta: Path, raiz: Path) -> ArchivoInfo:
    """Lee un archivo .py y devuelve su ArchivoInfo completo."""
    ruta_rel = ruta.relative_to(raiz).as_posix()
    carpeta = ruta.parent.relative_to(raiz).as_posix() if ruta.parent != raiz else "."

    try:
        codigo = ruta.read_text(encoding="utf-8", errors="replace")
        arbol = ast.parse(codigo, filename=str(ruta))
    except SyntaxError as e:
        return ArchivoInfo(
            ruta_relativa=ruta_rel,
            carpeta=carpeta,
            nombre=ruta.name,
            lenguaje="python",
            error=f"SyntaxError: {e}",
        )
    except Exception as e:
        return ArchivoInfo(
            ruta_relativa=ruta_rel,
            carpeta=carpeta,
            nombre=ruta.name,
            lenguaje="python",
            error=str(e),
        )

    clases = []
    funciones = []

    for nodo in ast.iter_child_nodes(arbol):
        if isinstance(nodo, ast.ClassDef):
            clases.append(_parsear_clase(nodo))
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funciones.append(_parsear_funcion(nodo))

    return ArchivoInfo(
        ruta_relativa=ruta_rel,
        carpeta=carpeta,
        nombre=ruta.name,
        lenguaje="python",
        clases=clases,
        funciones=funciones,
        variables=_extraer_variables_modulo(arbol),
        imports=_extraer_imports(arbol),
    )


# ---------------------------------------------------------------------------
# Construccion de firmas
# ---------------------------------------------------------------------------

def _firma_args(args: ast.arguments, omitir_self: bool = False) -> str:
    """Construye la lista de argumentos como string."""
    partes: list[str] = []
    # Calcular offset de defaults para args normales
    n_args = len(args.args)
    n_defaults = len(args.defaults)
    offset = n_args - n_defaults

    # Positional-only (antes de /)
    pos_only_count = len(args.posonlyargs)
    for i, arg in enumerate(args.posonlyargs):
        if omitir_self and i == 0:
            continue
        parte = _arg_con_tipo(arg)
        idx_default = i - (pos_only_count - len(args.defaults))
        if idx_default >= 0 and idx_default < len(args.defaults):
            parte += f" = {_valor_simple(args.defaults[idx_default]) or '...'}"
        partes.append(parte)
    if pos_only_count > (1 if omitir_self else 0):
        partes.append("/")

    # Args normales
    for i, arg in enumerate(args.args):
        if omitir_self and i == 0 and not args.posonlyargs:
            continue
        parte = _arg_con_tipo(arg)
        idx_default = i - offset
        if idx_default >= 0:
            parte += f" = {_valor_simple(args.defaults[idx_default]) or '...'}"
        partes.append(parte)

    # *args
    if args.vararg:
        partes.append(f"*{_arg_con_tipo(args.vararg)}")
    elif args.kwonlyargs:
        partes.append("*")

    # Keyword-only
    for i, arg in enumerate(args.kwonlyargs):
        parte = _arg_con_tipo(arg)
        if args.kw_defaults[i] is not None:
            parte += f" = {_valor_simple(args.kw_defaults[i]) or '...'}"
        partes.append(parte)

    # **kwargs
    if args.kwarg:
        partes.append(f"**{_arg_con_tipo(args.kwarg)}")

    return ", ".join(partes)


def _arg_con_tipo(arg: ast.arg) -> str:
    """Devuelve 'nombre: tipo' o 'nombre' si no tiene tipo."""
    if arg.annotation:
        return f"{arg.arg}: {ast.unparse(arg.annotation)}"
    return arg.arg


def _firma_funcion(nodo: ast.FunctionDef | ast.AsyncFunctionDef,
                   omitir_self: bool = False) -> str:
    """Construye la firma completa: nombre(args) -> retorno."""
    args_str = _firma_args(nodo.args, omitir_self=omitir_self)
    prefijo = "async " if isinstance(nodo, ast.AsyncFunctionDef) else ""
    retorno = ""
    if nodo.returns:
        retorno = f" -> {ast.unparse(nodo.returns)}"
    return f"{prefijo}{nodo.name}({args_str}){retorno}"


def _firma_clase(nodo: ast.ClassDef) -> str:
    """Firma basada en __init__ sin self. Si no hay __init__: NombreClase()."""
    for item in ast.iter_child_nodes(nodo):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == "__init__":
                args_str = _firma_args(item.args, omitir_self=True)
                return f"{nodo.name}({args_str})"
    return f"{nodo.name}()"


def _clases_base(nodo: ast.ClassDef) -> list[str]:
    """Extrae los nombres de las clases base."""
    bases = []
    for base in nodo.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            pass
    return bases


# ---------------------------------------------------------------------------
# Extraccion de valores literales
# ---------------------------------------------------------------------------

def _valor_simple(nodo) -> Optional[str]:
    """Extrae el valor solo si es un literal simple. No evalua expresiones."""
    if nodo is None:
        return None
    if isinstance(nodo, ast.Constant):
        return repr(nodo.value)
    if isinstance(nodo, ast.UnaryOp) and isinstance(nodo.op, ast.USub):
        if isinstance(nodo.operand, ast.Constant):
            return f"-{nodo.operand.value}"
    if isinstance(nodo, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
        try:
            return ast.unparse(nodo)
        except Exception:
            return None
    if isinstance(nodo, ast.Name):
        # None, True, False ya son Constant en Python 3.8+
        # pero por compatibilidad
        if nodo.id in ("None", "True", "False"):
            return nodo.id
    return None


# ---------------------------------------------------------------------------
# Extraccion de llamadas
# ---------------------------------------------------------------------------

class _VisitanteLlamadas(ast.NodeVisitor):
    """Extrae nombres de llamadas unicas en orden de aparicion."""

    def __init__(self):
        self._vistas: set[str] = set()
        self.llamadas: list[LlamadaInfo] = []

    def visit_Call(self, node: ast.Call):
        nombre = self._nombre_llamada(node.func)
        if nombre and nombre not in LLAMADAS_EXCLUIDAS and nombre not in self._vistas:
            self._vistas.add(nombre)
            self.llamadas.append(LlamadaInfo(nombre=nombre))
        self.generic_visit(node)

    def _nombre_llamada(self, nodo) -> Optional[str]:
        if isinstance(nodo, ast.Name):
            return nodo.id
        if isinstance(nodo, ast.Attribute):
            receptor = self._nombre_llamada(nodo.value)
            if receptor:
                return f"{receptor}.{nodo.attr}"
            return nodo.attr
        return None


def _extraer_llamadas(nodo: ast.AST) -> list[LlamadaInfo]:
    visitante = _VisitanteLlamadas()
    visitante.visit(nodo)
    return visitante.llamadas


# ---------------------------------------------------------------------------
# Extraccion de variables
# ---------------------------------------------------------------------------

def _extraer_variables_modulo(arbol: ast.Module) -> list[VariableInfo]:
    """Extrae variables de nivel modulo (AnnAssign y Assign)."""
    variables: list[VariableInfo] = []
    vistos: set[str] = set()

    for nodo in ast.iter_child_nodes(arbol):
        # x: int = 5
        if isinstance(nodo, ast.AnnAssign) and isinstance(nodo.target, ast.Name):
            nombre = nodo.target.id
            if nombre not in vistos:
                vistos.add(nombre)
                variables.append(VariableInfo(
                    nombre=nombre,
                    tipo=ast.unparse(nodo.annotation),
                    valor_inicial=_valor_simple(nodo.value),
                    scope="modulo",
                    linea=nodo.lineno,
                ))

        # x = 5  o  a, b = ...
        elif isinstance(nodo, ast.Assign):
            for target in nodo.targets:
                if isinstance(target, ast.Name):
                    nombre = target.id
                    if nombre not in vistos:
                        vistos.add(nombre)
                        variables.append(VariableInfo(
                            nombre=nombre,
                            tipo=None,
                            valor_inicial=_valor_simple(nodo.value),
                            scope="modulo",
                            linea=nodo.lineno,
                        ))
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name) and elt.id not in vistos:
                            vistos.add(elt.id)
                            variables.append(VariableInfo(
                                nombre=elt.id,
                                tipo=None,
                                valor_inicial=None,
                                scope="modulo",
                                linea=nodo.lineno,
                            ))

    return variables


def _extraer_atributos_clase(nodo: ast.ClassDef) -> list[VariableInfo]:
    """Extrae atributos de clase: cuerpo directo + self.x en __init__."""
    atributos: list[VariableInfo] = []
    vistos: set[str] = set()

    # Pasada 1: AnnAssign y Assign en cuerpo directo de clase
    for item in ast.iter_child_nodes(nodo):
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            nombre = item.target.id
            if nombre not in vistos:
                vistos.add(nombre)
                atributos.append(VariableInfo(
                    nombre=nombre,
                    tipo=ast.unparse(item.annotation),
                    valor_inicial=_valor_simple(item.value),
                    scope="clase",
                    linea=item.lineno,
                ))
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id not in vistos:
                    vistos.add(target.id)
                    atributos.append(VariableInfo(
                        nombre=target.id,
                        tipo=None,
                        valor_inicial=_valor_simple(item.value),
                        scope="clase",
                        linea=item.lineno,
                    ))

    # Pasada 2: self.x = ... dentro de __init__
    for item in ast.iter_child_nodes(nodo):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name != "__init__":
                continue
            for stmt in ast.walk(item):
                # self.x: tipo = valor
                if isinstance(stmt, ast.AnnAssign):
                    if (isinstance(stmt.target, ast.Attribute)
                            and isinstance(stmt.target.value, ast.Name)
                            and stmt.target.value.id == "self"):
                        nombre = stmt.target.attr
                        if nombre not in vistos:
                            vistos.add(nombre)
                            atributos.append(VariableInfo(
                                nombre=nombre,
                                tipo=ast.unparse(stmt.annotation),
                                valor_inicial=_valor_simple(stmt.value),
                                scope="clase",
                                linea=stmt.lineno,
                            ))
                # self.x = valor
                elif isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if (isinstance(target, ast.Attribute)
                                and isinstance(target.value, ast.Name)
                                and target.value.id == "self"):
                            nombre = target.attr
                            if nombre not in vistos:
                                vistos.add(nombre)
                                atributos.append(VariableInfo(
                                    nombre=nombre,
                                    tipo=None,
                                    valor_inicial=_valor_simple(stmt.value),
                                    scope="clase",
                                    linea=stmt.lineno,
                                ))

    return atributos


# ---------------------------------------------------------------------------
# Extraccion de imports
# ---------------------------------------------------------------------------

def _extraer_imports(arbol: ast.Module) -> list[ImportInfo]:
    imports = []
    for nodo in ast.iter_child_nodes(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append(ImportInfo(
                    modulo=alias.name,
                    nombres=[],
                    es_from=False,
                ))
        elif isinstance(nodo, ast.ImportFrom):
            modulo = nodo.module or ""
            nombres = [alias.name for alias in nodo.names]
            imports.append(ImportInfo(
                modulo=modulo,
                nombres=nombres,
                es_from=True,
            ))
    return imports


# ---------------------------------------------------------------------------
# Parseo de nodos individuales
# ---------------------------------------------------------------------------

def _docstring(nodo) -> str:
    """Extrae el docstring compactado a una linea."""
    doc = ast.get_docstring(nodo)
    if not doc:
        return ""
    # Compactar a una sola linea
    return " ".join(doc.split())


def _decoradores(nodo) -> list[str]:
    resultado = []
    for dec in nodo.decorator_list:
        try:
            resultado.append(f"@{ast.unparse(dec)}")
        except Exception:
            pass
    return resultado


def _parsear_metodo(nodo: ast.FunctionDef | ast.AsyncFunctionDef) -> MetodoInfo:
    return MetodoInfo(
        nombre=nodo.name,
        firma=_firma_funcion(nodo, omitir_self=True),
        docstring=_docstring(nodo),
        decoradores=_decoradores(nodo),
        es_async=isinstance(nodo, ast.AsyncFunctionDef),
        llamadas=_extraer_llamadas(nodo),
        linea=nodo.lineno,
    )


def _parsear_clase(nodo: ast.ClassDef) -> ClaseInfo:
    metodos = []
    for item in ast.iter_child_nodes(nodo):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            metodos.append(_parsear_metodo(item))

    return ClaseInfo(
        nombre=nodo.name,
        firma=_firma_clase(nodo),
        docstring=_docstring(nodo),
        clases_base=_clases_base(nodo),
        metodos=metodos,
        atributos=_extraer_atributos_clase(nodo),
        linea=nodo.lineno,
    )


def _parsear_funcion(nodo: ast.FunctionDef | ast.AsyncFunctionDef) -> FuncionInfo:
    return FuncionInfo(
        nombre=nodo.name,
        firma=_firma_funcion(nodo, omitir_self=False),
        docstring=_docstring(nodo),
        decoradores=_decoradores(nodo),
        es_async=isinstance(nodo, ast.AsyncFunctionDef),
        llamadas=_extraer_llamadas(nodo),
        linea=nodo.lineno,
    )