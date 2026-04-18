// frontend/src/api/client.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getCarpetas, getClases, getMetodos, getFunciones, getImports, getVariables,
  getLlamadas, getUsos, getLibreria, getBuscar, getIdioma,
  getEstado, postReanalizar, getExportar, postCarpeta,
} from './client.js'

// ---------------------------------------------------------------------------
// Mock global de fetch
// ---------------------------------------------------------------------------

const mockJson  = vi.fn()
const mockText  = vi.fn()
const mockFetch = vi.fn()

beforeEach(() => {
  mockJson.mockReset()
  mockText.mockReset()
  mockFetch.mockReset()

  // Respuesta OK por defecto
  mockFetch.mockResolvedValue({
    ok: true,
    json: mockJson,
    text: mockText,
  })
  mockJson.mockResolvedValue({})
  mockText.mockResolvedValue('')

  vi.stubGlobal('fetch', mockFetch)
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function urlLlamada() {
  return mockFetch.mock.calls[0][0]
}

function opcionesLlamada() {
  return mockFetch.mock.calls[0][1]
}

// ---------------------------------------------------------------------------
// Estructura
// ---------------------------------------------------------------------------

describe('getCarpetas', () => {
  it('llama GET /carpetas', async () => {
    await getCarpetas()
    expect(urlLlamada()).toBe('/carpetas')
    expect(opcionesLlamada()).toBeUndefined()
  })
})

describe('getClases', () => {
  it('sin archivo: GET /clases', async () => {
    await getClases()
    expect(urlLlamada()).toBe('/clases')
  })

  it('con archivo: agrega ?archivo= codificado', async () => {
    await getClases('core/index.py')
    expect(urlLlamada()).toBe('/clases?archivo=core%2Findex.py')
  })
})

describe('getMetodos', () => {
  it('codifica el nombre de clase en la ruta', async () => {
    await getMetodos('ProjectIndex')
    expect(urlLlamada()).toBe('/metodos/ProjectIndex')
  })

  it('codifica nombres con punto (Clase.Inner)', async () => {
    await getMetodos('Clase.Inner')
    expect(urlLlamada()).toBe('/metodos/Clase.Inner')
  })
})

describe('getFunciones', () => {
  it('sin archivo: GET /funciones', async () => {
    await getFunciones()
    expect(urlLlamada()).toBe('/funciones')
  })

  it('con archivo: agrega ?archivo=', async () => {
    await getFunciones('shared/formatters.py')
    expect(urlLlamada()).toBe('/funciones?archivo=shared%2Fformatters.py')
  })
})

describe('getImports', () => {
  it('sin archivo: GET /imports', async () => {
    await getImports()
    expect(urlLlamada()).toBe('/imports')
  })

  it('con archivo: agrega ?archivo=', async () => {
    await getImports('main.py')
    expect(urlLlamada()).toBe('/imports?archivo=main.py')
  })
})

describe('getVariables', () => {
  it('sin params: GET /variables', async () => {
    await getVariables()
    expect(urlLlamada()).toBe('/variables')
  })

  it('con scope modulo: agrega ?scope=modulo', async () => {
    await getVariables(null, 'modulo')
    expect(urlLlamada()).toBe('/variables?scope=modulo')
  })

  it('con archivo y scope: ambos params presentes', async () => {
    await getVariables('core/index.py', 'clase')
    const url = urlLlamada()
    expect(url).toContain('archivo=core%2Findex.py')
    expect(url).toContain('scope=clase')
  })
})

// ---------------------------------------------------------------------------
// Relaciones
// ---------------------------------------------------------------------------

describe('getLlamadas', () => {
  it('simbolo simple: GET /llamadas/funcion', async () => {
    await getLlamadas('construir_indice')
    expect(urlLlamada()).toBe('/llamadas/construir_indice')
  })

  it('simbolo con punto: codifica Clase.metodo', async () => {
    await getLlamadas('ProjectIndex.total_clases')
    expect(urlLlamada()).toBe('/llamadas/ProjectIndex.total_clases')
  })
})

describe('getUsos', () => {
  it('GET /usos/{nombre}', async () => {
    await getUsos('logger')
    expect(urlLlamada()).toBe('/usos/logger')
  })
})

describe('getLibreria', () => {
  it('GET /libreria/{nombre}', async () => {
    await getLibreria('mqtt')
    expect(urlLlamada()).toBe('/libreria/mqtt')
  })
})

describe('getBuscar', () => {
  it('patron simple: GET /buscar?patron=', async () => {
    await getBuscar('conectar')
    expect(urlLlamada()).toBe('/buscar?patron=conectar')
  })

  it('patron con wildcard *: se codifica correctamente', async () => {
    await getBuscar('*leer*')
    expect(urlLlamada()).toBe('/buscar?patron=*leer*')
  })

  it('patron con wildcard ?: se codifica correctamente', async () => {
    await getBuscar('get?')
    expect(urlLlamada()).toBe('/buscar?patron=get%3F')
  })
})

describe('getIdioma', () => {
  it('GET /idioma', async () => {
    await getIdioma()
    expect(urlLlamada()).toBe('/idioma')
  })
})

// ---------------------------------------------------------------------------
// Control
// ---------------------------------------------------------------------------

describe('getEstado', () => {
  it('GET /estado', async () => {
    await getEstado()
    expect(urlLlamada()).toBe('/estado')
  })
})

describe('postReanalizar', () => {
  it('POST /reanalizar sin body', async () => {
    await postReanalizar()
    expect(urlLlamada()).toBe('/reanalizar')
    expect(opcionesLlamada().method).toBe('POST')
    expect(JSON.parse(opcionesLlamada().body)).toEqual({})
  })
})

describe('getExportar', () => {
  it('nivel por defecto: firmas', async () => {
    await getExportar()
    expect(urlLlamada()).toBe('/exportar/firmas')
  })

  it('nivel estructura', async () => {
    await getExportar('estructura')
    expect(urlLlamada()).toBe('/exportar/estructura')
  })

  it('nivel completo', async () => {
    await getExportar('completo')
    expect(urlLlamada()).toBe('/exportar/completo')
  })

  it('llama text() no json() — respuesta es texto plano', async () => {
    await getExportar('firmas')
    expect(mockText).toHaveBeenCalled()
    expect(mockJson).not.toHaveBeenCalled()
  })
})

describe('postCarpeta', () => {
  it('POST /carpeta con body { carpeta: ruta }', async () => {
    await postCarpeta('/home/user/proyecto')
    expect(urlLlamada()).toBe('/carpeta')
    expect(opcionesLlamada().method).toBe('POST')
    expect(JSON.parse(opcionesLlamada().body)).toEqual({
      carpeta: '/home/user/proyecto',
    })
  })

  it('Content-Type es application/json', async () => {
    await postCarpeta('/ruta')
    expect(opcionesLlamada().headers['Content-Type']).toBe('application/json')
  })
})

// ---------------------------------------------------------------------------
// Manejo de errores
// ---------------------------------------------------------------------------

describe('errores HTTP', () => {
  it('lanza Error cuando el servidor devuelve 404', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 404 })
    await expect(getCarpetas()).rejects.toThrow('404')
  })

  it('lanza Error cuando el servidor devuelve 500', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500 })
    await expect(getEstado()).rejects.toThrow('500')
  })
})