# tests/conftest.py

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


@pytest.fixture
def indice() -> ProjectIndex:
    """Indice de prueba con dos archivos, clases, metodos, funciones y variables."""

    # --- archivo a.py ---
    metodo_conectar = MetodoInfo(
        nombre="conectar",
        firma="conectar(self, host: str, puerto: int) -> bool",
        docstring="Establece la conexion.",
        decoradores=[],
        es_async=False,
        llamadas=[LlamadaInfo("socket.connect"), LlamadaInfo("logger.info")],
        linea=15,
    )
    metodo_enviar = MetodoInfo(
        nombre="enviar",
        firma="enviar(self, datos: bytes) -> None",
        docstring="Envia datos por el socket.",
        decoradores=[],
        es_async=True,
        llamadas=[LlamadaInfo("socket.send"), LlamadaInfo("logger.debug")],
        linea=28,
    )
    clase_cliente = ClaseInfo(
        nombre="ClienteMQTT",
        firma="ClienteMQTT(host: str, puerto: int = 1883)",
        docstring="Cliente MQTT minimalista.",
        clases_base=["BaseCliente"],
        metodos=[metodo_conectar, metodo_enviar],
        atributos=[
            VariableInfo("host", "str", None, "clase", 10),
            VariableInfo("puerto", "int", "1883", "clase", 11),
        ],
        linea=8,
    )

    archivo_a = ArchivoInfo(
        ruta_relativa="red/cliente.py",
        carpeta="red",
        nombre="cliente.py",
        lenguaje="python",
        clases=[clase_cliente],
        funciones=[
            FuncionInfo(
                nombre="crear_cliente",
                firma="crear_cliente(host: str) -> ClienteMQTT",
                docstring="Fabrica de clientes.",
                llamadas=[LlamadaInfo("ClienteMQTT"), LlamadaInfo("logger.info")],
                linea=50,
            )
        ],
        variables=[
            VariableInfo("TIMEOUT", "int", "30", "modulo", 3),
            VariableInfo("VERSION", "str", '"1.0"', "modulo", 4),
        ],
        imports=[
            ImportInfo("socket", [], False),
            ImportInfo("logging", ["getLogger"], True),
        ],
    )

    # --- archivo b.py ---
    metodo_procesar = MetodoInfo(
        nombre="procesar",
        firma="procesar(self, mensaje: str) -> dict",
        docstring="Parsea el mensaje.",
        llamadas=[LlamadaInfo("json.loads"), LlamadaInfo("logger.info")],
        linea=20,
    )
    clase_parser = ClaseInfo(
        nombre="Parser",
        firma="Parser(strict: bool = True)",
        docstring="Parsea mensajes MQTT.",
        clases_base=[],
        metodos=[metodo_procesar],
        atributos=[VariableInfo("strict", "bool", "True", "clase", 15)],
        linea=12,
    )

    archivo_b = ArchivoInfo(
        ruta_relativa="util/parser.py",
        carpeta="util",
        nombre="parser.py",
        lenguaje="python",
        clases=[clase_parser],
        funciones=[],
        variables=[],
        imports=[ImportInfo("json", [], False)],
        error=None,
    )

    # --- archivo con error ---
    archivo_err = ArchivoInfo(
        ruta_relativa="util/roto.py",
        carpeta="util",
        nombre="roto.py",
        lenguaje="python",
        error="SyntaxError en linea 7",
    )

    idx = ProjectIndex(
        carpeta_raiz=Path("/proyecto"),
        archivos={
            "red/cliente.py": archivo_a,
            "util/parser.py": archivo_b,
            "util/roto.py": archivo_err,
        },
        ultimo_analisis=datetime(2024, 6, 1, 10, 0, 0),
    )
    return idx