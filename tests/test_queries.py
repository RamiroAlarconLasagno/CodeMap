# tests/test_queries.py

import pytest

from core.queries import (
    q_carpetas,
    q_clases,
    q_estado,
    q_funciones,
    q_imports,
    q_llamadas,
    q_metodos,
    q_usos,
    q_variables,
)


# ---------------------------------------------------------------------------
# q_carpetas
# ---------------------------------------------------------------------------

def test_carpetas_devuelve_arbol(indice):
    resultado = q_carpetas(indice)
    assert "red" in resultado
    assert "util" in resultado
    assert "cliente.py" in resultado["red"]
    assert "parser.py" in resultado["util"]


def test_carpetas_agrupa_por_carpeta(indice):
    resultado = q_carpetas(indice)
    # util tiene dos archivos
    assert len(resultado["util"]) == 2


# ---------------------------------------------------------------------------
# q_imports
# ---------------------------------------------------------------------------

def test_imports_todos(indice):
    resultado = q_imports(indice)
    assert "red/cliente.py" in resultado
    assert len(resultado["red/cliente.py"]) == 2


def test_imports_por_archivo(indice):
    resultado = q_imports(indice, archivo="util/parser.py")
    assert list(resultado.keys()) == ["util/parser.py"]
    assert resultado["util/parser.py"][0]["modulo"] == "json"


def test_imports_archivo_inexistente(indice):
    resultado = q_imports(indice, archivo="no_existe.py")
    assert resultado == {}


def test_imports_estructura_dict(indice):
    resultado = q_imports(indice, archivo="red/cliente.py")
    imp = resultado["red/cliente.py"][1]
    assert "modulo" in imp
    assert "nombres" in imp
    assert "es_from" in imp
    assert imp["es_from"] is True


# ---------------------------------------------------------------------------
# q_clases
# ---------------------------------------------------------------------------

def test_clases_todas(indice):
    resultado = q_clases(indice)
    assert "red/cliente.py" in resultado
    assert resultado["red/cliente.py"][0]["nombre"] == "ClienteMQTT"


def test_clases_por_archivo(indice):
    resultado = q_clases(indice, archivo="util/parser.py")
    assert len(resultado["util/parser.py"]) == 1
    assert resultado["util/parser.py"][0]["nombre"] == "Parser"


def test_clases_sin_metodos_en_resultado(indice):
    resultado = q_clases(indice, archivo="red/cliente.py")
    clase = resultado["red/cliente.py"][0]
    assert "metodos" not in clase
    assert "total_metodos" in clase
    assert clase["total_metodos"] == 2


def test_clases_incluye_bases(indice):
    resultado = q_clases(indice, archivo="red/cliente.py")
    assert "BaseCliente" in resultado["red/cliente.py"][0]["clases_base"]


# ---------------------------------------------------------------------------
# q_metodos
# ---------------------------------------------------------------------------

def test_metodos_clase_existente(indice):
    resultado = q_metodos(indice, "ClienteMQTT")
    assert resultado is not None
    assert resultado["clase"] == "ClienteMQTT"
    assert len(resultado["metodos"]) == 2


def test_metodos_incluye_firma_clase(indice):
    resultado = q_metodos(indice, "ClienteMQTT")
    assert "firma_clase" in resultado
    assert "ClienteMQTT" in resultado["firma_clase"]


def test_metodos_incluye_llamadas(indice):
    resultado = q_metodos(indice, "ClienteMQTT")
    metodo = next(m for m in resultado["metodos"] if m["nombre"] == "conectar")
    assert "socket.connect" in metodo["llamadas"]


def test_metodos_async_flag(indice):
    resultado = q_metodos(indice, "ClienteMQTT")
    enviar = next(m for m in resultado["metodos"] if m["nombre"] == "enviar")
    assert enviar["es_async"] is True


def test_metodos_clase_inexistente(indice):
    assert q_metodos(indice, "NoExiste") is None


def test_metodos_incluye_atributos(indice):
    resultado = q_metodos(indice, "ClienteMQTT")
    assert len(resultado["atributos"]) == 2
    nombres = [a["nombre"] for a in resultado["atributos"]]
    assert "host" in nombres


# ---------------------------------------------------------------------------
# q_funciones
# ---------------------------------------------------------------------------

def test_funciones_todas(indice):
    resultado = q_funciones(indice)
    assert "red/cliente.py" in resultado
    assert resultado["red/cliente.py"][0]["nombre"] == "crear_cliente"


def test_funciones_por_archivo(indice):
    resultado = q_funciones(indice, archivo="util/parser.py")
    assert resultado["util/parser.py"] == []


def test_funciones_incluye_llamadas(indice):
    resultado = q_funciones(indice, archivo="red/cliente.py")
    fn = resultado["red/cliente.py"][0]
    assert "ClienteMQTT" in fn["llamadas"]


# ---------------------------------------------------------------------------
# q_variables
# ---------------------------------------------------------------------------

def test_variables_scope_modulo(indice):
    resultado = q_variables(indice, archivo="red/cliente.py", scope="modulo")
    assert "red/cliente.py" in resultado
    nombres = [v["nombre"] for v in resultado["red/cliente.py"]]
    assert "TIMEOUT" in nombres
    assert "VERSION" in nombres


def test_variables_scope_clase(indice):
    resultado = q_variables(indice, archivo="red/cliente.py", scope="clase")
    assert "red/cliente.py" in resultado
    nombres = [v["nombre"] for v in resultado["red/cliente.py"]]
    assert "ClienteMQTT.host" in nombres


def test_variables_sin_scope_devuelve_todas(indice):
    resultado = q_variables(indice, archivo="red/cliente.py")
    nombres = [v["nombre"] for v in resultado["red/cliente.py"]]
    assert "TIMEOUT" in nombres
    assert "ClienteMQTT.host" in nombres


def test_variables_archivo_sin_variables(indice):
    resultado = q_variables(indice, archivo="util/parser.py", scope="modulo")
    assert "util/parser.py" not in resultado


# ---------------------------------------------------------------------------
# q_llamadas
# ---------------------------------------------------------------------------

def test_llamadas_metodo(indice):
    resultado = q_llamadas(indice, "ClienteMQTT.conectar")
    assert resultado is not None
    assert "socket.connect" in resultado["llamadas"]
    assert "logger.info" in resultado["llamadas"]


def test_llamadas_funcion_suelta(indice):
    resultado = q_llamadas(indice, "crear_cliente")
    assert resultado is not None
    assert "ClienteMQTT" in resultado["llamadas"]


def test_llamadas_simbolo_inexistente(indice):
    assert q_llamadas(indice, "NoExiste.metodo") is None
    assert q_llamadas(indice, "funcion_inexistente") is None


# ---------------------------------------------------------------------------
# q_usos
# ---------------------------------------------------------------------------

def test_usos_encuentra_simbolo(indice):
    resultado = q_usos(indice, "logger")
    assert len(resultado) > 0
    contextos = [u["contexto"] for u in resultado]
    assert any("conectar" in c or "enviar" in c for c in contextos)


def test_usos_busqueda_parcial(indice):
    # "socket" aparece en conectar y enviar
    resultado = q_usos(indice, "socket")
    assert len(resultado) >= 2


def test_usos_sin_resultados(indice):
    resultado = q_usos(indice, "simbolo_que_no_existe_xyz")
    assert resultado == []


def test_usos_estructura_dict(indice):
    resultado = q_usos(indice, "json")
    assert len(resultado) > 0
    uso = resultado[0]
    assert "archivo" in uso
    assert "contexto" in uso
    assert "llamada" in uso


# ---------------------------------------------------------------------------
# q_estado
# ---------------------------------------------------------------------------

def test_estado_totales(indice):
    resultado = q_estado(indice)
    assert resultado["total_archivos"] == 3
    assert resultado["total_clases"] == 2
    assert resultado["total_metodos"] == 3
    assert resultado["total_funciones"] == 1


def test_estado_carpeta_raiz(indice):
    resultado = q_estado(indice)
    assert "proyecto" in resultado["carpeta_raiz"]


def test_estado_archivos_con_error(indice):
    resultado = q_estado(indice)
    assert len(resultado["archivos_con_error"]) == 1
    assert resultado["archivos_con_error"][0]["archivo"] == "util/roto.py"


def test_estado_ultimo_analisis(indice):
    resultado = q_estado(indice)
    assert "2024-06-01" in resultado["ultimo_analisis"]