// frontend/src/api/client.js

const BASE_URL = ''  // vacio = misma origin (proxy Vite en dev, FastAPI en prod)

async function _get(ruta) {
  const res = await fetch(BASE_URL + ruta)
  if (!res.ok) throw new Error(`GET ${ruta} → ${res.status}`)
  return res.json()
}

async function _post(ruta, body = {}) {
  const res = await fetch(BASE_URL + ruta, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${ruta} → ${res.status}`)
  return res.json()
}

async function _getText(ruta) {
  const res = await fetch(BASE_URL + ruta)
  if (!res.ok) throw new Error(`GET ${ruta} → ${res.status}`)
  return res.text()
}

// ---------------------------------------------------------------------------
// Estructura
// ---------------------------------------------------------------------------

export function getCarpetas() {
  return _get('/carpetas')
}

export function getClases(archivo = null) {
  const q = archivo ? `?archivo=${encodeURIComponent(archivo)}` : ''
  return _get(`/clases${q}`)
}

/** clase: nombre exacto de la clase */
export function getMetodos(clase) {
  return _get(`/metodos/${encodeURIComponent(clase)}`)
}

export function getFunciones(archivo = null) {
  const q = archivo ? `?archivo=${encodeURIComponent(archivo)}` : ''
  return _get(`/funciones${q}`)
}

export function getImports(archivo = null) {
  const q = archivo ? `?archivo=${encodeURIComponent(archivo)}` : ''
  return _get(`/imports${q}`)
}

/** scope: 'modulo' | 'clase' | null */
export function getVariables(archivo = null, scope = null) {
  const params = new URLSearchParams()
  if (archivo) params.set('archivo', archivo)
  if (scope)   params.set('scope', scope)
  const q = params.toString() ? `?${params}` : ''
  return _get(`/variables${q}`)
}

// ---------------------------------------------------------------------------
// Relaciones
// ---------------------------------------------------------------------------

/** simbolo: 'Clase.metodo' o 'funcion_suelta' */
export function getLlamadas(simbolo) {
  return _get(`/llamadas/${encodeURIComponent(simbolo)}`)
}

export function getUsos(nombre) {
  return _get(`/usos/${encodeURIComponent(nombre)}`)
}

export function getLibreria(nombre) {
  return _get(`/libreria/${encodeURIComponent(nombre)}`)
}

/** patron: soporta wildcards * y ? */
export function getBuscar(patron) {
  return _get(`/buscar?patron=${encodeURIComponent(patron)}`)
}

export function getIdioma() {
  return _get('/idioma')
}

// ---------------------------------------------------------------------------
// Control
// ---------------------------------------------------------------------------

export function getEstado() {
  return _get('/estado')
}

export function postReanalizar() {
  return _post('/reanalizar')
}

/** nivel: 'estructura' | 'firmas' | 'completo' — devuelve texto plano.
 *  archivos: lista de rutas a incluir (null = todos).
 *  filtros: { firmas, docstrings, llamadas, imports, clases_base, variables }
 */
export async function getExportar(nivel = 'firmas', archivos = null, filtros = null) {
  const res = await fetch(`${BASE_URL}/exportar/${encodeURIComponent(nivel)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ archivos, filtros }),
  })
  if (!res.ok) throw new Error(`POST /exportar/${nivel} → ${res.status}`)
  return res.text()
}

/** ruta: string con la ruta absoluta de la nueva carpeta */
export function postCarpeta(ruta) {
  return _post('/carpeta', { carpeta: ruta })
}