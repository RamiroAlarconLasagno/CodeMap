// frontend/src/components/ScopePanel.jsx
import { useState, useMemo } from 'react'

// ---------------------------------------------------------------------------
// Checkbox visual
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Construcción del árbol desde el dict plano { carpeta: [rutas] }
// ---------------------------------------------------------------------------

function buildTree(archivos) {
  const root = { name: '', fullPath: null, archivos: [], children: {} }

  for (const [carpeta, rutas] of Object.entries(archivos)) {
    if (carpeta === '.') {
      root.archivos.push(...rutas)
      continue
    }
    const parts = carpeta.split('/')
    let node = root
    let current = ''
    for (const part of parts) {
      current = current ? `${current}/${part}` : part
      if (!node.children[part]) {
        node.children[part] = { name: part, fullPath: current, archivos: [], children: {} }
      }
      node = node.children[part]
    }
    node.archivos.push(...rutas)
  }

  return root
}

function getAllRutas(node) {
  const acc = [...node.archivos]
  for (const child of Object.values(node.children)) {
    for (const r of getAllRutas(child)) acc.push(r)
  }
  return acc
}

// ---------------------------------------------------------------------------
// Nodo de carpeta — renderizado recursivo, indentación por border-l anidado
// ---------------------------------------------------------------------------

function NodoCarpeta({ node, excluidos, onToggleArchivo, onToggleCarpeta }) {
  const [abierta, setAbierta] = useState(true)

  const todasRutas   = getAllRutas(node)
  const nActivos     = todasRutas.filter(r => !excluidos.has(r)).length
  const todosActivos = nActivos === todasRutas.length
  const algunoActivo = nActivos > 0
  const expandible   = todasRutas.length > 0

  return (
    <div>
      {/* Cabecera de carpeta */}
      <div className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-gray-800/40 transition-colors">
        <button
          onClick={() => onToggleCarpeta(node.fullPath, !todosActivos)}
          className="flex items-center gap-2 flex-1 min-w-0 text-left"
        >
          <Checkbox checked={todosActivos} indeterminate={!todosActivos && algunoActivo} />
          <span className={`text-[11px] font-mono truncate transition-colors
            ${todosActivos || algunoActivo ? 'text-gray-400' : 'text-gray-600'}`}>
            {node.name}/
          </span>
        </button>
        <span className="text-[10px] text-gray-700 shrink-0 mr-0.5">
          {nActivos}/{todasRutas.length}
        </span>
        {expandible && (
          <button
            onClick={() => setAbierta(a => !a)}
            className="text-gray-600 text-[10px] w-4 shrink-0 hover:text-gray-400 transition-colors"
          >
            {abierta ? '▾' : '▸'}
          </button>
        )}
      </div>

      {/* Contenido: subcarpetas + archivos, indentados con border-l */}
      {abierta && (
        <div className="ml-3 border-l border-gray-800/50 pl-1">
          {/* Subcarpetas en orden alfabético */}
          {Object.entries(node.children)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([name, child]) => (
              <NodoCarpeta
                key={name}
                node={child}
                excluidos={excluidos}
                onToggleArchivo={onToggleArchivo}
                onToggleCarpeta={onToggleCarpeta}
              />
            ))}

          {/* Archivos directos en esta carpeta */}
          {node.archivos.map(ruta => {
            const nombre = ruta.split('/').pop()
            const activo = !excluidos.has(ruta)
            return (
              <button
                key={ruta}
                onClick={() => onToggleArchivo(ruta)}
                className="w-full flex items-center gap-2 pl-2 pr-2 py-0.5
                           hover:bg-gray-800/40 rounded text-left transition-colors"
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

// ---------------------------------------------------------------------------
// ScopePanel — raíz
// ---------------------------------------------------------------------------

export default function ScopePanel({
  archivos, excluidos, onToggleArchivo, onToggleCarpeta, onToggleTodo,
}) {
  const todasRutas    = Object.values(archivos).flat()
  const totalActivos  = todasRutas.filter(r => !excluidos.has(r)).length
  const totalArchivos = todasRutas.length

  const tree = useMemo(() => buildTree(archivos), [archivos])

  if (!totalArchivos) return (
    <div className="bg-gray-950 flex items-center justify-center h-full">
      <span className="text-gray-600 text-xs font-mono">Sin archivos indexados</span>
    </div>
  )

  return (
    <div className="bg-gray-950 overflow-y-auto flex flex-col font-mono">

      {/* Header sticky con contador y botones todo / ninguno */}
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

      {/* Árbol de carpetas */}
      <div className="py-2 px-2">
        {/* Archivos sueltos en la raíz ('.') */}
        {tree.archivos.map(ruta => {
          const nombre = ruta.split('/').pop()
          const activo = !excluidos.has(ruta)
          return (
            <button
              key={ruta}
              onClick={() => onToggleArchivo(ruta)}
              className="w-full flex items-center gap-2 px-2 py-0.5
                         hover:bg-gray-800/40 rounded text-left transition-colors"
            >
              <Checkbox checked={activo} />
              <span className={`text-[11px] font-mono truncate transition-colors
                ${activo ? 'text-gray-300' : 'text-gray-600 line-through'}`}>
                {nombre}
              </span>
            </button>
          )
        })}

        {/* Carpetas de primer nivel (orden alfabético) */}
        {Object.entries(tree.children)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([name, child]) => (
            <NodoCarpeta
              key={name}
              node={child}
              excluidos={excluidos}
              onToggleArchivo={onToggleArchivo}
              onToggleCarpeta={onToggleCarpeta}
            />
          ))}
      </div>

    </div>
  )
}
