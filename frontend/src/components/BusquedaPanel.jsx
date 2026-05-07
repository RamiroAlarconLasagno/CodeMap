// frontend/src/components/BusquedaPanel.jsx

const TIPO_BADGE = {
  clase:   { label: 'CLS', bg: 'bg-blue-900',   text: 'text-blue-300',   border: 'border-blue-700'   },
  metodo:  { label: 'MET', bg: 'bg-green-900',  text: 'text-green-300',  border: 'border-green-700'  },
  funcion: { label: 'FN',  bg: 'bg-purple-900', text: 'text-purple-300', border: 'border-purple-700' },
}

function mapToItem(r) {
  if (r.tipo === 'metodo') {
    const dot    = r.nombre.indexOf('.')
    const clase  = dot > -1 ? r.nombre.slice(0, dot)  : ''
    const nombre = dot > -1 ? r.nombre.slice(dot + 1) : r.nombre
    return { ...r, nombre, clase }
  }
  return r
}

function ResultadoFila({ r, onSeleccionar }) {
  const badge = TIPO_BADGE[r.tipo] ?? TIPO_BADGE.funcion
  const item  = mapToItem(r)

  return (
    <button
      onClick={() => onSeleccionar(item)}
      className="flex flex-col gap-0.5 px-3 py-2.5 border-b border-gray-800/60
                 text-left hover:bg-gray-800/50 transition-colors group w-full"
    >
      <div className="flex items-center gap-2">
        <span className={`text-[9px] px-1.5 py-0.5 rounded border shrink-0
                         ${badge.bg} ${badge.text} ${badge.border}`}>
          {badge.label}
        </span>
        <span className="text-[12px] text-gray-100 truncate group-hover:text-white">
          {r.nombre}
        </span>
      </div>

      {r.firma && (
        <div className="text-[10px] text-gray-500 truncate pl-8 font-mono">
          {r.firma}
        </div>
      )}

      {r.llama_a && (
        <div className="text-[10px] text-[#1D9E75]/80 truncate pl-8 font-mono">
          → {r.llama_a.join(', ')}
        </div>
      )}

      <div className="text-[10px] text-gray-600 truncate pl-8">
        {r.archivo}
        {r.linea != null && <span className="text-gray-700">:{r.linea}</span>}
      </div>
    </button>
  )
}

function SeccionHeader({ label, count }) {
  return (
    <div className="px-3 py-1.5 bg-gray-900/80 border-b border-gray-800
                    text-[10px] font-medium text-gray-500 uppercase tracking-widest
                    flex items-center justify-between shrink-0">
      <span>{label}</span>
      <span className="text-gray-700">{count}</span>
    </div>
  )
}

export default function BusquedaPanel({ resultados, patron, onSeleccionar }) {
  if (!patron) {
    return (
      <div className="flex items-center justify-center h-full text-gray-600 text-xs font-mono">
        escribe algo para buscar
      </div>
    )
  }

  if (!resultados.length) {
    return (
      <div className="flex items-center justify-center h-full text-gray-600 text-xs font-mono">
        sin resultados para &ldquo;{patron}&rdquo;
      </div>
    )
  }

  const definiciones = resultados.filter(r => (r.categoria ?? 'definicion') === 'definicion')
  const usos         = resultados.filter(r => r.categoria === 'uso')

  return (
    <div className="flex flex-col overflow-y-auto font-mono">

      {definiciones.length > 0 && (
        <>
          <SeccionHeader label="definiciones" count={definiciones.length} />
          {definiciones.map((r, i) => (
            <ResultadoFila key={`def-${i}`} r={r} onSeleccionar={onSeleccionar} />
          ))}
        </>
      )}

      {usos.length > 0 && (
        <>
          <SeccionHeader label="usados en" count={usos.length} />
          {usos.map((r, i) => (
            <ResultadoFila key={`uso-${i}`} r={r} onSeleccionar={onSeleccionar} />
          ))}
        </>
      )}

    </div>
  )
}
