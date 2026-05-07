# tests/test_python_parser.py

from pathlib import Path

import pytest

from core.analyzer.python_parser import parsear_archivo

FIXTURE = Path(__file__).parent / "fixtures" / "sample.py"


@pytest.fixture
def info():
    return parsear_archivo(FIXTURE, FIXTURE.parent)


# ---------------------------------------------------------------------------
# Archivo general
# ---------------------------------------------------------------------------

def test_sin_error(info):
    assert info.error is None


def test_lenguaje(info):
    assert info.lenguaje == "python"


def test_nombre_archivo(info):
    assert info.nombre == "sample.py"


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

def test_imports_detectados(info):
    modulos = [i.modulo for i in info.imports]
    assert "os" in modulos
    assert "sys" in modulos
    assert "pathlib" in modulos


def test_import_from(info):
    from_imports = [i for i in info.imports if i.es_from]
    assert any("Path" in i.nombres for i in from_imports)


def test_import_typing(info):
    modulos = [i.modulo for i in info.imports]
    assert "typing" in modulos


# ---------------------------------------------------------------------------
# Variables de modulo
# ---------------------------------------------------------------------------

def test_variables_modulo_detectadas(info):
    nombres = [v.nombre for v in info.variables]
    assert "CONSTANTE_MODULO" in nombres
    assert "VERSION" in nombres
    assert "DEBUG" in nombres


def test_variable_con_tipo(info):
    constante = next(v for v in info.variables if v.nombre == "CONSTANTE_MODULO")
    assert constante.tipo == "str"


def test_variable_con_valor(info):
    version = next(v for v in info.variables if v.nombre == "VERSION")
    assert version.valor_inicial is not None


def test_variables_scope_modulo(info):
    assert all(v.scope == "modulo" for v in info.variables)


# ---------------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------------

def test_clases_detectadas(info):
    nombres = [c.nombre for c in info.clases]
    assert "ClaseBase" in nombres
    assert "ClaseHija" in nombres
    assert "ClaseMultipleHerencia" in nombres


def test_clase_base_sin_herencia(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    assert clase.clases_base == []


def test_clase_hija_herencia(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseHija")
    assert "ClaseBase" in clase.clases_base


def test_clase_multiple_herencia(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseMultipleHerencia")
    assert len(clase.clases_base) == 2


def test_clase_docstring(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    assert "base" in clase.docstring.lower()


def test_clase_firma(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    assert "nombre" in clase.firma
    assert "str" in clase.firma


# ---------------------------------------------------------------------------
# Atributos de clase
# ---------------------------------------------------------------------------

def test_atributos_clase_base(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    nombres = [a.nombre for a in clase.atributos]
    # atributo_clase del cuerpo + nombre y activo del __init__
    assert "nombre" in nombres
    assert "activo" in nombres


def test_atributo_de_cuerpo_clase(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    nombres = [a.nombre for a in clase.atributos]
    assert "atributo_clase" in nombres


def test_atributo_scope_es_clase(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    assert all(a.scope == "clase" for a in clase.atributos)


# ---------------------------------------------------------------------------
# Metodos
# ---------------------------------------------------------------------------

def test_metodos_clase_base(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    nombres = [m.nombre for m in clase.metodos]
    assert "__init__" in nombres
    assert "metodo_simple" in nombres
    assert "nombre_upper" in nombres
    assert "metodo_estatico" in nombres
    assert "desde_dict" in nombres


def test_metodo_async(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseHija")
    metodo = next(m for m in clase.metodos if m.nombre == "metodo_async")
    assert metodo.es_async is True


def test_metodo_no_async(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    metodo = next(m for m in clase.metodos if m.nombre == "metodo_simple")
    assert metodo.es_async is False


def test_decoradores(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    metodo = next(m for m in clase.metodos if m.nombre == "nombre_upper")
    assert "@property" in metodo.decoradores


def test_decorador_staticmethod(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    metodo = next(m for m in clase.metodos if m.nombre == "metodo_estatico")
    assert "@staticmethod" in metodo.decoradores


def test_metodo_firma_incluye_tipo(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    metodo = next(m for m in clase.metodos if m.nombre == "metodo_simple")
    assert "-> str" in metodo.firma


def test_metodo_docstring(info):
    clase = next(c for c in info.clases if c.nombre == "ClaseBase")
    metodo = next(m for m in clase.metodos if m.nombre == "metodo_simple")
    assert metodo.docstring != ""


# ---------------------------------------------------------------------------
# Funciones sueltas
# ---------------------------------------------------------------------------

def test_funciones_detectadas(info):
    nombres = [f.nombre for f in info.funciones]
    assert "funcion_simple" in nombres
    assert "funcion_sin_tipo" in nombres
    assert "funcion_asincrona" in nombres


def test_funcion_async(info):
    fn = next(f for f in info.funciones if f.nombre == "funcion_asincrona")
    assert fn.es_async is True


def test_funcion_firma_con_tipos(info):
    fn = next(f for f in info.funciones if f.nombre == "funcion_simple")
    assert "x: int" in fn.firma
    assert "-> int" in fn.firma


def test_funcion_docstring(info):
    fn = next(f for f in info.funciones if f.nombre == "funcion_simple")
    assert fn.docstring != ""


def test_funcion_sin_tipo_firma(info):
    fn = next(f for f in info.funciones if f.nombre == "funcion_sin_tipo")
    assert "nombre" in fn.firma


# ---------------------------------------------------------------------------
# Archivo con error de sintaxis
# ---------------------------------------------------------------------------

def test_syntax_error_capturado(tmp_path):
    roto = tmp_path / "roto.py"
    roto.write_text("def funcion(\n    x =\n", encoding="utf-8")
    info = parsear_archivo(roto, tmp_path)
    assert info.error is not None
    assert "SyntaxError" in info.error


def test_archivo_vacio(tmp_path):
    vacio = tmp_path / "vacio.py"
    vacio.write_text("", encoding="utf-8")
    info = parsear_archivo(vacio, tmp_path)
    assert info.error is None
    assert info.clases == []
    assert info.funciones == []