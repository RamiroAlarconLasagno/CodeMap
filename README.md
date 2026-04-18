# CodeMap — Analizador Interactivo de Código para LLMs

Herramienta local que analiza proyectos de software, construye un índice estructural
en memoria y lo expone a través de dos interfaces: una web interactiva (`--web`) y un
servidor MCP para Claude Desktop (`--mcp`).

---

## Problema que resuelve

Las LLMs tienen límite de contexto. Darles todo el código de una vez consume tokens
innecesariamente y reduce la calidad del razonamiento. CodeMap permite navegación
quirúrgica por capas: árbol → archivo → clase → método → implementación puntual.

---

## Arquitectura

```
Motor AST / Regex  →  ProjectIndex (memoria)  →  FastAPI REST  →  React frontend  (--web)
                                              →  MCP stdio                         (--mcp)
```

El índice se construye una sola vez al iniciar. Las consultas no tocan disco. El índice
se reconstruye solo cuando se invoca `reanalizar`. Ambas interfaces comparten el mismo
índice a través de `core/state.py`.

### Regla de dependencias

```
shared/  ←  core/  ←  interfaces/
```

`core/` no importa nada de `interfaces/`. El flujo es unidireccional.

---

## Lenguajes soportados

| Extensión | Lenguaje | Parser |
|-----------|----------|--------|
| `.py` | Python | `ast` stdlib — preciso, extrae todo |
| `.dart` | Dart | Regex + contador de llaves |
| `.js` `.jsx` | JavaScript | Regex + contador de llaves |
| `.ts` `.tsx` | TypeScript | Regex + contador de llaves |
| `.c` `.h` | C | Regex + contador de llaves |
| `.cpp` `.cc` `.cxx` `.hpp` | C++ | Regex + contador de llaves |

Para agregar un nuevo lenguaje: una entrada en `shared/config.py` →
`EXTENSIONES_SOPORTADAS` y un nuevo archivo `core/analyzer/nuevo_parser.py`.
El dispatcher y el resto del sistema no requieren cambios.

---

## Estructura de carpetas

```
codemap/
│
├── main.py                         # Punto de entrada --web / --mcp
├── requirements.txt
├── .gitignore
│
├── core/
│   ├── __init__.py
│   ├── index.py                    # Dataclasses: ProjectIndex, ArchivoInfo, ClaseInfo...
│   ├── state.py                    # Singleton del índice compartido entre interfaces
│   ├── queries.py                  # Consultas sobre el índice en memoria
│   ├── filters.py                  # Filtros: librería, patrón, idioma
│   │
│   ├── analyzer/                   # Motor de análisis — un archivo por lenguaje
│   │   ├── __init__.py             # Dispatcher por extensión + construir_indice()
│   │   ├── regex_base.py           # Utilidades compartidas entre parsers regex
│   │   ├── python_parser.py        # Parser AST — Python
│   │   ├── dart_parser.py          # Parser regex — Dart
│   │   ├── js_parser.py            # Parser regex — JS / TS / JSX / TSX
│   │   └── c_parser.py             # Parser regex — C / C++
│   │
│   └── mcp/
│       ├── __init__.py
│       └── server.py               # 14 herramientas MCP expuestas por stdio
│
├── interfaces/
│   └── web/
│       ├── __init__.py
│       ├── server.py               # FastAPI app
│       └── routes/
│           ├── __init__.py
│           ├── estructura.py       # GET /carpetas /clases /metodos /funciones /imports /variables
│           ├── relaciones.py       # GET /llamadas /usos /libreria /buscar /idioma
│           └── control.py          # GET /estado  POST /reanalizar  GET /exportar  POST /carpeta
│
├── shared/
│   ├── __init__.py
│   ├── config.py                   # CARPETAS_EXCLUIDAS, EXTENSIONES_SOPORTADAS, LLAMADAS_EXCLUIDAS
│   └── formatters.py               # exportar_txt() y exportar_md()
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/
        │   └── client.js           # Llamadas REST a FastAPI
        └── components/
            ├── TopBar.jsx          # Ruta activa, botón Reload, estado del índice
            ├── FilterPanel.jsx     # Checkboxes de detalle + filtro por librería
            ├── FileTree.jsx        # Árbol colapsable con badges CLASE/MET/FUN/VAR
            ├── DetailPanel.jsx     # Firma, docstring, llamadas del elemento seleccionado
            └── SearchBar.jsx       # Búsqueda en tiempo real con wildcards
```

---

## Qué extrae por archivo

**Todos los lenguajes:**
- Imports / includes / `#define`
- Clases con firma, clases base heredadas
- Atributos de clase (cuerpo de clase + constructor)
- Métodos con firma completa, `async`, llamadas únicas internas
- Funciones sueltas de módulo con firma
- Variables de módulo con tipo y valor inicial

**Solo Python (AST):**
- Decoradores exactos (`@property`, `@staticmethod`, etc.)
- Tipo de retorno (`-> tipo`)
- Docstrings compactados a una línea
- `self.x` en `__init__` como atributos de clase
- Variables con anotación de tipo (`x: int = 5`)

**No extrae (intencional):**
- Variables locales dentro de funciones
- Cuerpos completos de funciones
- Llamadas dinámicas (`getattr(obj, nombre)()`)
- Referencias cruzadas entre archivos
- Llamadas repetidas — si aparece 50 veces, se registra una

---

## Modos de ejecución

```bash
# Interfaz web local (localhost:8000)
python main.py --web --carpeta /ruta/proyecto

# Servidor MCP para Claude Desktop
python main.py --mcp --carpeta /ruta/proyecto

# Sin --carpeta abre diálogo gráfico (PySide6 o tkinter)
python main.py --web
```

---

## Consultas disponibles

### Estructura
| Función | Descripción |
|---------|-------------|
| `q_carpetas(indice)` | Árbol carpeta → lista de archivos |
| `q_imports(indice, archivo?)` | Imports por archivo |
| `q_clases(indice, archivo?)` | Clases sin métodos |
| `q_metodos(indice, clase)` | Métodos de una clase específica |
| `q_funciones(indice, archivo?)` | Funciones sueltas |
| `q_variables(indice, archivo?, scope?)` | Variables de módulo o de clase |

### Relaciones
| Función | Descripción |
|---------|-------------|
| `q_llamadas(indice, simbolo)` | Llamadas de `Clase.metodo` o `funcion` |
| `q_usos(indice, nombre)` | Dónde se usa un símbolo en el proyecto |

### Filtros
| Función | Descripción |
|---------|-------------|
| `f_libreria(indice, nombre)` | Archivos/funciones que usan una librería |
| `f_buscar(indice, patron)` | Búsqueda con wildcards `*` y `?` |
| `f_idioma(indice)` | Detecta mezcla es/en en nombres |

### Control
| Función | Descripción |
|---------|-------------|
| `q_estado(indice)` | Totales, fecha de análisis, errores |
| `exportar_txt(indice, nivel)` | TXT compacto: `estructura` / `firmas` / `completo` |
| `exportar_md(indice, nivel)` | Markdown: `estructura` / `firmas` / `completo` |

---

## Herramientas MCP (14 herramientas)

Todas con prefijo `codemap_`:

`carpetas` · `clases` · `metodos` · `funciones` · `imports` · `variables` · `llamadas` ·
`usos` · `libreria` · `buscar` · `idioma` · `estado` · `reanalizar` · `exportar`

### Configuración `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codemap": {
      "command": "python",
      "args": [
        "/ruta/absoluta/codemap/main.py",
        "--mcp",
        "--carpeta",
        "/ruta/del/proyecto"
      ]
    }
  }
}
```

---

## Instalación

### Requisitos

- Python 3.9+
- Node.js 18+ (solo para la interfaz web)

### Backend

```bash
git clone https://github.com/.../codemap
cd codemap
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
mcp>=1.0.0
# PySide6>=6.7.0  # opcional, para diálogo gráfico de carpeta
```

### Frontend (interfaz web)

Solo necesario si se usa `--web`. El modo `--mcp` no requiere Node.js.

```bash
cd frontend
npm install
```

Para desarrollo con recarga en caliente (proxy automático a `:8000`):
```bash
npm run dev        # abre localhost:5173
```

Para generar el build de producción que sirve FastAPI:
```bash
npm run build      # genera frontend/dist/
```

---

## Orden de implementación

**Fase 1 — Estructura base**
`index.py` → `state.py` → `config.py` → `queries.py` → `filters.py` → `formatters.py`

**Fase 2 — Motor y punto de entrada**
`analyzer/__init__.py` → `python_parser.py` → `main.py`

En este punto el sistema es funcional para proyectos Python.
MCP, web, queries y exportar funcionan antes de escribir un parser regex.

**Fase 3 — Interfaces**
`mcp/server.py` → `interfaces/web/server.py` → `routes/` → `frontend/`

**Fase 4 — Parsers regex (uno por uno)**
`regex_base.py` → `dart_parser.py` → `js_parser.py` → `c_parser.py`

---

## Decisiones de diseño

**`core/` no importa `interfaces/`**
Flujo unidireccional. Las interfaces son vistas del índice, no lógica de negocio.

**Estado centralizado en `core/state.py`**
El índice vive en un singleton compartido (`get_indice`, `set_indice`, `esta_inicializado`).
Ambas interfaces importan de ahí. Si en el futuro corren simultáneamente, comparten
el mismo índice sin cambios adicionales.

**Índice en memoria, sin base de datos**
Se reconstruye con `reanalizar`. Cero acceso a disco durante el uso normal.

**Un archivo por parser de lenguaje**
Facilita mantenimiento, testing unitario y carga selectiva a una LLM.

**`regex_base.py` como capa compartida**
Limpiadores de strings/comentarios, mapa de scopes y extractor de bloques son
compartidos por todos los parsers regex. Ninguno reimplementa estas funciones.

**Constructor C++ con regex dinámico**
`RE_CTOR = re.compile(rf'...{re.escape(nombre_clase)}...')` generado por clase.
Evita que `SensorADE9000` se detecte como método `E9000`.

**Llamadas únicas por orden de aparición**
Si una función llama 50 veces a lo mismo, se registra una sola vez.
El objetivo es mostrar relación estructural, no frecuencia de ejecución.

**`exportar_md` como salida preferida para LLM**
El servidor MCP usa `exportar_md` por defecto. `exportar_txt` queda disponible
para casos donde se necesite algo más compacto.