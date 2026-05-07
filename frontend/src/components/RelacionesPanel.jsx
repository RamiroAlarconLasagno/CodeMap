// frontend/src/components/RelacionesPanel.jsx
import { useState, useEffect, useRef } from 'react'
import { getBuscar, getLlamadas, getUsos, getLibreria } from '../api/client.js'

const MODOS = [
  { id: 'llamadas',  label: 'llamadas' },
  { id: 'usos',      label: 'usos' },
  { id: 'librerias', label: 'librerías' },
]

// ---------------------------------------------------------------------------
// Pill de tipo de símbolo
// ---------------------------------------------------------------------------

function TipoBadge({ tipo }) {
  const estilos = {
    metodo:  'bg-green-900 text-green-300 border-green-700',
    funcion: 'bg-yellow-900 text-yellow-300 border-yellow-700',
    clase:   'bg-blue-900 text-blue-300 border-blue-700',
  }
  const etiquetas = { metodo: 'MET', funcion: 'FUN', clase: 'CLASE' }
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded border shrink-0 leading-none font-medium
      ${estilos[tipo] ?? 'bg-gray-800 text-gray-400 border-gray-600'}`}>
      {etiquetas[tipo] ?? tipo}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Modo LLAMADAS
// ---------------------------------------------------------------------------

function ModoLlamadas() {
  const [query,         setQuery]         = useState('')
  const [sugerencias,   setSugerencias]   = useState([])
  const [llamadasData,  setLlamadasData]  = useState(null)
  const [cargando,      setCargando]      = useState(false)
  const debounceRef = useRef(null)

  function handleQueryChange(val) {
    setQuery(val)
    setLlamadasData(null)
    clearTimeout(debounceRef.current)
    if (!val.trim()) { setSugerencias([]); return }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await getBuscar(val)
        setSugerencias(res.filter(r => r.tipo !== 'clase').slice(0, 15))
      } catch {}
    }, 280)
  }

  async function seleccionar(item) {
    setSugerencias([])
    setQuery(item.nombre)
    setCargando(true)
    try {
      const data = await getLlamadas(item.nombre)
      setLlamadasData(data ?? { simbolo: item.nombre, archivo: item.archivo, llamadas: [] })
    } catch {
      setLlamadasData({ simbolo: item.nombre, archivo: item.archivo, llamadas: [] })
    } finally {
      setCargando(false)
    }
  }

  return (
    <div>
      {/* Input con sugerencias */}
      <div className="relative mb-4">
        <input
          value={query}
          onChange={e => handleQueryChange(e.target.value)}
          placeholder="Clase.metodo o funcion…"
          className="w-full text-[11px] px-3 py-1.5 rounded bg-gray-800 border border-gray-700
                     text-gray-200 placeholder-gray-600 outline-none focus:border-[#1D9E75]
                     transition-colors"
        />
        {sugerencias.length > 0 && (
          <div className="absolute top-full left-0 right-0 z-20 mt-0.5 bg-[#1a1d27]
                          border border-gray-700 rounded shadow-lg max-h-52 overflow-y-auto">
            {sugerencias.map((s, i) => (
              <button
                key={i}
                onClick={() => seleccionar(s)}
                className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-700
                           text-left transition-colors"
              >
                <TipoBadge tipo={s.tipo} />
                <span className="text-gray-200 truncate">{s.nombre}</span>
                <span className="text-gray-600 text-[10px] ml-auto shrink-0">
                  {s.archivo?.split('/').pop()}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Resultado */}
      {cargando && (
        <div className="text-gray-600 text-[11px] animate-pulse">cargando…</div>
      )}

      {llamadasData && !cargando && (
        <div>
          <div className="text-[10px] text-gray-600 mb-1 truncate">{llamadasData.archivo}</div>
          <div className="text-gray-200 font-medium mb-3">{llamadasData.simbolo}</div>
          {llamadasData.llamadas.length === 0 ? (
            <div className="text-gray-600 italic text-[11px]">sin llamadas registradas</div>
          ) : (
            <div className="flex flex-col gap-1">
              {llamadasData.llamadas.map((l, i) => (
                <div key={i}
                     className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-gray-800/60 border-l-2 border-[#1D9E75]/40">
                  <span className="text-gray-600 text-[10px] shrink-0">→</span>
                  <span className="text-[#1D9E75] text-[11px] truncate">{l}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!query && !llamadasData && (
        <p className="text-gray-700 text-[11px]">
          Escribe el nombre de un método o función para ver qué llama.
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Modo USOS
// ---------------------------------------------------------------------------

function ModoUsos() {
  const [query,    setQuery]    = useState('')
  const [usos,     setUsos]     = useState([])
  const [buscado,  setBuscado]  = useState(false)
  const [cargando, setCargando] = useState(false)

  async function buscar() {
    if (!query.trim()) return
    setCargando(true)
    setBuscado(false)
    try {
      const res = await getUsos(query.trim())
      setUsos(res)
    } finally {
      setCargando(false)
      setBuscado(true)
    }
  }

  // Agrupar por archivo
  const porArchivo = {}
  for (const u of usos) {
    if (!porArchivo[u.archivo]) porArchivo[u.archivo] = []
    porArchivo[u.archivo].push(u)
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && buscar()}
          placeholder="nombre del símbolo…"
          className="flex-1 text-[11px] px-3 py-1.5 rounded bg-gray-800 border border-gray-700
                     text-gray-200 placeholder-gray-600 outline-none focus:border-[#1D9E75]
                     transition-colors"
        />
        <button
          onClick={buscar}
          disabled={!query.trim() || cargando}
          className="text-[11px] px-3 py-1.5 rounded border border-[#1D9E75] text-[#1D9E75]
                     hover:bg-[#1D9E75] hover:text-white transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
        >
          buscar
        </button>
      </div>

      {cargando && (
        <div className="text-gray-600 text-[11px] animate-pulse">buscando…</div>
      )}

      {buscado && !cargando && usos.length === 0 && (
        <div className="text-gray-600 italic text-[11px]">sin usos encontrados para "{query}"</div>
      )}

      {!cargando && usos.length > 0 && (
        <div className="flex flex-col gap-3">
          <div className="text-[10px] text-gray-600">
            {usos.length} referencia{usos.length !== 1 ? 's' : ''} en {Object.keys(porArchivo).length} archivo{Object.keys(porArchivo).length !== 1 ? 's' : ''}
          </div>
          {Object.entries(porArchivo).map(([archivo, lista]) => (
            <div key={archivo}>
              <div className="text-[10px] text-gray-500 mb-1 truncate">{archivo}</div>
              <div className="flex flex-col gap-0.5 ml-1">
                {lista.map((u, i) => (
                  <div key={i}
                       className="flex items-center gap-2 px-2.5 py-1 rounded bg-gray-800/60 text-[11px]">
                    <span className="text-gray-400 truncate shrink-0 max-w-[120px]">{u.contexto}</span>
                    <span className="text-gray-700 shrink-0">→</span>
                    <span className="text-[#1D9E75] truncate">{u.llamada}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {!query && (
        <p className="text-gray-700 text-[11px]">
          Escribe un nombre parcial y presioná Enter para ver en qué métodos se llama.
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Modo LIBRERÍAS
// ---------------------------------------------------------------------------

function ModoLibrerias({ librerias }) {
  const [libData,  setLibData]  = useState({})
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    if (!librerias.length) return
    let activo = true
    async function cargar() {
      setCargando(true)
      try {
        const resultados = await Promise.all(librerias.map(l => getLibreria(l)))
        if (!activo) return
        const data = {}
        librerias.forEach((l, i) => { data[l] = resultados[i] })
        setLibData(data)
      } finally {
        if (activo) setCargando(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [librerias.join(',')])

  if (!librerias.length) return (
    <p className="text-gray-700 text-[11px]">
      Agrega librerías en el panel izquierdo para ver sus relaciones aquí.
    </p>
  )

  if (cargando) return (
    <div className="text-gray-600 text-[11px] animate-pulse">cargando…</div>
  )

  return (
    <div className="flex flex-col gap-5">
      {librerias.map(lib => {
        const resultados = libData[lib] ?? []

        // Agrupar por archivo
        const porArchivo = {}
        for (const r of resultados) {
          if (!porArchivo[r.archivo]) porArchivo[r.archivo] = { imports: [], llamadas: [] }
          if (r.tipo === 'import') {
            porArchivo[r.archivo].imports.push(r.detalle)
          } else {
            const calls = Array.isArray(r.detalle) ? r.detalle : [r.detalle]
            porArchivo[r.archivo].llamadas.push(...calls)
          }
        }

        const archivosCount = Object.keys(porArchivo).length

        return (
          <div key={lib}>
            {/* Encabezado de librería */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] text-[#1D9E75] font-medium px-2 py-0.5 rounded
                               bg-[#1D9E75]/10 border border-[#1D9E75]/30">
                {lib}
              </span>
              <span className="text-[10px] text-gray-600">
                {archivosCount} archivo{archivosCount !== 1 ? 's' : ''}
              </span>
            </div>

            {archivosCount === 0 ? (
              <div className="text-gray-700 italic text-[11px] ml-1">sin resultados</div>
            ) : (
              <div className="flex flex-col gap-1 ml-1">
                {Object.entries(porArchivo).map(([archivo, data]) => (
                  <div key={archivo}
                       className="px-2.5 py-1.5 rounded bg-gray-800/60 border-l-2 border-gray-700">
                    <div className="text-[10px] text-gray-400 truncate mb-0.5">{archivo}</div>
                    {data.imports.map((imp, i) => (
                      <div key={i} className="text-[10px] text-gray-600">
                        import <span className="text-gray-500">{imp}</span>
                      </div>
                    ))}
                    {data.llamadas.length > 0 && (
                      <div className="text-[10px] text-gray-600 truncate">
                        llama: <span className="text-gray-500">
                          {data.llamadas.slice(0, 4).join(', ')}
                          {data.llamadas.length > 4 ? ` +${data.llamadas.length - 4}` : ''}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// RelacionesPanel — raíz
// ---------------------------------------------------------------------------

export default function RelacionesPanel({ librerias = [] }) {
  const [modo, setModo] = useState('llamadas')

  return (
    <div className="bg-gray-950 flex flex-col overflow-hidden font-mono">
      {/* Mode selector */}
      <div className="flex border-b border-gray-800 px-2 gap-0.5 pt-1.5 shrink-0">
        {MODOS.map(m => (
          <button
            key={m.id}
            onClick={() => setModo(m.id)}
            className={`text-[11px] px-3 py-1 rounded-t border-b-2 transition-colors
              ${modo === m.id
                ? 'border-[#1D9E75] text-[#1D9E75]'
                : 'border-transparent text-gray-500 hover:text-gray-300'}`}
          >
            {m.label}
            {m.id === 'librerias' && librerias.length > 0 && (
              <span className="ml-1 text-[#1D9E75]/70">({librerias.length})</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {modo === 'llamadas'  && <ModoLlamadas />}
        {modo === 'usos'      && <ModoUsos />}
        {modo === 'librerias' && <ModoLibrerias librerias={librerias} />}
      </div>
    </div>
  )
}
