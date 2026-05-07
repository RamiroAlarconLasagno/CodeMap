# core/mcp/server.py
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from core.analyzer import construir_indice, reanalizar
from core.filters import f_buscar, f_idioma, f_libreria
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
from core.state import get_indice, set_indice
from shared.formatters import exportar_md

# ---------------------------------------------------------------------------
# Definicion de las 14 herramientas
# ---------------------------------------------------------------------------

_HERRAMIENTAS: list[Tool] = [
    Tool(
        name="codemap_carpetas",
        description="Arbol de carpetas del proyecto con sus archivos analizados.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="codemap_clases",
        description="Lista de clases del proyecto. Opcionalmente filtra por archivo.",
        inputSchema={
            "type": "object",
            "properties": {
                "archivo": {"type": "string", "description": "Ruta relativa del archivo (opcional)"}
            },
        },
    ),
    Tool(
        name="codemap_metodos",
        description="Metodos de una clase especifica por nombre exacto.",
        inputSchema={
            "type": "object",
            "properties": {
                "clase": {"type": "string", "description": "Nombre exacto de la clase"}
            },
            "required": ["clase"],
        },
    ),
    Tool(
        name="codemap_funciones",
        description="Funciones sueltas del proyecto. Opcionalmente filtra por archivo.",
        inputSchema={
            "type": "object",
            "properties": {
                "archivo": {"type": "string", "description": "Ruta relativa del archivo (opcional)"}
            },
        },
    ),
    Tool(
        name="codemap_imports",
        description="Imports por archivo. Sin archivo devuelve todos.",
        inputSchema={
            "type": "object",
            "properties": {
                "archivo": {"type": "string", "description": "Ruta relativa del archivo (opcional)"}
            },
        },
    ),
    Tool(
        name="codemap_variables",
        description="Variables de modulo o de clase. scope: 'modulo'|'clase'|null.",
        inputSchema={
            "type": "object",
            "properties": {
                "archivo": {"type": "string", "description": "Ruta relativa (opcional)"},
                "scope": {"type": "string", "enum": ["modulo", "clase"], "description": "Scope (opcional)"},
            },
        },
    ),
    Tool(
        name="codemap_llamadas",
        description="Llamadas internas de un metodo o funcion. simbolo: 'Clase.metodo' o 'funcion'.",
        inputSchema={
            "type": "object",
            "properties": {
                "simbolo": {"type": "string", "description": "Nombre del simbolo"}
            },
            "required": ["simbolo"],
        },
    ),
    Tool(
        name="codemap_usos",
        description="Donde aparece un simbolo como llamada en el proyecto (busqueda parcial).",
        inputSchema={
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre o fragmento a buscar"}
            },
            "required": ["nombre"],
        },
    ),
    Tool(
        name="codemap_libreria",
        description="Archivos, funciones y metodos que usan una libreria especifica.",
        inputSchema={
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre de la libreria"}
            },
            "required": ["nombre"],
        },
    ),
    Tool(
        name="codemap_buscar",
        description="Busca clases, metodos y funciones por nombre. Soporta wildcards * y ?.",
        inputSchema={
            "type": "object",
            "properties": {
                "patron": {"type": "string", "description": "Patron de busqueda (soporta * y ?)"}
            },
            "required": ["patron"],
        },
    ),
    Tool(
        name="codemap_idioma",
        description="Detecta mezcla de idiomas (es/en) en nombres de funciones y clases.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="codemap_estado",
        description="Totales del indice: archivos, clases, metodos, funciones, variables y errores.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="codemap_reanalizar",
        description="Reconstruye el indice analizando de nuevo la carpeta del proyecto.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="codemap_exportar",
        description="Exporta el indice como Markdown. nivel: 'estructura'|'firmas'|'completo'.",
        inputSchema={
            "type": "object",
            "properties": {
                "nivel": {
                    "type": "string",
                    "enum": ["estructura", "firmas", "completo"],
                    "description": "Nivel de detalle (default: firmas)",
                }
            },
        },
    ),
]


# ---------------------------------------------------------------------------
# Handler de herramientas
# ---------------------------------------------------------------------------

async def _manejar_herramienta(nombre: str, args: dict) -> list[TextContent]:
    """Despacha la herramienta MCP a la funcion correspondiente."""
    indice = get_indice()

    if nombre == "codemap_carpetas":
        resultado = q_carpetas(indice)

    elif nombre == "codemap_clases":
        resultado = q_clases(indice, args.get("archivo"))

    elif nombre == "codemap_metodos":
        resultado = q_metodos(indice, args["clase"])
        if resultado is None:
            return [TextContent(type="text", text=f"Clase '{args['clase']}' no encontrada.")]

    elif nombre == "codemap_funciones":
        resultado = q_funciones(indice, args.get("archivo"))

    elif nombre == "codemap_imports":
        resultado = q_imports(indice, args.get("archivo"))

    elif nombre == "codemap_variables":
        resultado = q_variables(indice, args.get("archivo"), args.get("scope"))

    elif nombre == "codemap_llamadas":
        resultado = q_llamadas(indice, args["simbolo"])
        if resultado is None:
            return [TextContent(type="text", text=f"Simbolo '{args['simbolo']}' no encontrado.")]

    elif nombre == "codemap_usos":
        resultado = q_usos(indice, args["nombre"])

    elif nombre == "codemap_libreria":
        resultado = f_libreria(indice, args["nombre"])

    elif nombre == "codemap_buscar":
        resultado = f_buscar(indice, args["patron"])

    elif nombre == "codemap_idioma":
        resultado = f_idioma(indice)

    elif nombre == "codemap_estado":
        resultado = q_estado(indice)

    elif nombre == "codemap_reanalizar":
        set_indice(reanalizar(indice))
        resultado = q_estado(get_indice())

    elif nombre == "codemap_exportar":
        nivel = args.get("nivel", "firmas")
        texto = exportar_md(indice, nivel)
        return [TextContent(type="text", text=texto)]

    else:
        return [TextContent(type="text", text=f"Herramienta desconocida: {nombre}")]

    return [TextContent(type="text", text=json.dumps(resultado, ensure_ascii=False, indent=2))]


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

async def iniciar_servidor(carpeta: Path) -> None:
    """Construye el indice y arranca el servidor MCP por stdio."""
    set_indice(construir_indice(carpeta))

    server = Server("codemap")

    @server.list_tools()
    async def listar_herramientas():
        return _HERRAMIENTAS

    @server.call_tool()
    async def llamar_herramienta(nombre: str, arguments: dict):
        return await _manejar_herramienta(nombre, arguments or {})

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())