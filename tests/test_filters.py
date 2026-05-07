# tests/test_filters.py

import pytest

from core.filters import f_buscar, f_idioma, f_libreria


# ---------------------------------------------------------------------------
# f_libreria
# ---------------------------------------------------------------------------

def test_libreria_encuentra_por_import(indice):
    resultado = f_libreria(indice, "socket")
    tipos = [r["tipo"] for r in resultado]
    assert "import" in tipos


def test_libreria_encuentra_por_llamada(indice):
    resultado = f_libreria(indice, "socket")
    tipos = [r["tipo"] for r in resultado]
    assert "llamada" in tipos


def test_libreria_busqueda_parcial(indice):
    # "log" coincide con "logging" en imports y "logger" en llamadas
    resultado = f_libreria(indice, "log")
    assert len(resultado) > 0


def test_libreria_no_encontrada(indice):
    resultado = f_libreria(indice, "libreria_inexistente_xyz")
    assert resultado == []


def test_libreria_resultado_tiene_campos(indice):
    resultado = f_libreria(indice, "socket")
    for r in resultado:
        assert "archivo" in r
        assert "tipo" in r
        assert "simbolo" in r
        assert "detalle" in r


def test_libreria_import_simbolo_es_none(indice):
    resultado = f_libreria(indice, "socket")
    imports = [r for r in resultado if r["tipo"] == "import"]
    assert all(r["simbolo"] is None for r in imports)


def test_libreria_llamada_incluye_simbolo(indice):
    resultado = f_libreria(indice, "socket")
    llamadas = [r for r in resultado if r["tipo"] == "llamada"]
    assert all(r["simbolo"] is not None for r in llamadas)


def test_libreria_case_insensitive(indice):
    resultado_lower = f_libreria(indice, "socket")
    resultado_upper = f_libreria(indice, "SOCKET")
    assert len(resultado_lower) == len(resultado_upper)


def test_libreria_json_en_metodo(indice):
    # json.loads aparece en Parser.procesar
    resultado = f_libreria(indice, "json")
    simbolos = [r["simbolo"] for r in resultado if r["tipo"] == "llamada"]
    assert any("Parser" in s for s in simbolos)


# ---------------------------------------------------------------------------
# f_buscar
# ---------------------------------------------------------------------------

def test_buscar_subcadena(indice):
    resultado = f_buscar(indice, "cliente")
    assert len(resultado) > 0
    nombres = [r["nombre"] for r in resultado]
    assert any("ClienteMQTT" in n for n in nombres)


def test_buscar_wildcard_asterisco(indice):
    resultado = f_buscar(indice, "*MQTT*")
    assert len(resultado) > 0
    assert all("MQTT" in r["nombre"] for r in resultado)


def test_buscar_wildcard_interrogacion(indice):
    # Parser tiene 6 letras, P?rser no coincide pero Par?er si
    resultado = f_buscar(indice, "Par?er")
    assert any(r["nombre"] == "Parser" for r in resultado)


def test_buscar_encuentra_metodos(indice):
    resultado = f_buscar(indice, "conectar")
    assert len(resultado) > 0
    assert resultado[0]["tipo"] == "metodo"
    assert "ClienteMQTT.conectar" in resultado[0]["nombre"]


def test_buscar_encuentra_funciones(indice):
    resultado = f_buscar(indice, "crear")
    assert any(r["tipo"] == "funcion" for r in resultado)


def test_buscar_encuentra_clases(indice):
    resultado = f_buscar(indice, "Parser")
    clases = [r for r in resultado if r["tipo"] == "clase"]
    assert len(clases) == 1


def test_buscar_sin_resultados(indice):
    resultado = f_buscar(indice, "xyz_no_existe_abc")
    assert resultado == []


def test_buscar_resultado_tiene_campos(indice):
    resultado = f_buscar(indice, "conectar")
    r = resultado[0]
    assert "archivo" in r
    assert "tipo" in r
    assert "nombre" in r
    assert "firma" in r
    assert "linea" in r


def test_buscar_case_insensitive(indice):
    resultado_lower = f_buscar(indice, "parser")
    resultado_upper = f_buscar(indice, "PARSER")
    assert len(resultado_lower) == len(resultado_upper)


def test_buscar_wildcard_todo(indice):
    # * solo deberia devolver todo
    resultado = f_buscar(indice, "*")
    assert len(resultado) > 0


# ---------------------------------------------------------------------------
# f_idioma
# ---------------------------------------------------------------------------

def test_idioma_devuelve_estructura(indice):
    resultado = f_idioma(indice)
    assert "idioma_dominante" in resultado
    assert "conteo_es" in resultado
    assert "conteo_en" in resultado
    assert "archivos_con_mezcla" in resultado


def test_idioma_dominante_es_valido(indice):
    resultado = f_idioma(indice)
    assert resultado["idioma_dominante"] in ("es", "en", "indeterminado")


def test_idioma_conteos_no_negativos(indice):
    resultado = f_idioma(indice)
    assert resultado["conteo_es"] >= 0
    assert resultado["conteo_en"] >= 0


def test_idioma_archivos_mezcla_es_lista(indice):
    resultado = f_idioma(indice)
    assert isinstance(resultado["archivos_con_mezcla"], list)


def test_idioma_detecta_espanol():
    """Indice con nombres puramente en espanol."""
    from pathlib import Path
    from core.index import (
        ArchivoInfo, ClaseInfo, FuncionInfo, MetodoInfo, ProjectIndex
    )
    idx = ProjectIndex(carpeta_raiz=Path("/tmp"))
    archivo = ArchivoInfo(
        ruta_relativa="a.py", carpeta=".", nombre="a.py", lenguaje="python"
    )
    archivo.clases = [
        ClaseInfo(
            nombre="ClienteConexion",
            firma="ClienteConexion()",
            docstring="",
            metodos=[
                MetodoInfo(nombre="conectar", firma="conectar()", docstring=""),
                MetodoInfo(nombre="enviar", firma="enviar()", docstring=""),
                MetodoInfo(nombre="guardar", firma="guardar()", docstring=""),
            ],
        )
    ]
    idx.archivos = {"a.py": archivo}
    resultado = f_idioma(idx)
    assert resultado["conteo_es"] > 0


def test_idioma_detecta_ingles():
    """Indice con nombres puramente en ingles."""
    from pathlib import Path
    from core.index import (
        ArchivoInfo, ClaseInfo, FuncionInfo, MetodoInfo, ProjectIndex
    )
    idx = ProjectIndex(carpeta_raiz=Path("/tmp"))
    archivo = ArchivoInfo(
        ruta_relativa="b.py", carpeta=".", nombre="b.py", lenguaje="python"
    )
    archivo.clases = [
        ClaseInfo(
            nombre="ConnectionManager",
            firma="ConnectionManager()",
            docstring="",
            metodos=[
                MetodoInfo(nombre="connect", firma="connect()", docstring=""),
                MetodoInfo(nombre="send", firma="send()", docstring=""),
                MetodoInfo(nombre="save", firma="save()", docstring=""),
            ],
        )
    ]
    idx.archivos = {"b.py": archivo}
    resultado = f_idioma(idx)
    assert resultado["conteo_en"] > 0


def test_idioma_indice_vacio():
    from pathlib import Path
    from core.index import ProjectIndex
    idx = ProjectIndex(carpeta_raiz=Path("/tmp"))
    resultado = f_idioma(idx)
    assert resultado["idioma_dominante"] == "indeterminado"
    assert resultado["conteo_es"] == 0
    assert resultado["conteo_en"] == 0