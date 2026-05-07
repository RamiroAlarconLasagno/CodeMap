# tests/test_formatters.py

import pytest

from shared.formatters import exportar_md, exportar_txt


# ---------------------------------------------------------------------------
# Validacion de nivel
# ---------------------------------------------------------------------------

def test_nivel_invalido_txt(indice):
    with pytest.raises(ValueError, match="nivel debe ser"):
        exportar_txt(indice, nivel="invalido")


def test_nivel_invalido_md(indice):
    with pytest.raises(ValueError, match="nivel debe ser"):
        exportar_md(indice, nivel="todo")


# ---------------------------------------------------------------------------
# exportar_txt — estructura
# ---------------------------------------------------------------------------

def test_txt_estructura_contiene_clases(indice):
    salida = exportar_txt(indice, nivel="estructura")
    assert "ClienteMQTT" in salida
    assert "Parser" in salida


def test_txt_estructura_contiene_funciones(indice):
    salida = exportar_txt(indice, nivel="estructura")
    assert "crear_cliente" in salida


def test_txt_estructura_contiene_variables(indice):
    salida = exportar_txt(indice, nivel="estructura")
    assert "TIMEOUT" in salida


def test_txt_estructura_no_contiene_firmas(indice):
    salida = exportar_txt(indice, nivel="estructura")
    # En modo estructura no aparecen los tipos de los parametros
    assert "host: str" not in salida


def test_txt_estructura_no_contiene_llamadas(indice):
    salida = exportar_txt(indice, nivel="estructura")
    assert "socket.connect" not in salida


# ---------------------------------------------------------------------------
# exportar_txt — firmas
# ---------------------------------------------------------------------------

def test_txt_firmas_contiene_firmas(indice):
    salida = exportar_txt(indice, nivel="firmas")
    assert "conectar(self, host: str, puerto: int) -> bool" in salida


def test_txt_firmas_contiene_docstrings(indice):
    salida = exportar_txt(indice, nivel="firmas")
    assert "Establece la conexion" in salida


def test_txt_firmas_no_contiene_llamadas(indice):
    salida = exportar_txt(indice, nivel="firmas")
    assert "socket.connect" not in salida


# ---------------------------------------------------------------------------
# exportar_txt — completo
# ---------------------------------------------------------------------------

def test_txt_completo_contiene_llamadas(indice):
    salida = exportar_txt(indice, nivel="completo")
    assert "socket.connect" in salida
    assert "logger.info" in salida


def test_txt_completo_contiene_todo(indice):
    salida = exportar_txt(indice, nivel="completo")
    assert "ClienteMQTT" in salida
    assert "conectar(self, host: str" in salida
    assert "socket.connect" in salida


# ---------------------------------------------------------------------------
# exportar_md — estructura general
# ---------------------------------------------------------------------------

def test_md_contiene_headers(indice):
    salida = exportar_md(indice, nivel="estructura")
    assert "# CodeMap" in salida
    assert "## `red/cliente.py`" in salida
    assert "## `util/parser.py`" in salida


def test_md_contiene_resumen(indice):
    salida = exportar_md(indice, nivel="firmas")
    assert "Archivos:" in salida
    assert "Clases:" in salida


def test_md_marca_archivos_con_error(indice):
    salida = exportar_md(indice, nivel="estructura")
    assert "Error" in salida
    assert "SyntaxError" in salida


def test_md_firmas_contiene_firmas(indice):
    salida = exportar_md(indice, nivel="firmas")
    assert "conectar(self, host: str, puerto: int) -> bool" in salida


def test_md_completo_contiene_llamadas(indice):
    salida = exportar_md(indice, nivel="completo")
    assert "socket.connect" in salida


# ---------------------------------------------------------------------------
# Propiedades generales
# ---------------------------------------------------------------------------

def test_txt_devuelve_string(indice):
    for nivel in ("estructura", "firmas", "completo"):
        assert isinstance(exportar_txt(indice, nivel), str)


def test_md_devuelve_string(indice):
    for nivel in ("estructura", "firmas", "completo"):
        assert isinstance(exportar_md(indice, nivel), str)


def test_archivos_ordenados_alfabeticamente(indice):
    salida = exportar_md(indice, nivel="estructura")
    pos_red = salida.find("red/cliente.py")
    pos_util = salida.find("util/parser.py")
    assert pos_red < pos_util