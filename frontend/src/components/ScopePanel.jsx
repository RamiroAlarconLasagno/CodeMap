// frontend/src/components/ScopePanel.jsx
import { useState } from 'react'

function Checkbox({ checked, indeterminate = false }) {
  return (
    <span className={`w-3.5 h-3.5 rounded shrink-0 border flex items-center justify-center
                      text-[9px] transition-colors select-none
      ${checked
        ? 'bg-[#1D9E75] border-[#1D9E75] text-white'
        : indeterminate
          ? 'bg-[#1D9E75]/20 border-[#1D9E75]/50 text-[#1D9E75]'
          : 'bg-gray-800 border-gray-600'}`}>
      {checked ? '✓' : indeterminate ? '–' : ''}
    </span>
  )
}

function SeccionCarpeta({ carpeta, rutas, excluidos, onToggleArchivo, onToggleCarpeta }) {
  const [abierta, setAbierta] = useState(true)

  const activos = rutas.filter(r => !excluidos.has(r))
  const todosActivos = activos.length === rutas.length
  const algunoActivo = activos.length > 0
  const indeterminate = !todosActivos && algunoActivo

  return (
    <div className="mb-0.5">
      {/* Folder row */}
      <div className="flex items-center gap-1 px-3 py-1 hover:bg-gray-800/40 rounded">
        <button
          onClick={() => onToggleCarpeta(carpeta, !todosActivos)}
          className="flex items-center gap-2 flex-1 min-w-0 text-left"
        >
          <Checkbox checked={todosActivos} indeterminate={indeterminate} />
          <span className={`text-[11px] truncate transition-colors
            ${todosActivos || indeterminate ? 'text-gray-400' : 'text-gray-600'}`}>
            {carpeta}/
          </span>
        </button>
        <span className="text-[10px] text-gray-700 shrink-0 mr-1">
          {activos.length}/{rutas.length}
        </span>
        <button
          onClick={() => setAbierta(a => !a)}
          className="text-gray-600 text-[10px] w-4 shrink-0 hover:text-gray-400 transition-colors"
        >
          {abierta ? '▾' : '▸'}
        </button>
      </div>

      {/* Files */}
      {abierta && (
        <div className="ml-5 border-l border-gray-800/60 pl-2 mt-0.5">
          {rutas.map(ruta => {
            const nombre = ruta.split('/').pop()
            const activo = !excluidos.has(ruta)
            return (
              <button
                key={ruta}
                onClick={() => onToggleArchivo(ruta)}
                className="w-full flex items-center gap-2 px-2 py-0.5 hover:bg-gray-800/40
                           rounded text-left transition-colors"
              >
                <Checkbox checked={activo} />
                <span className={`text-[11px] font-mono truncate transition-colors
                  ${activo ? 'text-gray-300' : 'text-gray-600 line-through'}`}>
                  {nombre}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function ScopePanel({
  archivos, excluidos, onToggleArchivo, onToggleCarpeta, onToggleTodo,
}) {
  const todasRutas = Object.values(archivos).flat()
  const totalActivos = todasRutas.filter(r => !excluidos.has(r)).length
  const totalArchivos = todasRutas.length

  if (!totalArchivos) return (
    <div className="bg-gray-950 flex items-center justify-center h-full">
      <span className="text-gray-600 text-xs font-mono">Sin archivos indexados</span>
    </div>
  )

  return (
    <div className="bg-gray-950 overflow-y-auto flex flex-col font-mono">
      {/* Header sticky */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800
                      sticky top-0 bg-gray-950 z-10">
        <span className="text-[11px] text-gray-500">
          {totalActivos}
          <span className="text-gray-700"> / </span>
          {totalArchivos} archivos
        </span>
        <div className="flex-1" />
        <button
          onClick={() => onToggleTodo(true)}
          className="text-[10px] text-[#1D9E75] hover:text-[#1D9E75]/70 transition-colors"
        >
          todo
        </button>
        <span className="text-gray-700 text-[10px]">·</span>
        <button
          onClick={() => onToggleTodo(false)}
          className="text-[10px] text-gray-500 hover:text-gray-300 transition-colors"
        >
          ninguno
        </button>
      </div>

      {/* Folders */}
      <div className="py-2">
        {Object.entries(archivos).map(([carpeta, rutas]) => (
          <SeccionCarpeta
            key={carpeta}
            carpeta={carpeta}
            rutas={rutas}
            excluidos={excluidos}
            onToggleArchivo={onToggleArchivo}
            onToggleCarpeta={onToggleCarpeta}
          />
        ))}
      </div>
    </div>
  )
}
