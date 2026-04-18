# tests/test_mcp.py
"""
Tests del servidor MCP (core/mcp/server.py).
No arranca stdio — testea _manejar_herramienta directamente
con un indice sintetico en core/state.
"""
import json
from pathlib import Path

import pytest

import core.state as state
from core.mcp.server import _manejar_herramienta
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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    state._reset()
    yield
    state._reset()


@pytest.fixture()
def indice_prueba():
    """Indice sintetico con una clase, un metodo, una funcion y un import."""
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _llamar(nombre, args=None):
    contents = await _manejar_herramienta(nombre, args or {})
    assert len(contents) == 1
    return contents[0].text


async def _json(nombre, args=None):
    return json.loads(await _llamar(nombre, args))


# ---------------------------------------------------------------------------
# Tests de estructura
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_codemap_carpetas(indice_prueba):
    resultado = await _json("codemap_carpetas")
    assert "src" in resultado


@pytest.mark.asyncio
async def test_codemap_clases_sin_filtro(indice_prueba):
    resultado = await _json("codemap_clases")
    assert "src/app.py" in resultado
    assert resultado["src/app.py"][0]["nombre"] == "Aplicacion"


@pytest.mark.asyncio
async def test_codemap_clases_con_archivo(indice_prueba):
    resultado = await _json("codemap_clases", {"archivo": "src/app.py"})
    assert "Aplicacion" in [c["nombre"] for c in resultado["src/app.py"]]


@pytest.mark.asyncio
async def test_codemap_metodos_encontrado(indice_prueba):
    resultado = await _json("codemap_metodos", {"clase": "Aplicacion"})
    assert resultado["clase"] == "Aplicacion"
    assert resultado["metodos"][0]["nombre"] == "iniciar"


@pytest.mark.asyncio
async def test_codemap_metodos_no_encontrado(indice_prueba):
    texto = await _llamar("codemap_metodos", {"clase": "NoExiste"})
    assert "no encontrada" in texto


@pytest.mark.asyncio
async def test_codemap_funciones(indice_prueba):
    resultado = await _json("codemap_funciones")
    assert resultado["src/app.py"][0]["nombre"] == "crear_app"


@pytest.mark.asyncio
async def test_codemap_imports(indice_prueba):
    resultado = await _json("codemap_imports")
    assert resultado["src/app.py"][0]["modulo"] == "os"


@pytest.mark.asyncio
async def test_codemap_variables_modulo(indice_prueba):
    resultado = await _json("codemap_variables", {"scope": "modulo"})
    nombres = [v["nombre"] for v in resultado["src/app.py"]]
    assert "VERSION" in nombres


@pytest.mark.asyncio
async def test_codemap_variables_clase(indice_prueba):
    resultado = await _json("codemap_variables", {"scope": "clase"})
    nombres_aplanados = [v["nombre"] for lista in resultado.values() for v in lista]
    assert any("nombre" in n for n in nombres_aplanados)


# ---------------------------------------------------------------------------
# Tests de relaciones
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_codemap_llamadas_encontrado(indice_prueba):
    resultado = await _json("codemap_llamadas", {"simbolo": "Aplicacion.iniciar"})
    assert "os.path.exists" in resultado["llamadas"]


@pytest.mark.asyncio
async def test_codemap_llamadas_no_encontrado(indice_prueba):
    texto = await _llamar("codemap_llamadas", {"simbolo": "NoExiste.metodo"})
    assert "no encontrado" in texto


@pytest.mark.asyncio
async def test_codemap_usos(indice_prueba):
    resultado = await _json("codemap_usos", {"nombre": "Aplicacion"})
    assert any(u["llamada"] == "Aplicacion" for u in resultado)


@pytest.mark.asyncio
async def test_codemap_libreria(indice_prueba):
    resultado = await _json("codemap_libreria", {"nombre": "os"})
    assert isinstance(resultado, list)


@pytest.mark.asyncio
async def test_codemap_buscar(indice_prueba):
    resultado = await _json("codemap_buscar", {"patron": "*app*"})
    nombres = [r["nombre"] for r in resultado]
    assert any("app" in n.lower() or "Aplicacion" in n for n in nombres)


@pytest.mark.asyncio
async def test_codemap_idioma(indice_prueba):
    resultado = await _json("codemap_idioma")
    assert "idioma_dominante" in resultado


# ---------------------------------------------------------------------------
# Tests de control
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_codemap_estado(indice_prueba):
    resultado = await _json("codemap_estado")
    assert resultado["total_archivos"] == 1
    assert resultado["total_clases"] == 1


@pytest.mark.asyncio
async def test_codemap_exportar_firmas(indice_prueba):
    texto = await _llamar("codemap_exportar", {"nivel": "firmas"})
    assert "Aplicacion" in texto
    assert "#" in texto  # es markdown


@pytest.mark.asyncio
async def test_codemap_exportar_estructura(indice_prueba):
    texto = await _llamar("codemap_exportar", {"nivel": "estructura"})
    assert len(texto) > 0


@pytest.mark.asyncio
async def test_codemap_herramienta_desconocida(indice_prueba):
    texto = await _llamar("codemap_xyz_no_existe")
    assert "desconocida" in texto