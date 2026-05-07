// tests/fixtures/sample.js
// Fixture representativo de un proyecto React/Node real.
// Cubre: imports named/default/bare/type, dos clases con herencia,
// private fields (#), getters, metodos async, arrow functions de modulo,
// funciones sueltas, variables const/let/var, atributos TS con modificadores.

import { useState, useCallback, useRef } from 'react';
import axios, { AxiosError } from 'axios';
import type { RequestConfig, ResponseData } from './types.js';
import 'reflect-metadata';

export const BASE_URL = 'https://api.ejemplo.com/v2';
const TIMEOUT_MS = 8000;
let _instancia = null;
var _modo_debug = false;

export class ApiClient {
  static #instancia = null;
  #baseUrl;
  timeout;
  headers;

  constructor(baseUrl, opciones = {}) {
    this.#baseUrl = baseUrl;
    this.timeout = opciones.timeout ?? TIMEOUT_MS;
    this.headers = { 'Content-Type': 'application/json', ...opciones.headers };
    this._interceptores = [];
  }

  static getInstance() {
    if (!ApiClient.#instancia) {
      ApiClient.#instancia = new ApiClient(BASE_URL);
    }
    return ApiClient.#instancia;
  }

  get baseUrl() {
    return this.#baseUrl;
  }

  async get(endpoint, params = {}) {
    const url = construirUrl(this.#baseUrl, endpoint);
    const respuesta = await axios.get(url, { params, timeout: this.timeout });
    return normalizar(respuesta.data);
  }

  async post(endpoint, cuerpo) {
    const respuesta = await axios.post(
      construirUrl(this.#baseUrl, endpoint),
      cuerpo,
      { headers: this.headers, timeout: this.timeout }
    );
    return normalizar(respuesta.data);
  }

  agregarInterceptor(fn) {
    this._interceptores.push(fn);
  }
}

export class ApiClientAutenticado extends ApiClient {
  #token;
  #renovarToken;

  constructor(baseUrl, token, renovarToken) {
    super(baseUrl, { headers: { Authorization: `Bearer ${token}` } });
    this.#token = token;
    this.#renovarToken = renovarToken;
  }

  async get(endpoint, params = {}) {
    try {
      return await super.get(endpoint, params);
    } catch (e) {
      if (e instanceof AxiosError && e.response?.status === 401) {
        this.#token = await this.#renovarToken();
        return super.get(endpoint, params);
      }
      throw e;
    }
  }
}

export function construirUrl(base, path) {
  return `${base}/${path}`.replace(/\/+/g, '/').replace(':/', '://');
}

function normalizar(datos) {
  if (!datos) return null;
  if (Array.isArray(datos)) return datos.map(normalizar);
  return { ...datos, _normalizado: true };
}

export const useApiClient = (config) => {
  const clienteRef = useRef(null);
  const [cargando, setCargando] = useState(false);

  const ejecutar = useCallback(async (endpoint) => {
    setCargando(true);
    try {
      if (!clienteRef.current) {
        clienteRef.current = new ApiClientAutenticado(
          config.url, config.token, config.renovar
        );
      }
      return await clienteRef.current.get(endpoint);
    } finally {
      setCargando(false);
    }
  }, [config]);

  return { ejecutar, cargando };
};

const manejarError = (error) => {
  if (error instanceof AxiosError) {
    return { codigo: error.response?.status ?? 0, mensaje: error.message };
  }
  return { codigo: -1, mensaje: String(error) };
};