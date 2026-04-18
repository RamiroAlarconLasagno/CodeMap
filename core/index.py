# core/index.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class LlamadaInfo:
    nombre: str


@dataclass
class VariableInfo:
    nombre: str
    tipo: Optional[str]
    valor_inicial: Optional[str]
    scope: str          # 'modulo' | 'clase'
    linea: int


@dataclass
class MetodoInfo:
    nombre: str
    firma: str
    docstring: str
    decoradores: list[str] = field(default_factory=list)
    es_async: bool = False
    llamadas: list[LlamadaInfo] = field(default_factory=list)
    linea: int = 0


@dataclass
class ClaseInfo:
    nombre: str
    firma: str
    docstring: str
    clases_base: list[str] = field(default_factory=list)
    metodos: list[MetodoInfo] = field(default_factory=list)
    atributos: list[VariableInfo] = field(default_factory=list)
    linea: int = 0


@dataclass
class FuncionInfo:
    nombre: str
    firma: str
    docstring: str
    decoradores: list[str] = field(default_factory=list)
    es_async: bool = False
    llamadas: list[LlamadaInfo] = field(default_factory=list)
    linea: int = 0


@dataclass
class ImportInfo:
    modulo: str
    nombres: list[str] = field(default_factory=list)
    es_from: bool = False


@dataclass
class ArchivoInfo:
    ruta_relativa: str
    carpeta: str
    nombre: str
    lenguaje: str       # 'python' | 'dart' | 'js' | 'ts' | 'c' | 'cpp'
    clases: list[ClaseInfo] = field(default_factory=list)
    funciones: list[FuncionInfo] = field(default_factory=list)
    variables: list[VariableInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ProjectIndex:
    carpeta_raiz: Path
    archivos: dict[str, ArchivoInfo] = field(default_factory=dict)
    ultimo_analisis: Optional[datetime] = None

    def esta_vacio(self) -> bool:
        return len(self.archivos) == 0

    def total_archivos(self) -> int:
        return len(self.archivos)

    def total_clases(self) -> int:
        return sum(len(a.clases) for a in self.archivos.values())

    def total_funciones(self) -> int:
        return sum(len(a.funciones) for a in self.archivos.values())

    def total_metodos(self) -> int:
        return sum(
            len(c.metodos)
            for a in self.archivos.values()
            for c in a.clases
        )

    def total_variables(self) -> int:
        return sum(len(a.variables) for a in self.archivos.values())