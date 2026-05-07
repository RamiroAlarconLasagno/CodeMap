# core/filters.py

from __future__ import annotations

import fnmatch
import re
from typing import Optional

from core.index import ProjectIndex

# ---------------------------------------------------------------------------
# Palabras clave por idioma para heuristica de f_idioma
# ---------------------------------------------------------------------------

_PALABRAS_ES = frozenset({
    "obtener", "establecer", "crear", "eliminar", "actualizar", "buscar",
    "conectar", "desconectar", "iniciar", "detener", "pausar", "reanudar",
    "cargar", "guardar", "enviar", "recibir", "procesar", "validar",
    "calcular", "mostrar", "ocultar", "abrir", "cerrar", "leer", "escribir",
    "agregar", "quitar", "limpiar", "reiniciar", "verificar", "comprobar",
    "convertir", "parsear", "formatear", "imprimir", "registrar", "manejar",
    "cliente", "servidor", "archivo", "carpeta", "indice", "lista", "tabla",
    "usuario", "contrasena", "nombre", "valor", "tipo", "estado", "error",
    "mensaje", "datos", "resultado", "respuesta", "solicitud", "conexion",
    "configuracion", "parametro", "opcion", "modo", "nivel", "limite",
    "tiempo", "fecha", "hora", "numero", "texto", "cadena", "clave",
})

_PALABRAS_EN = frozenset({
    "get", "set", "create", "delete", "update", "search", "find",
    "connect", "disconnect", "start", "stop", "pause", "resume",
    "load", "save", "send", "receive", "process", "validate",
    "calculate", "show", "hide", "open", "close", "read", "write",
    "add", "remove", "clear", "reset", "check", "verify",
    "convert", "parse", "format", "print", "log", "handle",
    "client", "server", "file", "folder", "index", "list", "table",
    "user", "password", "name", "value", "type", "status", "error",
    "message", "data", "result", "response", "request", "connection",
    "config", "param", "option", "mode", "level", "limit",
    "time", "date", "number", "text", "string", "key", "manager",
    "handler", "builder", "factory", "parser", "reader", "writer",
})


def f_libreria(indice: ProjectIndex, nombre_lib: str) -> list[dict]:
    """Archivos/funciones/metodos que usan una libreria.
    Busca en imports Y en llamadas simultaneamente.
    """
    nombre_lower = nombre_lib.lower()
    resultados = []

    for ruta, info in indice.archivos.items():
        # Verificar si el archivo importa la libreria
        importa = any(
            nombre_lower in imp.modulo.lower()
            for imp in info.imports
        )

        if importa:
            resultados.append({
                "archivo": ruta,
                "tipo": "import",
                "simbolo": None,
                "detalle": next(
                    imp.modulo for imp in info.imports
                    if nombre_lower in imp.modulo.lower()
                ),
            })

        # Buscar en llamadas de metodos
        for clase in info.clases:
            for metodo in clase.metodos:
                llamadas_match = [
                    l.nombre for l in metodo.llamadas
                    if nombre_lower in l.nombre.lower()
                ]
                if llamadas_match:
                    resultados.append({
                        "archivo": ruta,
                        "tipo": "llamada",
                        "simbolo": f"{clase.nombre}.{metodo.nombre}",
                        "detalle": llamadas_match,
                    })

        # Buscar en llamadas de funciones sueltas
        for funcion in info.funciones:
            llamadas_match = [
                l.nombre for l in funcion.llamadas
                if nombre_lower in l.nombre.lower()
            ]
            if llamadas_match:
                resultados.append({
                    "archivo": ruta,
                    "tipo": "llamada",
                    "simbolo": funcion.nombre,
                    "detalle": llamadas_match,
                })

    return resultados


def f_buscar(indice: ProjectIndex, patron: str) -> list[dict]:
    """Busca clases, metodos y funciones por nombre (categoria='definicion')
    y tambien los simbolos que los invocan (categoria='uso').
    Soporta wildcards * y ?. Sin wildcards: busqueda de subcadena.
    """
    tiene_wildcards = "*" in patron or "?" in patron
    resultados = []

    def coincide(nombre: str) -> bool:
        if tiene_wildcards:
            return fnmatch.fnmatch(nombre.lower(), patron.lower())
        return patron.lower() in nombre.lower()

    for ruta, info in indice.archivos.items():
        # --- Definiciones ---
        for clase in info.clases:
            if coincide(clase.nombre):
                resultados.append({
                    "archivo": ruta,
                    "tipo": "clase",
                    "nombre": clase.nombre,
                    "firma": clase.firma,
                    "linea": clase.linea,
                    "categoria": "definicion",
                })
            for metodo in clase.metodos:
                if coincide(metodo.nombre):
                    resultados.append({
                        "archivo": ruta,
                        "tipo": "metodo",
                        "nombre": f"{clase.nombre}.{metodo.nombre}",
                        "firma": metodo.firma,
                        "linea": metodo.linea,
                        "categoria": "definicion",
                    })

        for funcion in info.funciones:
            if coincide(funcion.nombre):
                resultados.append({
                    "archivo": ruta,
                    "tipo": "funcion",
                    "nombre": funcion.nombre,
                    "firma": funcion.firma,
                    "linea": funcion.linea,
                    "categoria": "definicion",
                })

        # --- Usos: simbolos que invocan algo que coincide con el patron ---
        for clase in info.clases:
            for metodo in clase.metodos:
                match = [l.nombre for l in metodo.llamadas if coincide(l.nombre)]
                if match:
                    resultados.append({
                        "archivo": ruta,
                        "tipo": "metodo",
                        "nombre": f"{clase.nombre}.{metodo.nombre}",
                        "firma": metodo.firma,
                        "linea": metodo.linea,
                        "categoria": "uso",
                        "llama_a": match,
                    })

        for funcion in info.funciones:
            match = [l.nombre for l in funcion.llamadas if coincide(l.nombre)]
            if match:
                resultados.append({
                    "archivo": ruta,
                    "tipo": "funcion",
                    "nombre": funcion.nombre,
                    "firma": funcion.firma,
                    "linea": funcion.linea,
                    "categoria": "uso",
                    "llama_a": match,
                })

    return resultados


def f_idioma(indice: ProjectIndex) -> dict:
    """Detecta mezcla de idiomas en nombres de funciones y clases.
    Heuristica por tokens snake_case y CamelCase contra diccionarios es/en.
    """
    conteo_es = 0
    conteo_en = 0
    archivos_con_mezcla: list[str] = []

    for ruta, info in indice.archivos.items():
        es_archivo = 0
        en_archivo = 0

        nombres = []
        nombres += [c.nombre for c in info.clases]
        nombres += [m.nombre for c in info.clases for m in c.metodos]
        nombres += [f.nombre for f in info.funciones]

        for nombre in nombres:
            tokens = _tokenizar(nombre)
            for token in tokens:
                if token in _PALABRAS_ES:
                    es_archivo += 1
                elif token in _PALABRAS_EN:
                    en_archivo += 1

        conteo_es += es_archivo
        conteo_en += en_archivo

        if es_archivo > 0 and en_archivo > 0:
            archivos_con_mezcla.append(ruta)

    total = conteo_es + conteo_en
    if total == 0:
        idioma_dominante = "indeterminado"
    elif conteo_es >= conteo_en:
        idioma_dominante = "es"
    else:
        idioma_dominante = "en"

    return {
        "idioma_dominante": idioma_dominante,
        "conteo_es": conteo_es,
        "conteo_en": conteo_en,
        "archivos_con_mezcla": archivos_con_mezcla,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _tokenizar(nombre: str) -> list[str]:
    """Convierte CamelCase y snake_case en lista de tokens en minusculas."""
    # Separar CamelCase
    nombre_separado = re.sub(r"([A-Z])", r"_\1", nombre).lower()
    # Separar por guiones bajos y filtrar vacios
    tokens = [t for t in nombre_separado.split("_") if t]
    return tokens