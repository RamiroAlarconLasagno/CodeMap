# tests/test_dart_parser.py
"""Tests del parser Dart. Usa tests/fixtures/sample.dart como fuente."""

from pathlib import Path

import pytest

from core.analyzer.dart_parser import parsear_archivo
from core.index import ArchivoInfo

FIXTURE = Path(__file__).parent / "fixtures" / "sample.dart"


@pytest.fixture(scope="module")
def info() -> ArchivoInfo:
    """Parsea sample.dart una sola vez para todos los tests del modulo."""
    assert FIXTURE.exists(), f"Fixture no encontrado: {FIXTURE}"
    return parsear_archivo(FIXTURE, FIXTURE.parent.parent)


# ---------------------------------------------------------------------------
# Salud general
# ---------------------------------------------------------------------------

def test_sin_error(info):
    assert info.error is None


def test_lenguaje(info):
    assert info.lenguaje == "dart"


def test_nombre_archivo(info):
    assert info.nombre == "sample.dart"


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

def test_imports_detectados(info):
    modulos = [i.modulo for i in info.imports]
    assert "package:flutter/material.dart" in modulos
    assert "dart:async" in modulos
    assert "package:http/http.dart" in modulos


def test_import_con_show(info):
    imp = next(i for i in info.imports if "http" in i.modulo)
    assert "get" in imp.nombres or "post" in imp.nombres


def test_import_con_alias_registrado(info):
    # dart:async se importa con alias 'async' y show Future, Stream
    imp = next((i for i in info.imports if i.modulo == "dart:async"), None)
    assert imp is not None


# ---------------------------------------------------------------------------
# Clases
# ---------------------------------------------------------------------------

def test_clases_detectadas(info):
    nombres = [c.nombre for c in info.clases]
    assert "Sensor" in nombres
    assert "SensorTemperatura" in nombres


def test_mixin_detectado(info):
    nombres = [c.nombre for c in info.clases]
    assert "LoggableMixin" in nombres


def test_enum_detectado(info):
    nombres = [c.nombre for c in info.clases]
    assert "EstadoConexion" in nombres


def test_clase_herencia(info):
    sensor_temp = next(c for c in info.clases if c.nombre == "SensorTemperatura")
    assert "Sensor" in sensor_temp.clases_base


def test_clase_con_mixin(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    assert "LoggableMixin" in sensor.clases_base


# ---------------------------------------------------------------------------
# Metodos
# ---------------------------------------------------------------------------

def test_metodos_sensor(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    nombres = [m.nombre for m in sensor.metodos]
    assert "leer" in nombres


def test_metodo_async(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    leer = next(m for m in sensor.metodos if m.nombre == "leer")
    assert leer.es_async is True


def test_metodo_no_async(info):
    mixin = next(c for c in info.clases if c.nombre == "LoggableMixin")
    registrar = next((m for m in mixin.metodos if m.nombre == "registrar"), None)
    assert registrar is not None
    assert registrar.es_async is False


def test_constructor_detectado(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    nombres = [m.nombre for m in sensor.metodos]
    # Constructor principal o nombrado deben aparecer
    assert "Sensor" in nombres or "simulado" in nombres


def test_constructor_nombrado(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    nombres = [m.nombre for m in sensor.metodos]
    assert "simulado" in nombres


def test_override_detectado(info):
    sensor_temp = next(c for c in info.clases if c.nombre == "SensorTemperatura")
    nombres = [m.nombre for m in sensor_temp.metodos]
    assert "leer" in nombres


# ---------------------------------------------------------------------------
# Atributos
# ---------------------------------------------------------------------------

def test_atributos_sensor(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    nombres = [a.nombre for a in sensor.atributos]
    assert "id" in nombres or "_ultimo_valor" in nombres or "_instancias" in nombres


def test_atributo_scope_clase(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    for attr in sensor.atributos:
        assert attr.scope == "clase"


# ---------------------------------------------------------------------------
# Funciones sueltas
# ---------------------------------------------------------------------------

def test_funciones_detectadas(info):
    nombres = [f.nombre for f in info.funciones]
    assert "inicializar" in nombres
    assert "parsearConfig" in nombres


def test_funcion_async(info):
    inicializar = next(f for f in info.funciones if f.nombre == "inicializar")
    assert inicializar.es_async is True


def test_funcion_no_async(info):
    parsear = next(f for f in info.funciones if f.nombre == "parsearConfig")
    assert parsear.es_async is False


# ---------------------------------------------------------------------------
# Variables de modulo
# ---------------------------------------------------------------------------

def test_variables_modulo_detectadas(info):
    nombres = [v.nombre for v in info.variables]
    assert "VERSION" in nombres or "MAX_REINTENTOS" in nombres


def test_variables_scope_modulo(info):
    for var in info.variables:
        assert var.scope == "modulo"


# ---------------------------------------------------------------------------
# Llamadas
# ---------------------------------------------------------------------------

def test_llamadas_en_metodo(info):
    sensor = next(c for c in info.clases if c.nombre == "Sensor")
    leer = next(m for m in sensor.metodos if m.nombre == "leer")
    # leer() llama a _fetch y notifyListeners
    nombres_llamadas = [ll.nombre for ll in leer.llamadas]
    assert len(nombres_llamadas) >= 1


def test_llamadas_unicas(info):
    """Ninguna llamada debe repetirse dentro del mismo metodo."""
    for clase in info.clases:
        for metodo in clase.metodos:
            nombres = [ll.nombre for ll in metodo.llamadas]
            assert len(nombres) == len(set(nombres)), (
                f"Llamadas duplicadas en {clase.nombre}.{metodo.nombre}: {nombres}"
            )


# ---------------------------------------------------------------------------
# Robustez
# ---------------------------------------------------------------------------

def test_archivo_inexistente(tmp_path):
    resultado = parsear_archivo(tmp_path / "no_existe.dart", tmp_path)
    assert resultado.error is not None


def test_archivo_vacio(tmp_path):
    f = tmp_path / "vacio.dart"
    f.write_text("")
    resultado = parsear_archivo(f, tmp_path)
    assert resultado.error is None
    assert resultado.clases == []
    assert resultado.funciones == []
    assert resultado.imports == []