# tests/test_js_parser.py
"""Tests para core/analyzer/js_parser.py.

Fixture: sample.js — proyecto React/Node con dos clases, herencia,
private fields (#), getters, metodos async, mixed imports, arrow functions
y variables de modulo. Representa codigo real que uno encuentra en produccion.
"""

import pytest
from pathlib import Path
from core.analyzer.js_parser import parsear_archivo

FIXTURES = Path(__file__).parent / "fixtures"
RAIZ = FIXTURES


@pytest.fixture(scope="module")
def info():
    return parsear_archivo(FIXTURES / "sample.js", RAIZ, "js")


@pytest.fixture(scope="module")
def cliente(info):
    return next(c for c in info.clases if c.nombre == "ApiClient")


@pytest.fixture(scope="module")
def cliente_auth(info):
    return next(c for c in info.clases if c.nombre == "ApiClientAutenticado")


# ---------------------------------------------------------------------------
# Metadatos
# ---------------------------------------------------------------------------

class TestMetadatos:
    def test_sin_error(self, info):
        assert info.error is None

    def test_lenguaje(self, info):
        assert info.lenguaje == "js"

    def test_nombre_archivo(self, info):
        assert info.nombre == "sample.js"


# ---------------------------------------------------------------------------
# Imports — named, default, mixed, bare, type
# ---------------------------------------------------------------------------

class TestImports:
    def test_cantidad(self, info):
        assert len(info.imports) == 4

    def test_import_named_react(self, info):
        react = next(i for i in info.imports if i.modulo == "react")
        assert react.es_from is True
        assert "useState" in react.nombres
        assert "useCallback" in react.nombres
        assert "useRef" in react.nombres

    def test_import_mixed_default_y_named(self, info):
        # import axios, { AxiosError } from 'axios'
        ax = next(i for i in info.imports if i.modulo == "axios")
        assert ax is not None

    def test_import_type(self, info):
        # import type { ... } from './types.js'
        modulos = [i.modulo for i in info.imports]
        assert "./types.js" in modulos

    def test_import_bare(self, info):
        bare = next(i for i in info.imports if i.modulo == "reflect-metadata")
        assert bare.es_from is False
        assert bare.nombres == []


# ---------------------------------------------------------------------------
# Clases — dos clases, herencia, private fields
# ---------------------------------------------------------------------------

class TestClases:
    def test_cantidad(self, info):
        assert len(info.clases) == 2

    def test_nombres(self, info):
        nombres = {c.nombre for c in info.clases}
        assert {"ApiClient", "ApiClientAutenticado"} == nombres

    def test_ApiClient_sin_herencia(self, cliente):
        assert cliente.clases_base == []

    def test_ApiClientAutenticado_hereda_de_ApiClient(self, cliente_auth):
        assert "ApiClient" in cliente_auth.clases_base

    def test_firma_herencia(self, cliente_auth):
        assert "extends" in cliente_auth.firma


# ---------------------------------------------------------------------------
# Metodos de ApiClient
# ---------------------------------------------------------------------------

class TestMetodosApiClient:
    @pytest.fixture(autouse=True)
    def metodos(self, cliente):
        self.m = {m.nombre: m for m in cliente.metodos}

    def test_metodos_detectados(self):
        assert {"constructor", "getInstance", "baseUrl", "get", "post", "agregarInterceptor"} \
               <= set(self.m)

    def test_constructor_es_primero(self, cliente):
        assert cliente.metodos[0].nombre == "constructor"

    def test_get_es_async(self):
        assert self.m["get"].es_async is True

    def test_post_es_async(self):
        assert self.m["post"].es_async is True

    def test_getInstance_no_es_async(self):
        assert self.m["getInstance"].es_async is False

    def test_getter_detectado(self):
        # get baseUrl() { return this.#baseUrl; }
        assert "baseUrl" in self.m

    def test_get_llama_construirUrl(self):
        llamadas = [l.nombre for l in self.m["get"].llamadas]
        assert "construirUrl" in llamadas

    def test_post_llama_construirUrl(self):
        llamadas = [l.nombre for l in self.m["post"].llamadas]
        assert "construirUrl" in llamadas


# ---------------------------------------------------------------------------
# Metodos de ApiClientAutenticado
# ---------------------------------------------------------------------------

class TestMetodosApiClientAutenticado:
    @pytest.fixture(autouse=True)
    def metodos(self, cliente_auth):
        self.m = {m.nombre: m for m in cliente_auth.metodos}

    def test_metodos_detectados(self):
        assert {"constructor", "get"} <= set(self.m)

    def test_get_override_es_async(self):
        assert self.m["get"].es_async is True


# ---------------------------------------------------------------------------
# Atributos de clase
# ---------------------------------------------------------------------------

class TestAtributos:
    def test_atributos_ApiClient(self, cliente):
        nombres = {a.nombre for a in cliente.atributos}
        # timeout, headers detectados como atributos JS planos
        assert "timeout" in nombres
        assert "headers" in nombres

    def test_no_duplicados(self, cliente):
        nombres = [a.nombre for a in cliente.atributos]
        assert len(nombres) == len(set(nombres))

    def test_scope_clase(self, cliente):
        for a in cliente.atributos:
            assert a.scope == "clase"


# ---------------------------------------------------------------------------
# Funciones sueltas — named, arrow, async
# ---------------------------------------------------------------------------

class TestFunciones:
    @pytest.fixture(autouse=True)
    def funciones(self, info):
        self.f = {f.nombre: f for f in info.funciones}

    def test_nombres_detectados(self):
        assert {"construirUrl", "normalizar", "useApiClient", "manejarError"} \
               <= set(self.f)

    def test_construirUrl_no_es_async(self):
        assert self.f["construirUrl"].es_async is False

    def test_useApiClient_es_arrow(self):
        # const useApiClient = (config) => { ... }
        assert "useApiClient" in self.f

    def test_manejarError_es_arrow(self):
        assert "manejarError" in self.f

    def test_clases_no_son_funciones(self):
        assert "ApiClient" not in self.f
        assert "ApiClientAutenticado" not in self.f


# ---------------------------------------------------------------------------
# Variables de modulo
# ---------------------------------------------------------------------------

class TestVariables:
    @pytest.fixture(autouse=True)
    def variables(self, info):
        self.v = {v.nombre: v for v in info.variables}

    def test_nombres_detectados(self):
        assert {"TIMEOUT_MS", "_instancia", "_modo_debug"} <= set(self.v)

    def test_timeout_valor(self):
        assert self.v["TIMEOUT_MS"].valor_inicial == "8000"

    def test_instancia_null(self):
        assert self.v["_instancia"].valor_inicial == "null"

    def test_modo_debug_false(self):
        assert self.v["_modo_debug"].valor_inicial == "false"

    def test_scope_modulo(self):
        for v in self.v.values():
            assert v.scope == "modulo"

    def test_funciones_no_son_variables(self):
        assert "construirUrl" not in self.v
        assert "useApiClient" not in self.v
        assert "manejarError" not in self.v

    def test_clases_no_son_variables(self):
        assert "ApiClient" not in self.v


# ---------------------------------------------------------------------------
# Archivo inexistente
# ---------------------------------------------------------------------------

class TestArchivoInexistente:
    def test_error_registrado(self):
        info = parsear_archivo(FIXTURES / "no_existe.js", RAIZ, "js")
        assert info.error is not None

    def test_listas_vacias_en_error(self):
        info = parsear_archivo(FIXTURES / "no_existe.js", RAIZ, "js")
        assert info.imports == []
        assert info.clases == []
        assert info.funciones == []
        assert info.variables == []