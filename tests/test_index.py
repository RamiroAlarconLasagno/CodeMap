# tests/test_index.py

from datetime import datetime
from pathlib import Path

import pytest

from core.index import (
    ArchivoInfo,
    ClaseInfo,
    FuncionInfo,
    ImportInfo,
    LlamadaInfo,
    MetodoInfo,
    ProjectIndex,
    VariableInfo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _archivo(nombre: str = "mod.py", lenguaje: str = "python") -> ArchivoInfo:
    return ArchivoInfo(
        ruta_relativa=nombre,
        carpeta=".",
        nombre=nombre,
        lenguaje=lenguaje,
    )


def _indice_vacio() -> ProjectIndex:
    return ProjectIndex(carpeta_raiz=Path("/tmp/proyecto"))


def _indice_con_archivos() -> ProjectIndex:
    idx = _indice_vacio()

    clase = ClaseInfo(
        nombre="MiClase",
        firma="MiClase(x: int)",
        docstring="Una clase.",
        clases_base=["Base"],
        metodos=[
            MetodoInfo(nombre="hacer", firma="hacer(self) -> None", docstring=""),
            MetodoInfo(nombre="calcular", firma="calcular(self, n: int) -> int", docstring=""),
        ],
        atributos=[
            VariableInfo(nombre="x", tipo="int", valor_inicial="0", scope="clase", linea=5),
        ],
        linea=10,
    )

    archivo_a = _archivo("a.py")
    archivo_a.clases = [clase]
    archivo_a.funciones = [
        FuncionInfo(nombre="helper", firma="helper(v: str) -> str", docstring=""),
        FuncionInfo(nombre="util", firma="util() -> None", docstring=""),
    ]
    archivo_a.variables = [
        VariableInfo(nombre="CONSTANTE", tipo="str", valor_inicial='"x"', scope="modulo", linea=1),
    ]

    archivo_b = _archivo("b.py")
    archivo_b.clases = [
        ClaseInfo(nombre="OtraClase", firma="OtraClase()", docstring="", linea=1),
    ]

    idx.archivos = {"a.py": archivo_a, "b.py": archivo_b}
    idx.ultimo_analisis = datetime(2024, 1, 1, 12, 0, 0)
    return idx


# ---------------------------------------------------------------------------
# LlamadaInfo
# ---------------------------------------------------------------------------

def test_llamada_info_crea_correctamente():
    llamada = LlamadaInfo(nombre="mi_funcion")
    assert llamada.nombre == "mi_funcion"


# ---------------------------------------------------------------------------
# VariableInfo
# ---------------------------------------------------------------------------

def test_variable_info_campos():
    v = VariableInfo(nombre="x", tipo="int", valor_inicial="5", scope="modulo", linea=3)
    assert v.nombre == "x"
    assert v.tipo == "int"
    assert v.valor_inicial == "5"
    assert v.scope == "modulo"
    assert v.linea == 3


def test_variable_info_tipo_opcional():
    v = VariableInfo(nombre="y", tipo=None, valor_inicial=None, scope="clase", linea=1)
    assert v.tipo is None
    assert v.valor_inicial is None


# ---------------------------------------------------------------------------
# MetodoInfo
# ---------------------------------------------------------------------------

def test_metodo_info_defaults():
    m = MetodoInfo(nombre="hacer", firma="hacer(self)", docstring="Hace algo.")
    assert m.decoradores == []
    assert m.es_async is False
    assert m.llamadas == []
    assert m.linea == 0


def test_metodo_info_completo():
    llamadas = [LlamadaInfo("otra_funcion"), LlamadaInfo("helper")]
    m = MetodoInfo(
        nombre="procesar",
        firma="procesar(self, datos: list) -> dict",
        docstring="Procesa.",
        decoradores=["@property"],
        es_async=True,
        llamadas=llamadas,
        linea=42,
    )
    assert m.es_async is True
    assert len(m.llamadas) == 2
    assert m.decoradores == ["@property"]


# ---------------------------------------------------------------------------
# ClaseInfo
# ---------------------------------------------------------------------------

def test_clase_info_defaults():
    c = ClaseInfo(nombre="Foo", firma="Foo()", docstring="")
    assert c.clases_base == []
    assert c.metodos == []
    assert c.atributos == []
    assert c.linea == 0


def test_clase_info_con_herencia():
    c = ClaseInfo(
        nombre="Hija",
        firma="Hija(x: int)",
        docstring="",
        clases_base=["Padre", "Mixin"],
    )
    assert len(c.clases_base) == 2
    assert "Padre" in c.clases_base


# ---------------------------------------------------------------------------
# FuncionInfo
# ---------------------------------------------------------------------------

def test_funcion_info_defaults():
    f = FuncionInfo(nombre="mi_func", firma="mi_func() -> None", docstring="")
    assert f.decoradores == []
    assert f.es_async is False
    assert f.llamadas == []


# ---------------------------------------------------------------------------
# ImportInfo
# ---------------------------------------------------------------------------

def test_import_info_simple():
    i = ImportInfo(modulo="os")
    assert i.modulo == "os"
    assert i.nombres == []
    assert i.es_from is False


def test_import_info_from():
    i = ImportInfo(modulo="pathlib", nombres=["Path"], es_from=True)
    assert i.es_from is True
    assert "Path" in i.nombres


# ---------------------------------------------------------------------------
# ArchivoInfo
# ---------------------------------------------------------------------------

def test_archivo_info_defaults():
    a = _archivo()
    assert a.clases == []
    assert a.funciones == []
    assert a.variables == []
    assert a.imports == []
    assert a.error is None


def test_archivo_info_con_error():
    a = _archivo()
    a.error = "SyntaxError en linea 5"
    assert a.error is not None


# ---------------------------------------------------------------------------
# ProjectIndex — estado vacio
# ---------------------------------------------------------------------------

def test_indice_vacio():
    idx = _indice_vacio()
    assert idx.esta_vacio() is True
    assert idx.total_archivos() == 0
    assert idx.total_clases() == 0
    assert idx.total_funciones() == 0
    assert idx.total_metodos() == 0
    assert idx.total_variables() == 0
    assert idx.ultimo_analisis is None


# ---------------------------------------------------------------------------
# ProjectIndex — conteos
# ---------------------------------------------------------------------------

def test_indice_total_archivos():
    idx = _indice_con_archivos()
    assert idx.total_archivos() == 2


def test_indice_total_clases():
    idx = _indice_con_archivos()
    # a.py tiene 1 clase, b.py tiene 1 clase
    assert idx.total_clases() == 2


def test_indice_total_funciones():
    idx = _indice_con_archivos()
    # a.py tiene 2 funciones sueltas, b.py ninguna
    assert idx.total_funciones() == 2


def test_indice_total_metodos():
    idx = _indice_con_archivos()
    # MiClase tiene 2 metodos, OtraClase tiene 0
    assert idx.total_metodos() == 2


def test_indice_total_variables():
    idx = _indice_con_archivos()
    # a.py tiene 1 variable de modulo, b.py ninguna
    assert idx.total_variables() == 1


def test_indice_no_esta_vacio():
    idx = _indice_con_archivos()
    assert idx.esta_vacio() is False


def test_indice_carpeta_raiz():
    idx = ProjectIndex(carpeta_raiz=Path("/mi/proyecto"))
    assert idx.carpeta_raiz == Path("/mi/proyecto")


def test_indice_ultimo_analisis():
    idx = _indice_con_archivos()
    assert idx.ultimo_analisis == datetime(2024, 1, 1, 12, 0, 0)