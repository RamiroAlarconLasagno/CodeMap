// frontend/src/components/DetailPanel.jsx
// Placeholder — se reemplaza en Commit 6
export default function DetailPanel({ seleccionado }) {
  return (
    <div className="bg-gray-900 border-l border-gray-700 p-4 text-xs font-mono text-gray-500">
      {seleccionado ? seleccionado.nombre : 'Selecciona un elemento'}
    </div>
  )
}