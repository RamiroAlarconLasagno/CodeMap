// frontend/src/components/TopBar.jsx
import { useState } from 'react'

// Formatea la fecha ISO del backend a algo legible
function _formatearFecha(iso) {
  if (!iso) return null
  try {
    return new Date(iso).toLocaleString('es', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export default function TopBar({ estado, cargando, onReanalizar, onCambiarCarpeta }) {
  const [editandoRuta, setEditandoRuta] = useState(false)
  const [inputRuta, setInputRuta] = useState('')

  function _confirmarRuta(e) {
    e.preventDefault()
    const ruta = inputRuta.trim()
    if (ruta) onCambiarCarpeta(ruta)
    setEditandoRuta(false)
    setInputRuta('')
  }

  function _cancelar() {
    setEditandoRuta(false)
    setInputRuta('')
  }

  const fecha = _formatearFecha(estado?.ultimo_analisis)

  return (
    <div className="flex items-center gap-3 px-4 h-full bg-[#0f1117] border-b border-gray-800 font-mono select-none">

      {/* Logo */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="w-2 h-2 rounded-full bg-[#1D9E75]
                         animate-[pulse_2s_ease-in-out_infinite]" />
        <span className="text-[13px] font-medium text-gray-100 tracking-tight">
          CodeMap
        </span>
      </div>

      {/* Ruta activa / input para cambiar carpeta */}
      {editandoRuta ? (
        <form onSubmit={_confirmarRuta} className="flex items-center gap-2 flex-1 max-w-md">
          <input
            autoFocus
            value={inputRuta}
            onChange={e => setInputRuta(e.target.value)}
            onKeyDown={e => e.key === 'Escape' && _cancelar()}
            placeholder="/ruta/del/proyecto"
            className="flex-1 text-[11px] px-2 py-1 rounded bg-gray-800 border border-[#1D9E75]
                       text-gray-100 outline-none placeholder-gray-600"
          />
          <button type="submit"
                  className="text-[11px] px-2 py-1 rounded bg-[#1D9E75] text-white">
            ok
          </button>
          <button type="button" onClick={_cancelar}
                  className="text-[11px] px-2 py-1 rounded border border-gray-700 text-gray-400">
            ✕
          </button>
        </form>
      ) : (
        <button
          onClick={() => { setEditandoRuta(true); setInputRuta(estado?.carpeta_raiz ?? '') }}
          title="Cambiar carpeta"
          className="text-[11px] text-gray-400 bg-gray-800 px-2 py-1 rounded
                     border border-gray-700 max-w-xs truncate hover:border-gray-500
                     hover:text-gray-300 transition-colors text-left"
        >
          {estado?.carpeta_raiz ?? '—'}
        </button>
      )}

      {/* Totales */}
      {estado && (
        <div className="hidden md:flex items-center gap-3 text-[11px] text-gray-500">
          <span>{estado.total_archivos} archivos</span>
          <span className="text-gray-700">·</span>
          <span>{estado.total_clases} clases</span>
          <span className="text-gray-700">·</span>
          <span>{estado.total_metodos} métodos</span>
          <span className="text-gray-700">·</span>
          <span>{estado.total_funciones} funciones</span>
        </div>
      )}

      <div className="flex-1" />

      {/* Fecha de análisis */}
      {fecha && (
        <span className="hidden lg:block text-[10px] text-gray-600">
          {fecha}
        </span>
      )}

      {/* Errores del índice */}
      {estado?.archivos_con_error?.length > 0 && (
        <span className="text-[11px] text-yellow-500"
              title={estado.archivos_con_error.map(e => e.archivo).join('\n')}>
          ⚠ {estado.archivos_con_error.length} error{estado.archivos_con_error.length > 1 ? 'es' : ''}
        </span>
      )}

      {/* Botón reanalizar */}
      <button
        onClick={onReanalizar}
        disabled={cargando}
        className="text-[11px] px-3 py-1.5 rounded border border-gray-700
                   bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-gray-100
                   disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
      >
        {cargando ? 'analizando…' : '↻ reanalizar'}
      </button>

    </div>
  )
}