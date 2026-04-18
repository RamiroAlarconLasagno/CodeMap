# interfaces/web/server.py
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.analyzer import construir_indice
from core.state import set_indice
from interfaces.web.routes.control import router as router_control
from interfaces.web.routes.estructura import router as router_estructura
from interfaces.web.routes.relaciones import router as router_relaciones

# ---------------------------------------------------------------------------
# Creacion de la app (importable para tests con TestClient)
# ---------------------------------------------------------------------------

def crear_app() -> FastAPI:
    """Fabrica la FastAPI app con todos los routers registrados."""
    app = FastAPI(title="CodeMap API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router_estructura)
    app.include_router(router_relaciones)
    app.include_router(router_control)

    # Frontend React (solo si el build existe)
    dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    return app


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def iniciar_web(carpeta: Path) -> None:
    """Construye el indice y arranca el servidor FastAPI en localhost:8000."""
    set_indice(construir_indice(carpeta))
    app = crear_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)