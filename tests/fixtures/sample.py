# tests/fixtures/sample.py
"""Modulo de prueba para los tests de CodeMap."""

import os
import sys
from pathlib import Path
from typing import Optional, List

CONSTANTE_MODULO: str = "hola"
VERSION = "1.0.0"
DEBUG: bool = False


def funcion_simple(x: int, y: int) -> int:
    """Suma dos numeros."""
    return x + y


def funcion_sin_tipo(nombre, valor=None):
    resultado = str(nombre)
    return resultado


async def funcion_asincrona(url: str) -> dict:
    """Descarga datos de una URL."""
    datos = {}
    return datos


class ClaseBase:
    """Clase base de prueba."""

    atributo_clase: str = "base"

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.activo: bool = True

    def metodo_simple(self) -> str:
        """Devuelve el nombre."""
        return self.nombre

    @property
    def nombre_upper(self) -> str:
        return self.nombre.upper()

    @staticmethod
    def metodo_estatico(x: int) -> int:
        return x * 2

    @classmethod
    def desde_dict(cls, datos: dict) -> "ClaseBase":
        return cls(datos["nombre"])


class ClaseHija(ClaseBase):
    """Clase hija que hereda de ClaseBase."""

    def __init__(self, nombre: str, nivel: int = 0):
        super().__init__(nombre)
        self.nivel = nivel
        self._privado: Optional[str] = None

    def metodo_override(self) -> str:
        resultado = self.metodo_simple()
        return f"{resultado} (nivel {self.nivel})"

    async def metodo_async(self, items: List[str]) -> List[str]:
        """Procesa items de forma asincrona."""
        procesados = []
        for item in items:
            procesados.append(item.strip())
        return procesados


class ClaseMultipleHerencia(ClaseBase, dict):
    """Clase con herencia multiple."""

    def __init__(self):
        ClaseBase.__init__(self, "multi")
        dict.__init__(self)