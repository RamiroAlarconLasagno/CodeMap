// frontend/src/components/FileTree.jsx
// Placeholder — se reemplaza en Commit 5
export default function FileTree({ archivos, cargando, error }) {
  if (error)    return <div className="p-4 text-red-400 text-xs font-mono">{error}</div>
  if (cargando) return <div className="p-4 text-gray-400 text-xs font-mono animate-pulse">cargando...</div>
  const carpetas = Object.keys(archivos)
  if (!carpetas.length) return <div className="p-4 text-gray-600 text-xs font-mono">Sin archivos indexados.</div>
  return (
    <div className="bg-gray-950 overflow-y-auto p-3 text-xs font-mono text-gray-300">
      {carpetas.map(c => (
        <div key={c} className="mb-2">
          <div className="text-gray-500 mb-1">{c}/</div>
          {archivos[c].map(f => <div key={f} className="pl-3 text-gray-400">{f.split('/').pop()}</div>)}
        </div>
      ))}
    </div>
  )
}