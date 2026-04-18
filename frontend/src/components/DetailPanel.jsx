// frontend/src/components/DetailPanel.jsx
import { useState, useEffect } from 'react'
import { getMetodos, getLlamadas } from '../api/client.js'

// ---------------------------------------------------------------------------
// Colorizado de firma — resalta keywords, tipos y nombres
// ---------------------------------------------------------------------------

function FirmaColoreada({ firma }) {
  if (!firma) return null

  // Tokeniza la firma para colorizar partes clave
  const partes = firma.split(/(\bdef\b|\bclass\b|\basync\b|\bself\b|->|:\s*\w[\w.[\]|, ]*|=\s*[^,)]+)/)

  return (
    <code className="text-[12px] font-mono leading-relaxed whitespace-pre-wrap break-all">
      {firma.split('').reduce((acc, _char, i) => acc, null) && null}
      {/* Version simplificada — colores por patron */}
      {firma
        .replace(/\b(def|class|async|self|None|True|False)\b/g, '§KW§$1§/KW§')
        .replace(/(->|:)\s*([A-Za-z][\w[\]|, .]*)/g, '$1 §TY§$2§/TY§')
        .replace(/=\s*([^,)\n]+)/g, '= §DF§$1§/DF§')
        .split(/(§KW§.*?§\/KW§|§TY§.*?§\/TY§|§DF§.*?§\/DF§)/g)
        .map((parte, i) => {
          if (parte.startsWith('§KW§'))
            return <span key={i} className="text-purple-400">{parte.slice(4, -5)}</span>
          if (parte.startsWith('§TY§'))
            return <span key={i} className="text-blue-400">{parte.slice(4, -5)}</span>
          if (parte.startsWith('§DF§'))
            return <span key={i} className="text-orange-400">{parte.slice(4, -5)}</span>
          return <span key={i} className="text-gray-200">{parte}</span>
        })
      }
    </code>
  )
}

// ---------------------------------------------------------------------------
// Bloque con etiqueta
// ---------------------------------------------------------------------------

function Bloque({ label, children }) {
  return (
    <div className="border-b border-gray-800 px-4 py-3">
      <div className="text-[10px] font-medium text-gray-600 uppercase tracking-widest mb-2">
        {label}
      </div>
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Panel para CLASE
// ---------------------------------------------------------------------------

function DetalleClase({ item }) {
  const [metodos,  setMetodos]  = useState([])
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    let cancelado = false
    setCargando(true)
    getMetodos(item.nombre)
      .then(res => { if (!cancelado) setMetodos(res?.metodos ?? []) })
      .catch(() => {})
      .finally(() => { if (!cancelado) setCargando(false) })
    return () => { cancelado = true }
  }, [item.nombre])

  return (
    <>
      <Bloque label="firma">
        <FirmaColoreada firma={item.firma} />
      </Bloque>

      {item.docstring && (
        <Bloque label="docstring">
          <p className="text-[12px] text-gray-400 italic">"{item.docstring}"</p>
        </Bloque>
      )}

      {item.clases_base?.length > 0 && (
        <Bloque label="hereda de">
          <div className="flex flex-wrap gap-1.5">
            {item.clases_base.map(b => (
              <span key={b} className="text-[11px] px-2 py-0.5 rounded
                                       bg-blue-900/40 text-blue-300 border border-blue-800">
                {b}
              </span>
            ))}
          </div>
        </Bloque>
      )}

      {!cargando && metodos.length > 0 && (
        <Bloque label={`métodos (${metodos.length})`}>
          <div className="flex flex-col gap-0.5">
            {metodos.map(m => (
              <div key={m.nombre}
                   className="flex items-center gap-2 text-[12px] text-gray-300 py-0.5">
                <span className="text-[9px] px-1.5 py-0.5 rounded border
                                 bg-green-900 text-green-300 border-green-700 shrink-0">
                  MET
                </span>
                <span className="truncate font-mono">{m.nombre}</span>
                {m.es_async && (
                  <span className="text-[9px] text-purple-400 ml-auto shrink-0">async</span>
                )}
              </div>
            ))}
          </div>
        </Bloque>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Panel para METODO o FUNCION
// ---------------------------------------------------------------------------

function DetalleSimbolo({ item }) {
  const [llamadas, setLlamadas] = useState(item.llamadas ?? [])

  // Si el item viene del tree con llamadas ya cargadas no hace fetch extra
  useEffect(() => {
    if (item.llamadas?.length) { setLlamadas(item.llamadas); return }
    const simbolo = item.clase ? `${item.clase}.${item.nombre}` : item.nombre
    getLlamadas(simbolo)
      .then(res => setLlamadas(res?.llamadas ?? []))
      .catch(() => {})
  }, [item.nombre, item.clase])

  return (
    <>
      <Bloque label="firma">
        <FirmaColoreada firma={item.firma} />
      </Bloque>

      {item.docstring && (
        <Bloque label="docstring">
          <p className="text-[12px] text-gray-400 italic">"{item.docstring}"</p>
        </Bloque>
      )}

      {item.decoradores?.length > 0 && (
        <Bloque label="decoradores">
          {item.decoradores.map(d => (
            <div key={d} className="text-[12px] text-yellow-500 font-mono">@{d}</div>
          ))}
        </Bloque>
      )}

      {llamadas.length > 0 && (
        <Bloque label="llamadas">
          <div className="flex flex-col gap-1">
            {llamadas.map(l => (
              <div key={l} className="flex items-center gap-2 text-[12px] font-mono">
                <span className="text-[#1D9E75] shrink-0">→</span>
                <span className="text-gray-300 truncate">{l}</span>
              </div>
            ))}
          </div>
        </Bloque>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// Panel para VARIABLE
// ---------------------------------------------------------------------------

function DetalleVariable({ item }) {
  return (
    <>
      <Bloque label="tipo">
        <span className="text-[12px] font-mono text-blue-400">
          {item.tipo ?? 'sin tipo'}
        </span>
      </Bloque>
      {item.valor_inicial && (
        <Bloque label="valor inicial">
          <span className="text-[12px] font-mono text-orange-400">
            {item.valor_inicial}
          </span>
        </Bloque>
      )}
      <Bloque label="scope">
        <span className="text-[12px] font-mono text-gray-400">{item.scope}</span>
      </Bloque>
    </>
  )
}

// ---------------------------------------------------------------------------
// DetailPanel — raiz
// ---------------------------------------------------------------------------

export default function DetailPanel({ seleccionado, onNavegar }) {
  if (!seleccionado) {
    return (
      <div className="bg-[#0f1117] border-l border-gray-800 flex flex-col
                      items-center justify-center h-full gap-2">
        <span className="text-gray-600 text-xs font-mono">
          seleccioná un símbolo
        </span>
        <span className="text-gray-700 text-[11px]">
          clase · método · función · variable
        </span>
      </div>
    )
  }

  const { tipo, nombre, archivo, clase } = seleccionado

  // Subtitulo contextual
  const subtitulo = [
    tipo,
    clase ? `· ${clase}` : null,
    archivo ? `· ${archivo.split('/').pop()}` : null,
  ].filter(Boolean).join(' ')

  return (
    <div className="bg-[#0f1117] border-l border-gray-800 flex flex-col
                    overflow-hidden font-mono">

      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 shrink-0">
        <div className="text-[14px] font-medium text-gray-100 truncate">{nombre}</div>
        <div className="text-[11px] text-gray-500 mt-0.5 truncate">{subtitulo}</div>
      </div>

      {/* Contenido scrolleable */}
      <div className="flex-1 overflow-y-auto">
        {tipo === 'clase'    && <DetalleClase    item={seleccionado} />}
        {tipo === 'metodo'   && <DetalleSimbolo  item={seleccionado} />}
        {tipo === 'funcion'  && <DetalleSimbolo  item={seleccionado} />}
        {tipo === 'variable' && <DetalleVariable item={seleccionado} />}
      </div>

      {/* Footer — archivo completo */}
      <div className="px-4 py-2 border-t border-gray-800 shrink-0">
        <span className="text-[10px] text-gray-600 truncate block" title={archivo}>
          {archivo}
        </span>
      </div>

    </div>
  )
}