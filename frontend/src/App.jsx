// frontend/src/App.jsx
import { useState, useEffect, useCallback } from 'react'
import {
  getEstado, getCarpetas, getBuscar, getLibreria,
  postReanalizar, postCarpeta,
} from './api/client.js'

// Componentes — se implementan en commits posteriores, placeholders por ahora
import TopBar      from './components/TopBar.jsx'
import FilterPanel from './components/FilterPanel.jsx'
import FileTree    from './components/FileTree.jsx'
import DetailPanel from './components/DetailPanel.jsx'

// ---------------------------------------------------------------------------
// Estado inicial
// ---------------------------------------------------------------------------

const FILTROS_INICIALES = {
  firmas:      true,
  docstrings:  true,
  llamadas:    false,
  imports:     false,
  clases_base: true,
  variables:   false,
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

export default function App() {
  // -- estado global --------------------------------------------------------
  const [estado,       setEstado]       = useState(null)
  const [archivos,     setArchivos]     = useState({})
  const [seleccionado, setSeleccionado] = useState(null)
  const [filtros,      setFiltros]      = useState(FILTROS_INICIALES)
  const [vista,        setVista]        = useState('estructura')
  const [librerias,    setLibrerias]    = useState([])
  const [busqueda,     setBusqueda]     = useState('')
  const [cargando,     setCargando]     = useState(false)
  const [error,        setError]        = useState(null)

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
    setBusqueda('')
    setSeleccionado(null)
  }, [])

  const handleSeleccionar = useCallback((item) => {
    setSeleccionado(item)
  }, [])

  const handleBuscar = useCallback(async (patron) => {
    setBusqueda(patron)
    if (!patron.trim()) {
      const arbol = await getCarpetas()
      setArchivos(arbol)
      return
    }
    setCargando(true)
    try {
      const resultados = await getBuscar(patron)
      // Agrupar resultados por carpeta para que FileTree los pueda renderizar
      const agrupado = {}
      for (const item of resultados) {
        const partes = (item.archivo || '').split('/')
        const carpeta = partes.slice(0, -1).join('/') || '.'
        if (!agrupado[carpeta]) agrupado[carpeta] = []
        if (!agrupado[carpeta].includes(item.archivo)) {
          agrupado[carpeta].push(item.archivo)
        }
      }
      setArchivos(agrupado)
    } catch (e) {
      setError('Error en la busqueda.')
    } finally {
      setCargando(false)
    }
  }, [])

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

      {/* FileTree — columna central */}
      <FileTree
        archivos={archivos}
        filtros={filtros}
        seleccionado={seleccionado}
        onSeleccionar={handleSeleccionar}
        cargando={cargando}
        error={error}
      />

      {/* DetailPanel — columna derecha */}
      <DetailPanel
        seleccionado={seleccionado}
        onNavegar={handleSeleccionar}
      />

    </div>
  )
}