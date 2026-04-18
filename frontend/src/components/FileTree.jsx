// frontend/src/components/FileTree.jsx
import { useState, useEffect } from 'react'
import { getClases, getFunciones, getVariables } from '../api/client.js'

// ---------------------------------------------------------------------------
// Badges de tipo
// ---------------------------------------------------------------------------

const BADGE = {
  clase:   { label: 'CLASE', cls: 'bg-blue-900 text-blue-300 border-blue-700' },
  metodo:  { label: 'MET',   cls: 'bg-green-900 text-green-300 border-green-700' },
  funcion: { label: 'FUN',   cls: 'bg-yellow-900 text-yellow-300 border-yellow-700' },
  variable:{ label: 'VAR',   cls: 'bg-gray-800 text-gray-400 border-gray-600' },
}

function Badge({ tipo }) {
  const b = BADGE[tipo] ?? BADGE.variable
  return (
    <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded border
                      shrink-0 leading-none ${b.cls}`}>
      {b.label}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Fila de simbolo individual
// ---------------------------------------------------------------------------

function FilaSimbol({ tipo, nombre, firma, docstring, esAsync, seleccionado, onClick }) {
  const activo = seleccionado?.nombre === nombre && seleccionado?.tipo === tipo
  return (
    <div
      onClick={onClick}
      className={`flex items-start gap-2 px-3 py-1.5 cursor-pointer rounded mx-1
                  transition-colors group
                  ${activo
                    ? 'bg-[#1D9E75]/20 border border-[#1D9E75]/40'
                    : 'hover:bg-gray-800/60 border border-transparent'}`}
    >
      <Badge tipo={tipo} />
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          {esAsync && (
            <span className="text-[9px] text-purple-400 border border-purple-800
                             px-1 rounded">async</span>
          )}
          <span className={`text-[12px] truncate
                            ${activo ? 'text-[#1D9E75]' : 'text-gray-200'}`}>
            {nombre}
          </span>
        </div>
        {firma && (
          <div className="text-[11px] text-gray-500 truncate font-mono mt-0.5">
            {firma}
          </div>
        )}
        {docstring && (
          <div className="text-[11px] text-gray-600 italic truncate mt-0.5">
            "{docstring}"
          </div>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Bloque de un archivo (colapsable)
// ---------------------------------------------------------------------------

function BloqueArchivo({ rutaArchivo, filtros, seleccionado, onSeleccionar }) {
  const [abierto,   setAbierto]   = useState(true)
  const [clases,    setClases]    = useState([])
  const [funciones, setFunciones] = useState([])
  const [variables, setVariables] = useState([])
  const [cargando,  setCargando]  = useState(false)

  // Nombre corto para mostrar en el header
  const partes    = rutaArchivo.split('/')
  const nombreArchivo = partes.pop()
  const carpeta   = partes.join('/') || '.'

  useEffect(() => {
    let cancelado = false
    async function cargar() {
      setCargando(true)
      try {
        const [resClases, resFunciones, resVars] = await Promise.all([
          getClases(rutaArchivo),
          getFunciones(rutaArchivo),
          filtros.variables ? getVariables(rutaArchivo, 'modulo') : Promise.resolve({}),
        ])
        if (cancelado) return
        setClases(resClases[rutaArchivo]    ?? [])
        setFunciones(resFunciones[rutaArchivo] ?? [])
        setVariables(resVars[rutaArchivo]   ?? [])
      } catch {
        // Archivo sin simbolos indexados — normal para algunos archivos
      } finally {
        if (!cancelado) setCargando(false)
      }
    }
    cargar()
    return () => { cancelado = true }
  }, [rutaArchivo, filtros.variables])

  const totalSimbolos = clases.length + funciones.length + variables.length

  return (
    <div className="mb-1">
      {/* Header del archivo */}
      <button
        onClick={() => setAbierto(a => !a)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-left
                   hover:bg-gray-800/40 rounded transition-colors group"
      >
        <span className="text-gray-600 text-[10px] w-3 shrink-0">
          {abierto ? '▾' : '▸'}
        </span>
        <span className="text-[10px] text-gray-600 truncate">{carpeta}/</span>
        <span className="text-[12px] text-gray-300 font-medium truncate">
          {nombreArchivo}
        </span>
        {cargando && (
          <span className="ml-auto text-[10px] text-gray-600 animate-pulse">…</span>
        )}
        {!cargando && totalSimbolos > 0 && (
          <span className="ml-auto text-[10px] text-gray-600">{totalSimbolos}</span>
        )}
      </button>

      {/* Contenido colapsable */}
      {abierto && (
        <div className="ml-2">
          {/* Clases */}
          {clases.map(cls => (
            <div key={cls.nombre}>
              <FilaSimbol
                tipo="clase"
                nombre={cls.nombre}
                firma={filtros.firmas ? cls.firma : null}
                docstring={filtros.docstrings ? cls.docstring : null}
                seleccionado={seleccionado}
                onClick={() => onSeleccionar({
                  tipo: 'clase', nombre: cls.nombre,
                  archivo: rutaArchivo, ...cls,
                })}
              />
              {/* Metodos de la clase si filtros.firmas activo */}
              {filtros.firmas && cls.total_metodos > 0 && (
                <MetodosClase
                  nombreClase={cls.nombre}
                  archivo={rutaArchivo}
                  filtros={filtros}
                  seleccionado={seleccionado}
                  onSeleccionar={onSeleccionar}
                />
              )}
            </div>
          ))}

          {/* Funciones sueltas */}
          {funciones.map(fn => (
            <FilaSimbol
              key={fn.nombre}
              tipo="funcion"
              nombre={fn.nombre}
              firma={filtros.firmas ? fn.firma : null}
              docstring={filtros.docstrings ? fn.docstring : null}
              esAsync={fn.es_async}
              seleccionado={seleccionado}
              onClick={() => onSeleccionar({
                tipo: 'funcion', nombre: fn.nombre,
                archivo: rutaArchivo, ...fn,
              })}
            />
          ))}

          {/* Variables de modulo */}
          {filtros.variables && variables.map(v => (
            <FilaSimbol
              key={v.nombre}
              tipo="variable"
              nombre={v.nombre}
              firma={v.tipo ? `${v.nombre}: ${v.tipo}` : null}
              seleccionado={seleccionado}
              onClick={() => onSeleccionar({
                tipo: 'variable', nombre: v.nombre,
                archivo: rutaArchivo, ...v,
              })}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sub-componente: metodos de una clase (carga lazy)
// ---------------------------------------------------------------------------

function MetodosClase({ nombreClase, archivo, filtros, seleccionado, onSeleccionar }) {
  const [metodos,  setMetodos]  = useState([])
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    let cancelado = false
    async function cargar() {
      setCargando(true)
      try {
        const { getMetodos } = await import('../api/client.js')
        const res = await getMetodos(nombreClase)
        if (!cancelado) setMetodos(res?.metodos ?? [])
      } catch {
        // clase sin metodos
      } finally {
        if (!cancelado) setCargando(false)
      }
    }
    cargar()
    return () => { cancelado = true }
  }, [nombreClase])

  if (cargando) return null

  return (
    <div className="ml-3 border-l border-gray-800 pl-2">
      {metodos.map(m => (
        <FilaSimbol
          key={m.nombre}
          tipo="metodo"
          nombre={m.nombre}
          firma={filtros.firmas ? m.firma : null}
          docstring={filtros.docstrings ? m.docstring : null}
          esAsync={m.es_async}
          seleccionado={seleccionado}
          onClick={() => onSeleccionar({
            tipo: 'metodo', nombre: m.nombre,
            clase: nombreClase, archivo, ...m,
          })}
        />
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// FileTree — componente raiz
// ---------------------------------------------------------------------------

export default function FileTree({
  archivos, filtros, seleccionado, onSeleccionar, cargando, error,
}) {
  if (error) return (
    <div className="bg-gray-950 p-4 text-red-400 text-xs font-mono">{error}</div>
  )

  if (cargando && !Object.keys(archivos).length) return (
    <div className="bg-gray-950 p-4 text-gray-500 text-xs font-mono animate-pulse">
      cargando índice…
    </div>
  )

  // Construir lista plana de archivos desde el arbol { carpeta: [archivo] }
  const rutasArchivos = Object.values(archivos).flat()

  if (!rutasArchivos.length) return (
    <div className="bg-gray-950 p-6 flex flex-col items-center justify-center h-full gap-2">
      <span className="text-gray-600 text-xs font-mono">Sin archivos indexados</span>
      <span className="text-gray-700 text-[11px]">
        Usá ↻ reanalizar o cambiá la carpeta
      </span>
    </div>
  )

  return (
    <div className="bg-gray-950 overflow-y-auto py-2">
      {rutasArchivos.map(ruta => (
        <BloqueArchivo
          key={ruta}
          rutaArchivo={ruta}
          filtros={filtros}
          seleccionado={seleccionado}
          onSeleccionar={onSeleccionar}
        />
      ))}
    </div>
  )
}