// frontend/src/components/TopBar.jsx
// Placeholder — se reemplaza en Commit 4
export default function TopBar({ estado, cargando, onReanalizar, onCambiarCarpeta }) {
  return (
    <div className="flex items-center gap-3 px-4 h-full bg-gray-900 border-b border-gray-700 text-xs font-mono">
      <span className="text-accent font-medium">CodeMap</span>
      <span className="text-gray-500">{estado?.carpeta_raiz ?? '—'}</span>
      {cargando && <span className="text-gray-400 animate-pulse ml-auto">analizando...</span>}
    </div>
  )
}