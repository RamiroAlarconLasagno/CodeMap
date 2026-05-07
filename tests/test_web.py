# tests/test_web.py
"""
Tests de la API REST (interfaces/web/).
Usa TestClient de FastAPI — no levanta uvicorn real.
El indice se carga en state antes de cada test.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import core.state as state
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
from interfaces.web.server import crear_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    state._reset()
    yield
    state._reset()


@pytest.fixture()
def indice_prueba():
    idx = ProjectIndex(carpeta_raiz=Path("/tmp/test"))
    idx.archivos["src/app.py"] = ArchivoInfo(
        ruta_relativa="src/app.py",
        carpeta="src",
        nombre="app.py",
        lenguaje="python",
        imports=[ImportInfo(modulo="os")],
        clases=[
            ClaseInfo(
                nombre="Aplicacion",
                firma="class Aplicacion:",
                docstring="Clase principal.",
                clases_base=[],
                atributos=[
                    VariableInfo(nombre="nombre", tipo="str", valor_inicial='"app"', scope="clase", linea=5)
                ],
                metodos=[
                    MetodoInfo(
                        nombre="iniciar",
                        firma="def iniciar(self) -> None:",
                        docstring="Inicia la app.",
                        decoradores=[],
                        es_async=False,
                        llamadas=[LlamadaInfo(nombre="os.path.exists")],
                        linea=8,
                    )
                ],
                linea=3,
            )
        ],
        funciones=[
            FuncionInfo(
                nombre="crear_app",
                firma="def crear_app() -> Aplicacion:",
                docstring="Fabrica.",
                decoradores=[],
                es_async=False,
                llamadas=[LlamadaInfo(nombre="Aplicacion")],
                linea=18,
            )
        ],
        variables=[
            VariableInfo(nombre="VERSION", tipo="str", valor_inicial='"1.0"', scope="modulo", linea=1)
        ],
    )
    state.set_indice(idx)
    return idx


@pytest.fixture()
def client(indice_prueba):
    app = crear_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /carpetas
# ---------------------------------------------------------------------------

def test_get_carpetas(client):
    r = client.get("/carpetas")
    assert r.status_code == 200
    assert "src" in r.json()


# ---------------------------------------------------------------------------
# /clases
# ---------------------------------------------------------------------------

def test_get_clases_sin_filtro(client):
    r = client.get("/clases")
    assert r.status_code == 200
    data = r.json()
    assert "src/app.py" in data
    assert data["src/app.py"][0]["nombre"] == "Aplicacion"


def test_get_clases_con_archivo(client):
    r = client.get("/clases", params={"archivo": "src/app.py"})
    assert r.status_code == 200
    assert "src/app.py" in r.json()


# ---------------------------------------------------------------------------
# /metodos/{clase}
# ---------------------------------------------------------------------------

def test_get_metodos_encontrado(client):
    r = client.get("/metodos/Aplicacion")
    assert r.status_code == 200
    data = r.json()
    assert data["clase"] == "Aplicacion"
    assert data["metodos"][0]["nombre"] == "iniciar"


def test_get_metodos_no_encontrado(client):
    r = client.get("/metodos/NoExiste")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# /funciones
# ---------------------------------------------------------------------------

def test_get_funciones(client):
    r = client.get("/funciones")
    assert r.status_code == 200
    assert r.json()["src/app.py"][0]["nombre"] == "crear_app"


# ---------------------------------------------------------------------------
# /imports
# ---------------------------------------------------------------------------

def test_get_imports(client):
    r = client.get("/imports")
    assert r.status_code == 200
    assert r.json()["src/app.py"][0]["modulo"] == "os"


# ---------------------------------------------------------------------------
# /variables
# ---------------------------------------------------------------------------

def test_get_variables_sin_filtro(client):
    r = client.get("/variables")
    assert r.status_code == 200
    assert "src/app.py" in r.json()


def test_get_variables_scope_modulo(client):
    r = client.get("/variables", params={"scope": "modulo"})
    assert r.status_code == 200
    nombres = [v["nombre"] for v in r.json()["src/app.py"]]
    assert "VERSION" in nombres


# ---------------------------------------------------------------------------
# /llamadas/{simbolo}
# ---------------------------------------------------------------------------

def test_get_llamadas_encontrado(client):
    r = client.get("/llamadas/Aplicacion.iniciar")
    assert r.status_code == 200
    assert "os.path.exists" in r.json()["llamadas"]


def test_get_llamadas_no_encontrado(client):
    r = client.get("/llamadas/NoExiste.metodo")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# /usos/{nombre}
# ---------------------------------------------------------------------------

def test_get_usos(client):
    r = client.get("/usos/Aplicacion")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# /libreria/{nombre}
# ---------------------------------------------------------------------------

def test_get_libreria(client):
    r = client.get("/libreria/os")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# /buscar
# ---------------------------------------------------------------------------

def test_get_buscar(client):
    r = client.get("/buscar", params={"patron": "*app*"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# /idioma
# ---------------------------------------------------------------------------

def test_get_idioma(client):
    r = client.get("/idioma")
    assert r.status_code == 200
    assert "idioma_dominante" in r.json()


# ---------------------------------------------------------------------------
# /estado
# ---------------------------------------------------------------------------

def test_get_estado(client):
    r = client.get("/estado")
    assert r.status_code == 200
    data = r.json()
    assert data["total_archivos"] == 1
    assert data["total_clases"] == 1


# ---------------------------------------------------------------------------
# /exportar/{nivel}
# ---------------------------------------------------------------------------

def test_get_exportar_firmas(client):
    r = client.get("/exportar/firmas")
    assert r.status_code == 200
    assert "Aplicacion" in r.text


def test_get_exportar_estructura(client):
    r = client.get("/exportar/estructura")
    assert r.status_code == 200
    assert len(r.text) > 0


def test_get_exportar_completo(client):
    r = client.get("/exportar/completo")
    assert r.status_code == 200


def test_get_exportar_nivel_invalido(client):
    r = client.get("/exportar/invalido")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# /carpeta (POST)
# ---------------------------------------------------------------------------

def test_post_carpeta_existente(client, tmp_path):
    r = client.post("/carpeta", json={"carpeta": str(tmp_path)})
    assert r.status_code == 200
    assert "carpeta_raiz" in r.json()


def test_post_carpeta_no_existe(client):
    r = client.post("/carpeta", json={"carpeta": "/ruta/que/no/existe/jamas"})
    assert r.status_code == 400