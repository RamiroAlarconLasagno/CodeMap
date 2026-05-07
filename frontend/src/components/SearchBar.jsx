// frontend/src/components/SearchBar.jsx
export default function SearchBar({ valor, onChange, placeholder = 'buscar… (* y ? soportados)' }) {
  return (
    <div className="relative">
      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-600 text-[11px]
                       pointer-events-none select-none">
        ⌕
      </span>
      <input
        type="text"
        value={valor}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full text-[12px] font-mono pl-7 pr-3 py-1.5 rounded
                   bg-gray-800 border border-gray-700 text-gray-200
                   placeholder-gray-600 outline-none
                   focus:border-[#1D9E75] transition-colors"
      />
      {valor && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-600
                     hover:text-gray-400 text-[11px]"
        >
          ✕
        </button>
      )}
    </div>
  )
}