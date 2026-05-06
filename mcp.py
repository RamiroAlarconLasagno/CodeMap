# mcp.py
"""Punto de entrada headless de CodeMap para Claude Desktop via MCP stdio.

Uso:
    python mcp.py --carpeta /ruta/del/proyecto

Configuracion claude_desktop_config.json:
    {
        "mcpServers": {
            "codemap": {
                "command": "python",
                "args": [
                    "/ruta/absoluta/CodeMap/mcp.py",
                    "--carpeta",
                    "/ruta/del/proyecto"
                ]
            }
        }
    }
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _parsear_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CodeMap — Servidor MCP para Claude Desktop"
    )
    parser.add_argument(
        "--carpeta",
        type=Path,
        required=True,
        help="Carpeta del proyecto a analizar (requerido)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parsear_args()
    carpeta = args.carpeta.resolve()

    if not carpeta.exists():
        print(f"Error: la carpeta '{carpeta}' no existe.", file=sys.stderr)
        sys.exit(1)

    if not carpeta.is_dir():
        print(f"Error: '{carpeta}' no es una carpeta.", file=sys.stderr)
        sys.exit(1)

    from core.mcp.server import iniciar_servidor
    asyncio.run(iniciar_servidor(carpeta))


if __name__ == "__main__":
    main()
