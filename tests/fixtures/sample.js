// tests/fixtures/sample.js
// Fixture minimo para testear js_parser.py
// Cubre: imports ES, clase con herencia, constructor, metodos async,
//        arrow functions, variables de modulo, funciones sueltas.

import { EventEmitter } from 'events';
import logger from './logger.js';
import { leer, escribir } from './storage.js';

const VERSION = '2.0.0';
const MAX_ITEMS = 100;
let contadorGlobal = 0;

class Repositorio extends EventEmitter {
  #items;
  nombre;

  constructor(nombre) {
    super();
    this.nombre = nombre;
    this.#items = new Map();
  }

  get tamanio() {
    return this.#items.size;
  }

  async cargar(id) {
    const datos = await leer(id);
    this.#items.set(id, datos);
    this.emit('cargado', id);
    return datos;
  }

  guardar(id, valor) {
    this.#items.set(id, valor);
    this.emit('guardado', id);
  }

  limpiar() {
    this.#items.clear();
  }
}

class RepositorioCache extends Repositorio {
  #ttl;

  constructor(nombre, ttl = 60) {
    super(nombre);
    this.#ttl = ttl;
  }

  async cargar(id) {
    const cached = this.#items.get(id);
    if (cached) return cached;
    return super.cargar(id);
  }
}

const crearRepositorio = (nombre) => {
  return new Repositorio(nombre);
};

const procesarLote = async (ids, repositorio) => {
  const resultados = await Promise.all(ids.map(id => repositorio.cargar(id)));
  return resultados;
};

function formatearError(error) {
  return `[ERROR] ${error.message}`;
}

async function inicializar(config) {
  logger.info('Iniciando...');
  return crearRepositorio(config.nombre);
}