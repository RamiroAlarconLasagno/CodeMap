// frontend/src/App.jsx
import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getEstado, getCarpetas, getBuscar, getLibreria,
  postReanalizar, postCarpeta,
} from './api/client.js'

import TopBar      from './components/TopBar.jsx'
import FilterPanel from './components/FilterPanel.jsx'
import FileTree    from './components/FileTree.jsx'
import DetailPanel from './components/DetailPanel.jsx'
import ScopePanel      from './components/ScopePanel.jsx'
import RelacionesPanel from './components/RelacionesPanel.jsx'
import BusquedaPanel  from './components/BusquedaPanel.jsx'

// ---------------------------------------------------------------------------
// Estado inicial
// ---------------------------------------------------------------------------

const FILTROS_INICIALES = {
  clases:             true,
  metodos:            true,
  funciones:          true,
  firmas:             true,
  docstrings:         true,
  llamadas:           false,
  imports:            false,
  clases_base:        true,
  variables_globales: false,
  variables_clase:    false,
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  // -- estado global --------------------------------------------------------
  const [estado,            setEstado]            = useState(null)
  const [archivos,          setArchivos]          = useState({})
  const [archivosCompletos, setArchivosCompletos] = useState({})
  const [archivosExcluidos, setArchivosExcluidos] = useState(new Set())
  const [tabCentral,        setTabCentral]        = useState('estructura')
  const [seleccionado,      setSeleccionado]      = useState(null)
  const [filtros,           setFiltros]           = useState(FILTROS_INICIALES)
  const [vista,             setVista]             = useState('estructura')
  const [librerias,         setLibrerias]         = useState([])
  const [busqueda,          setBusqueda]          = useState('')
  const [resultadosBusqueda, setResultadosBusqueda] = useState([])
  const [cargando,          setCargando]          = useState(false)
  const [error,             setError]             = useState(null)

  // archivos visibles en FileTree = filtro actual (librería/búsqueda) ∩ scope
  const archivosVisibles = useMemo(() => {
    if (!archivosExcluidos.size) return archivos
    const result = {}
    for (const [carpeta, rutas] of Object.entries(archivos)) {
      const filtradas = rutas.filter(r => !archivosExcluidos.has(r))
      if (filtradas.length) result[carpeta] = filtradas
    }
    return result
  }, [archivos, archivosExcluidos])

  // lista plana para el export (usa árbol completo ∩ scope, sin filtro búsqueda/lib)
  const archivosActivos = useMemo(() => {
    if (!archivosExcluidos.size) return null  // null = backend exporta todo
    return Object.values(archivosCompletos).flat().filter(r => !archivosExcluidos.has(r))
  }, [archivosCompletos, archivosExcluidos])

  // -- carga inicial --------------------------------------------------------
  useEffect(() => {
    _cargarEstadoYArbol()
  }, [])

  async function _cargarEstadoYArbol() {
    setCargando(true)
    setError(null)
    try {
      const est = await getEstado()
      setEstado(est)
      if (est.total_archivos > 0) {
        const arbol = await getCarpetas()
        setArchivos(arbol)
        setArchivosCompletos(arbol)
        setArchivosExcluidos(new Set())
      }
    } catch (e) {
      setError('No se pudo conectar con el backend.')
    } finally {
      setCargando(false)
    }
  }

  // -- handlers -------------------------------------------------------------

  const handleReanalizar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const est = await postReanalizar()
      setEstado(est)
      const arbol = await getCarpetas()
      setArchivos(arbol)
      setArchivosCompletos(arbol)
      setArchivosExcluidos(new Set())
      setSeleccionado(null)
    } catch (e) {
      setError('Error al reanalizar.')
    } finally {
      setCargando(false)
    }
  }, [])

  const handleCambiarCarpeta = useCallback(async (ruta) => {
    if (!ruta) return
    setCargando(true)
    setError(null)
    try {
      const est = await postCarpeta(ruta)
      setEstado(est)
      const arbol = await getCarpetas()
      setArchivos(arbol)
      setArchivosCompletos(arbol)
      setArchivosExcluidos(new Set())
      setSeleccionado(null)
      setBusqueda('')
      setLibrerias([])
    } catch (e) {
      setError(`Carpeta no encontrada: ${ruta}`)
    } finally {
      setCargando(false)
    }
  }, [])

  const handleFiltroChange = useCallback((campo) => {
    setFiltros(prev => ({ ...prev, [campo]: !prev[campo] }))
  }, [])

  const handleVistaChange = useCallback((nuevaVista) => {
    setVista(nuevaVista)
    setSeleccionado(null)
    if (nuevaVista !== 'busqueda') {
      setBusqueda('')
      setResultadosBusqueda([])
      setArchivos(archivosCompletos)
    }
  }, [archivosCompletos])

  const handleSeleccionar = useCallback((item) => {
    setSeleccionado(item)
  }, [])

  const handleBuscar = useCallback(async (patron) => {
    setBusqueda(patron)
    if (!patron.trim()) {
      setResultadosBusqueda([])
      setArchivos(archivosCompletos)
      setVista('estructura')
      return
    }
    setVista('busqueda')
    setCargando(true)
    try {
      const resultados = await getBuscar(patron)
      setResultadosBusqueda(resultados)
    } catch (e) {
      setError('Error en la busqueda.')
    } finally {
      setCargando(false)
    }
  }, [archivosCompletos])

  const handleToggleArchivo = useCallback((ruta) => {
    setArchivosExcluidos(prev => {
      const next = new Set(prev)
      if (next.has(ruta)) next.delete(ruta)
      else next.add(ruta)
      return next
    })
  }, [])

  const handleToggleCarpeta = useCallback((carpeta, incluir) => {
    setArchivosExcluidos(prev => {
      const rutas = archivosCompletos[carpeta] ?? []
      const next = new Set(prev)
      for (const ruta of rutas) {
        if (incluir) next.delete(ruta)
        else next.add(ruta)
      }
      return next
    })
  }, [archivosCompletos])

  const handleToggleTodo = useCallback((incluir) => {
    if (incluir) {
      setArchivosExcluidos(new Set())
    } else {
      setArchivosExcluidos(new Set(Object.values(archivosCompletos).flat()))
    }
  }, [archivosCompletos])

  const handleLibreriaAdd = useCallback(async (nombre) => {
    if (!nombre || librerias.includes(nombre)) return
    const nuevas = [...librerias, nombre]
    setLibrerias(nuevas)
    await _aplicarFiltroLibrerias(nuevas)
  }, [librerias])

  const handleLibreriaRemove = useCallback(async (nombre) => {
    const nuevas = librerias.filter(l => l !== nombre)
    setLibrerias(nuevas)
    if (nuevas.length === 0) {
      const arbol = await getCarpetas()
      setArchivos(arbol)
    } else {
      await _aplicarFiltroLibrerias(nuevas)
    }
  }, [librerias])

  async function _aplicarFiltroLibrerias(tags) {
    setCargando(true)
    try {
      const resultados = await Promise.all(tags.map(t => getLibreria(t)))
      const archivosSet = new Set()
      for (const res of resultados) {
        for (const item of res) {
          if (item.archivo) archivosSet.add(item.archivo)
        }
      }
      const arbolFiltrado = {}
      for (const ruta of archivosSet) {
        const partes = ruta.split('/')
        const carpeta = partes.slice(0, -1).join('/') || '.'
        if (!arbolFiltrado[carpeta]) arbolFiltrado[carpeta] = []
        arbolFiltrado[carpeta].push(ruta)
      }
      setArchivos(arbolFiltrado)
    } catch (e) {
      setError('Error al filtrar por libreria.')
    } finally {
      setCargando(false)
    }
  }

  // -- render ---------------------------------------------------------------

  return (
    <div className="grid h-screen overflow-hidden"
         style={{ gridTemplateRows: '48px 1fr', gridTemplateColumns: '260px 1fr 300px' }}>

      {/* TopBar — fila 1, todas las columnas */}
      <div className="col-span-3">
        <TopBar
          estado={estado}
          cargando={cargando}
          onReanalizar={handleReanalizar}
          onCambiarCarpeta={handleCambiarCarpeta}
          archivosActivos={archivosActivos}
          filtros={filtros}
        />
      </div>

      {/* FilterPanel — columna izquierda (incluye SearchBar y filtro libreria) */}
      <FilterPanel
        filtros={filtros}
        onFiltroChange={handleFiltroChange}
        librerias={librerias}
        onLibreriaAdd={handleLibreriaAdd}
        onLibreriaRemove={handleLibreriaRemove}
        vista={vista}
        onVistaChange={handleVistaChange}
        busqueda={busqueda}
        onBuscar={handleBuscar}
      />

      {/* Panel central con pestañas */}
      <div className="flex flex-col overflow-hidden">
        {/* Tab bar */}
        <div className="flex border-b border-gray-800 bg-[#0f1117] px-2 gap-0.5 pt-1.5 shrink-0">
          {[
            { id: 'estructura', label: vista === 'relaciones' ? 'relaciones' : vista === 'busqueda' ? 'búsqueda' : 'código' },
            { id: 'alcance',    label: `alcance${archivosExcluidos.size ? ` (${archivosExcluidos.size})` : ''}` },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setTabCentral(tab.id)}
              className={`text-[11px] px-3 py-1 rounded-t border-b-2 transition-colors font-mono
                ${tabCentral === tab.id
                  ? 'border-[#1D9E75] text-[#1D9E75] bg-gray-900/50'
                  : 'border-transparent text-gray-500 hover:text-gray-300'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Contenido */}
        {tabCentral === 'alcance' ? (
          <ScopePanel
            archivos={archivosCompletos}
            excluidos={archivosExcluidos}
            onToggleArchivo={handleToggleArchivo}
            onToggleCarpeta={handleToggleCarpeta}
            onToggleTodo={handleToggleTodo}
          />
        ) : vista === 'relaciones' ? (
          <RelacionesPanel librerias={librerias} />
        ) : vista === 'busqueda' ? (
          <BusquedaPanel
            resultados={resultadosBusqueda}
            patron={busqueda}
            onSeleccionar={handleSeleccionar}
          />
        ) : (
          <FileTree
            archivos={archivosVisibles}
            filtros={filtros}
            seleccionado={seleccionado}
            onSeleccionar={handleSeleccionar}
            cargando={cargando}
            error={error}
          />
        )}
      </div>

      {/* DetailPanel — columna derecha */}
      <DetailPanel
        seleccionado={seleccionado}
        onNavegar={handleSeleccionar}
        filtros={filtros}
      />

    </div>
  )
}