// frontend/src/components/FilterPanel.jsx
import { useState } from 'react'
import SearchBar from './SearchBar.jsx'

// Definicion de filtros con etiqueta visible
const FILTROS = [
  { campo: 'firmas',      label: 'firmas' },
  { campo: 'docstrings',  label: 'docstrings' },
  { campo: 'llamadas',    label: 'llamadas' },
  { campo: 'imports',     label: 'imports' },
  { campo: 'clases_base', label: 'clases base' },
  { campo: 'variables',   label: 'variables' },
]

const VISTAS = [
  { id: 'estructura', label: 'estructura' },
  { id: 'relaciones', label: 'relaciones' },
  { id: 'busqueda',   label: 'búsqueda' },
]

function SeccionLabel({ children }) {
  return (
    <div className="text-[10px] font-medium text-gray-500 uppercase tracking-widest mb-2">
      {children}
    </div>
  )
}

export default function FilterPanel({
  filtros, onFiltroChange,
  librerias, onLibreriaAdd, onLibreriaRemove,
  vista, onVistaChange,
  busqueda, onBuscar,
}) {
  const [inputLib, setInputLib] = useState('')

  function _agregarLib(e) {
    e.preventDefault()
    const val = inputLib.trim().toLowerCase()
    if (val) { onLibreriaAdd(val); setInputLib('') }
  }

  return (
    <div className="flex flex-col bg-[#0f1117] border-r border-gray-800 overflow-hidden font-mono">

      {/* Búsqueda */}
      <div className="p-3 border-b border-gray-800">
        <SeccionLabel>buscar</SeccionLabel>
        <SearchBar
          valor={busqueda}
          onChange={onBuscar}
        />
      </div>

      {/* Vista */}
      <div className="p-3 border-b border-gray-800">
        <SeccionLabel>vista</SeccionLabel>
        <div className="flex gap-1">
          {VISTAS.map(v => (
            <button
              key={v.id}
              onClick={() => onVistaChange(v.id)}
              className={`flex-1 text-[11px] py-1 rounded transition-colors
                ${vista === v.id
                  ? 'bg-[#1D9E75] text-white border border-[#1D9E75]'
                  : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-500'
                }`}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filtros de detalle */}
      <div className="p-3 border-b border-gray-800">
        <SeccionLabel>mostrar</SeccionLabel>
        <div className="flex flex-col gap-1.5">
          {FILTROS.map(({ campo, label }) => (
            <label
              key={campo}
              className="flex items-center gap-2.5 cursor-pointer group"
              onClick={() => onFiltroChange(campo)}
            >
              {/* checkbox custom */}
              <span className={`w-3.5 h-3.5 rounded shrink-0 border flex items-center
                                justify-center text-[9px] transition-colors
                ${filtros[campo]
                  ? 'bg-[#1D9E75] border-[#1D9E75] text-white'
                  : 'bg-gray-800 border-gray-600 group-hover:border-gray-400'
                }`}>
                {filtros[campo] ? '✓' : ''}
              </span>
              <span className="text-[12px] text-gray-300 group-hover:text-gray-100
                               transition-colors">
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Filtro por librería */}
      <div className="p-3 border-b border-gray-800">
        <SeccionLabel>librería</SeccionLabel>
        <form onSubmit={_agregarLib} className="flex gap-1.5 mb-2">
          <input
            value={inputLib}
            onChange={e => setInputLib(e.target.value)}
            placeholder="mqtt, serial…"
            className="flex-1 text-[12px] px-2 py-1 rounded bg-gray-800
                       border border-gray-700 text-gray-200 placeholder-gray-600
                       outline-none focus:border-[#1D9E75] transition-colors"
          />
          <button
            type="submit"
            className="text-[11px] px-2 py-1 rounded border border-[#1D9E75]
                       text-[#1D9E75] hover:bg-[#1D9E75] hover:text-white transition-colors"
          >
            +
          </button>
        </form>

        {/* Tags activos */}
        {librerias.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {librerias.map(lib => (
              <button
                key={lib}
                onClick={() => onLibreriaRemove(lib)}
                title="Quitar filtro"
                className="text-[11px] px-2 py-0.5 rounded bg-[#E1F5EE] text-[#0F6E56]
                           border border-[#5DCAA5] hover:bg-red-100 hover:border-red-300
                           hover:text-red-600 transition-colors"
              >
                {lib} ×
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Spacer */}
      <div className="flex-1" />

    </div>
  )
}