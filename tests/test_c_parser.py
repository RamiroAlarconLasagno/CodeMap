# tests/test_c_parser.py
"""Tests para core/analyzer/c_parser.py.

Fixture: sample.cpp — firmware embebido con clase base, clase derivada
con herencia y override, enum class, constructor con lista de inicializacion,
metodos virtuales, funciones libres y variables globales calificadas.
Representa codigo C++ real de proyectos Arduino/embedded.
"""

import pytest
from pathlib import Path
from core.analyzer.c_parser import parsear_archivo

FIXTURES = Path(__file__).parent / "fixtures"
RAIZ = FIXTURES


@pytest.fixture(scope="module")
def info():
    return parsear_archivo(FIXTURES / "sample.cpp", RAIZ, "cpp")


@pytest.fixture(scope="module")
def sensor_base(info):
    return next(c for c in info.clases if c.nombre == "SensorBase")


@pytest.fixture(scope="module")
def sensor_ade(info):
    return next(c for c in info.clases if c.nombre == "SensorADE9000")


# ---------------------------------------------------------------------------
# Metadatos
# ---------------------------------------------------------------------------

class TestMetadatos:
    def test_sin_error(self, info):
        assert info.error is None

    def test_lenguaje(self, info):
        assert info.lenguaje == "cpp"

    def test_nombre_archivo(self, info):
        assert info.nombre == "sample.cpp"


# ---------------------------------------------------------------------------
# Includes
# ---------------------------------------------------------------------------

class TestIncludes:
    def test_cantidad(self, info):
        assert len(info.imports) == 6

    def test_includes_sistema(self, info):
        modulos = {i.modulo for i in info.imports}
        assert {"Arduino.h", "Wire.h", "vector", "memory"} <= modulos

    def test_includes_locales(self, info):
        modulos = {i.modulo for i in info.imports}
        assert "SensorADE9000.h" in modulos
        assert "config.h" in modulos

    def test_no_es_from(self, info):
        for imp in info.imports:
            assert imp.es_from is False


# ---------------------------------------------------------------------------
# Defines
# ---------------------------------------------------------------------------

class TestDefines:
    @pytest.fixture(autouse=True)
    def defines(self, info):
        self.d = {v.nombre: v for v in info.variables if v.tipo == "#define"}

    def test_define_entero(self):
        assert "HW_VERSION" in self.d
        assert self.d["HW_VERSION"].valor_inicial == "3"

    def test_define_buffer(self):
        assert "MAX_LECTURAS" in self.d
        assert self.d["MAX_LECTURAS"].valor_inicial == "512"

    def test_define_string(self):
        assert "ID_DISPOSITIVO" in self.d
        assert self.d["ID_DISPOSITIVO"].valor_inicial is not None

    def test_tipo_es_define(self):
        for d in self.d.values():
            assert d.tipo == "#define"

    def test_scope_modulo(self):
        for d in self.d.values():
            assert d.scope == "modulo"


# ---------------------------------------------------------------------------
# Clases — enum class, clase base, clase derivada
# ---------------------------------------------------------------------------

class TestClases:
    def test_cantidad(self, info):
        assert len(info.clases) == 3

    def test_nombres(self, info):
        nombres = {c.nombre for c in info.clases}
        assert {"EstadoSensor", "SensorBase", "SensorADE9000"} == nombres

    def test_SensorBase_sin_herencia(self, sensor_base):
        assert sensor_base.clases_base == []

    def test_SensorADE9000_hereda_SensorBase(self, sensor_ade):
        assert "SensorBase" in sensor_ade.clases_base


# ---------------------------------------------------------------------------
# Atributos
# ---------------------------------------------------------------------------

class TestAtributos:
    def test_atributos_SensorBase(self, sensor_base):
        nombres = {a.nombre for a in sensor_base.atributos}
        assert {"id", "ultimo_valor", "habilitado"} <= nombres

    def test_tipos_SensorBase(self, sensor_base):
        tipos = {a.nombre: a.tipo for a in sensor_base.atributos}
        assert tipos["id"] == "String"
        assert tipos["ultimo_valor"] == "float"
        assert tipos["habilitado"] == "bool"

    def test_atributos_SensorADE9000(self, sensor_ade):
        nombres = {a.nombre for a in sensor_ade.atributos}
        assert "canal" in nombres
        assert "factor_calibracion" in nombres

    def test_atributo_template(self, sensor_ade):
        # std::vector<float> _buffer
        nombres = {a.nombre for a in sensor_ade.atributos}
        assert "_buffer" in nombres

    def test_scope_clase(self, sensor_base):
        for a in sensor_base.atributos:
            assert a.scope == "clase"


# ---------------------------------------------------------------------------
# Metodos — constructor, virtuales, override, static
# ---------------------------------------------------------------------------

class TestMetodosSensorBase:
    @pytest.fixture(autouse=True)
    def metodos(self, sensor_base):
        self.m = {m.nombre: m for m in sensor_base.metodos}

    def test_constructor_detectado(self):
        assert "SensorBase" in self.m

    def test_constructor_es_primero(self, sensor_base):
        assert sensor_base.metodos[0].nombre == "SensorBase"

    def test_metodos_detectados(self):
        assert {"leer", "calibrar", "estaActivo", "contarInstancias"} <= set(self.m)

    def test_constructor_llama_inicializar(self):
        llamadas = [l.nombre for l in self.m["SensorBase"].llamadas]
        assert "_inicializar" in llamadas

    def test_inicializar_llama_Wire_begin(self):
        llamadas = [l.nombre for l in self.m["_inicializar"].llamadas]
        assert "begin" in llamadas

    def test_constructor_no_confunde_nombre(self, sensor_base):
        # Critico: SensorBase NO debe generar metodo 'Base' ni 'ase'
        nombres = [m.nombre for m in sensor_base.metodos]
        assert "Base" not in nombres
        assert "ase" not in nombres


class TestMetodosSensorADE9000:
    @pytest.fixture(autouse=True)
    def metodos(self, sensor_ade):
        self.m = {m.nombre: m for m in sensor_ade.metodos}

    def test_constructor_detectado(self):
        assert "SensorADE9000" in self.m

    def test_metodos_detectados(self):
        assert {"leer", "calibrar", "leerLote"} <= set(self.m)

    def test_constructor_llama_reserve(self):
        llamadas = [l.nombre for l in self.m["SensorADE9000"].llamadas]
        assert "reserve" in llamadas

    def test_leer_override_llama_leerADC(self):
        llamadas = [l.nombre for l in self.m["leer"].llamadas]
        assert "_leerADC" in llamadas

    def test_leerLote_llama_leer(self):
        llamadas = [l.nombre for l in self.m["leerLote"].llamadas]
        assert "leer" in llamadas

    def test_constructor_no_confunde_regex(self, sensor_ade):
        # SensorADE9000 no debe generar metodo 'E9000' ni '9000'
        nombres = [m.nombre for m in sensor_ade.metodos]
        assert "E9000" not in nombres
        assert "9000" not in nombres


# ---------------------------------------------------------------------------
# Funciones sueltas de modulo
# ---------------------------------------------------------------------------

class TestFunciones:
    @pytest.fixture(autouse=True)
    def funciones(self, info):
        self.f = {f.nombre: f for f in info.funciones}

    def test_nombres_detectados(self):
        assert {"calcularPromedio", "calcularRMS", "setup", "loop"} <= set(self.f)

    def test_calcularPromedio_llama_size(self):
        llamadas = [l.nombre for l in self.f["calcularPromedio"].llamadas]
        assert "size" in llamadas

    def test_setup_llama_begin(self):
        llamadas = [l.nombre for l in self.f["setup"].llamadas]
        assert "begin" in llamadas

    def test_loop_llama_delay(self):
        llamadas = [l.nombre for l in self.f["loop"].llamadas]
        assert "delay" in llamadas

    def test_clases_no_son_funciones(self):
        assert "SensorBase" not in self.f
        assert "SensorADE9000" not in self.f


# ---------------------------------------------------------------------------
# Variables globales
# ---------------------------------------------------------------------------

class TestVariables:
    @pytest.fixture(autouse=True)
    def variables(self, info):
        self.v = {v.nombre: v for v in info.variables if v.tipo != "#define"}

    def test_PIN_ALERTA(self):
        assert "PIN_ALERTA" in self.v
        assert self.v["PIN_ALERTA"].valor_inicial == "4"

    def test_FACTOR_ESCALA(self):
        assert "FACTOR_ESCALA" in self.v

    def test_total_instancias(self):
        assert "total_instancias" in self.v
        assert self.v["total_instancias"].valor_inicial == "0"

    def test_scope_modulo(self):
        for v in self.v.values():
            assert v.scope == "modulo"


# ---------------------------------------------------------------------------
# Archivo inexistente
# ---------------------------------------------------------------------------

class TestArchivoInexistente:
    def test_error_registrado(self):
        info = parsear_archivo(FIXTURES / "no_existe.cpp", RAIZ, "cpp")
        assert info.error is not None

    def test_listas_vacias_en_error(self):
        info = parsear_archivo(FIXTURES / "no_existe.cpp", RAIZ, "cpp")
        assert info.imports == []
        assert info.clases == []
        assert info.funciones == []
        assert info.variables == []