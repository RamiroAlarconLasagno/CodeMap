# main.py

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _parsear_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CodeMap — Analizador interactivo de codigo para LLMs"
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument(
        "--web",
        action="store_true",
        help="Iniciar interfaz web en localhost:8000",
    )
    grupo.add_argument(
        "--mcp",
        action="store_true",
        help="Iniciar servidor MCP por stdio para Claude Desktop",
    )
    parser.add_argument(
        "--carpeta",
        type=Path,
        default=None,
        help="Carpeta del proyecto a analizar",
    )
    return parser.parse_args()


def _seleccionar_carpeta() -> Path:
    """Abre dialogo grafico si no se paso --carpeta."""
    # Intentar PySide6
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog
        app = QApplication.instance() or QApplication(sys.argv)
        carpeta = QFileDialog.getExistingDirectory(None, "Seleccionar carpeta del proyecto")
        if not carpeta:
            print("No se selecciono ninguna carpeta.", file=sys.stderr)
            sys.exit(1)
        return Path(carpeta)
    except ImportError:
        pass

    # Intentar tkinter
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta del proyecto")
        root.destroy()
        if not carpeta:
            print("No se selecciono ninguna carpeta.", file=sys.stderr)
            sys.exit(1)
        return Path(carpeta)
    except ImportError:
        pass

    print(
        "Error: se requiere --carpeta o tener PySide6/tkinter instalado "
        "para el dialogo grafico.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    args = _parsear_args()

    carpeta = args.carpeta if args.carpeta else _seleccionar_carpeta()
    carpeta = carpeta.resolve()

    if not carpeta.exists():
        print(f"Error: la carpeta '{carpeta}' no existe.", file=sys.stderr)
        sys.exit(1)

    if not carpeta.is_dir():
        print(f"Error: '{carpeta}' no es una carpeta.", file=sys.stderr)
        sys.exit(1)

    if args.mcp:
        from core.mcp.server import iniciar_servidor
        asyncio.run(iniciar_servidor(carpeta))
    elif args.web:
        from interfaces.web.server import iniciar_web
        iniciar_web(carpeta)


if __name__ == "__main__":
    main()