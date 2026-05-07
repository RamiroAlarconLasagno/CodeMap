# main.py
"""Punto de entrada grafico de CodeMap. Lanza la interfaz web con Tkinter."""

from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox


URL_WEB = "http://localhost:8000"
FRONTEND_DIR = Path(__file__).parent / "frontend"


class AppCodeMap(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CodeMap")
        self.resizable(False, False)
        self._servidor_activo = False
        self._construir_ui()
        self._centrar_ventana(480, 260)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _construir_ui(self) -> None:
        PAD = 12

        # --- Fila carpeta ---
        marco_carpeta = tk.Frame(self)
        marco_carpeta.pack(fill="x", padx=PAD, pady=(PAD, 4))

        tk.Label(marco_carpeta, text="Carpeta del proyecto:").pack(anchor="w")

        marco_entrada = tk.Frame(marco_carpeta)
        marco_entrada.pack(fill="x")

        self._var_carpeta = tk.StringVar()
        self._entrada_carpeta = tk.Entry(
            marco_entrada,
            textvariable=self._var_carpeta,
            width=50,
        )
        self._entrada_carpeta.pack(side="left", fill="x", expand=True)

        tk.Button(
            marco_entrada,
            text="Buscar...",
            width=9,
            command=self._seleccionar_carpeta,
        ).pack(side="left", padx=(6, 0))

        # --- Label estado ---
        self._var_estado = tk.StringVar(value="Sin analizar")
        self._lbl_estado = tk.Label(
            self,
            textvariable=self._var_estado,
            fg="#666666",
            anchor="w",
        )
        self._lbl_estado.pack(fill="x", padx=PAD, pady=(0, 8))

        # --- Botones accion ---
        marco_botones = tk.Frame(self)
        marco_botones.pack(padx=PAD, pady=(0, PAD))

        self._btn_analizar = tk.Button(
            marco_botones,
            text="Analizar y iniciar servidor",
            width=24,
            command=self._iniciar_servidor,
        )
        self._btn_analizar.pack(side="left", padx=(0, 8))

        self._btn_abrir = tk.Button(
            marco_botones,
            text="Abrir en navegador",
            width=18,
            state="disabled",
            command=self._abrir_navegador,
        )
        self._btn_abrir.pack(side="left")

        # --- Segunda fila de botones ---
        marco_botones2 = tk.Frame(self)
        marco_botones2.pack(padx=PAD, pady=(0, PAD))

        self._btn_compilar = tk.Button(
            marco_botones2,
            text="Recompilar frontend",
            width=24,
            command=self._recompilar_frontend,
        )
        self._btn_compilar.pack(side="left")

        # --- Separador + estado servidor ---
        tk.Frame(self, height=1, bg="#cccccc").pack(fill="x", padx=PAD)
        self._var_servidor = tk.StringVar(value="Servidor: inactivo")
        tk.Label(
            self,
            textvariable=self._var_servidor,
            fg="#888888",
            font=("TkDefaultFont", 8),
            anchor="w",
        ).pack(fill="x", padx=PAD, pady=(4, 6))

    def _centrar_ventana(self, ancho: int, alto: int) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() - ancho) // 2
        y = (self.winfo_screenheight() - alto) // 2
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _seleccionar_carpeta(self) -> None:
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta del proyecto")
        if carpeta:
            self._var_carpeta.set(carpeta)
            self._var_estado.set("Sin analizar")
            self._lbl_estado.config(fg="#666666")

    def _iniciar_servidor(self) -> None:
        ruta_texto = self._var_carpeta.get().strip()
        if not ruta_texto:
            messagebox.showwarning("Falta carpeta", "Selecciona una carpeta antes de analizar.")
            return

        carpeta = Path(ruta_texto).resolve()
        if not carpeta.exists() or not carpeta.is_dir():
            messagebox.showerror("Carpeta invalida", f"La ruta no existe o no es una carpeta:\n{carpeta}")
            return

        if self._servidor_activo:
            messagebox.showinfo("Servidor activo", "El servidor ya esta corriendo.\nUsa 'Reanalizar' desde la interfaz web.")
            return

        self._btn_analizar.config(state="disabled")
        self._btn_compilar.config(state="disabled")
        self._var_servidor.set("Servidor: iniciando...")
        self.update()

        # Si dist/ no existe, compilar primero y luego arrancar
        if not (FRONTEND_DIR / "dist").exists():
            self._var_estado.set("Compilando frontend (primera vez)...")
            self._lbl_estado.config(fg="#e07b00")
            self.update()
            hilo = threading.Thread(
                target=self._compilar_y_arrancar, args=(carpeta,), daemon=True
            )
        else:
            self._var_estado.set("Analizando proyecto...")
            self._lbl_estado.config(fg="#e07b00")
            hilo = threading.Thread(
                target=self._ejecutar_servidor, args=(carpeta,), daemon=True
            )
        hilo.start()

    def _compilar_y_arrancar(self, carpeta: Path) -> None:
        """Corre npm run build y luego arranca el servidor."""
        exito, mensaje = self._correr_build()
        if not exito:
            self.after(0, lambda: self._error_build(mensaje))
            return
        self._ejecutar_servidor(carpeta)

    def _recompilar_frontend(self) -> None:
        """Fuerza npm run build independientemente del servidor."""
        self._btn_compilar.config(state="disabled")
        self._btn_analizar.config(state="disabled")
        self._var_estado.set("Recompilando frontend...")
        self._lbl_estado.config(fg="#e07b00")
        self.update()
        hilo = threading.Thread(target=self._hilo_recompilar, daemon=True)
        hilo.start()

    def _hilo_recompilar(self) -> None:
        exito, mensaje = self._correr_build()
        if exito:
            self.after(0, self._recompilacion_lista)
        else:
            self.after(0, lambda: self._error_build(mensaje))

    def _correr_build(self) -> tuple[bool, str]:
        """Ejecuta npm run build. Devuelve (exito, mensaje_error)."""
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            # Instalar dependencias primero
            resultado = subprocess.run(
                ["npm", "install"],
                cwd=str(FRONTEND_DIR),
                capture_output=True,
                text=True,
                shell=True,
            )
            if resultado.returncode != 0:
                return False, resultado.stderr or "npm install fallo"

        resultado = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            shell=True,
        )
        if resultado.returncode != 0:
            return False, resultado.stderr or "npm run build fallo"
        return True, ""

    def _recompilacion_lista(self) -> None:
        self._var_estado.set("Frontend recompilado correctamente")
        self._lbl_estado.config(fg="#2a8a2a")
        self._btn_compilar.config(state="normal")
        self._btn_analizar.config(state="normal" if not self._servidor_activo else "disabled")

    def _ejecutar_servidor(self, carpeta: Path) -> None:
        try:
            from interfaces.web.server import iniciar_web
            self._servidor_activo = True
            # Notificar UI antes de bloquear
            self.after(0, self._servidor_listo)
            iniciar_web(carpeta)  # bloquea hasta que el servidor se cierra
        except Exception as exc:
            self.after(0, lambda: self._servidor_error(str(exc)))

    def _servidor_listo(self) -> None:
        self._var_estado.set("Analisis completado — servidor activo")
        self._lbl_estado.config(fg="#2a8a2a")
        self._var_servidor.set(f"Servidor: {URL_WEB}")
        self._btn_abrir.config(state="normal")
        self._btn_analizar.config(text="Servidor activo", state="disabled")

    def _servidor_error(self, mensaje: str) -> None:
        self._servidor_activo = False
        self._var_estado.set("Error al iniciar el servidor")
        self._lbl_estado.config(fg="#cc0000")
        self._var_servidor.set("Servidor: inactivo")
        self._btn_analizar.config(state="normal")
        self._btn_compilar.config(state="normal")
        messagebox.showerror("Error", f"No se pudo iniciar el servidor:\n{mensaje}")

    def _error_build(self, mensaje: str) -> None:
        self._var_estado.set("Error al compilar el frontend")
        self._lbl_estado.config(fg="#cc0000")
        self._var_servidor.set("Servidor: inactivo")
        self._btn_analizar.config(state="normal")
        self._btn_compilar.config(state="normal")
        messagebox.showerror("Error de compilacion", f"npm run build fallo:\n{mensaje}")

    def _abrir_navegador(self) -> None:
        webbrowser.open(URL_WEB)


# ----------------------------------------------------------------------
# Punto de entrada
# ----------------------------------------------------------------------

def main() -> None:
    try:
        app = AppCodeMap()
        app.mainloop()
    except Exception as exc:
        print(f"Error fatal: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()