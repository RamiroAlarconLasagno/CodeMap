// tests/fixtures/sample.dart
// Fixture minimo para testear dart_parser.py
// Cubre: imports, clase con herencia, mixin, enum, constructor,
//        metodos async, atributos, funciones sueltas, variables de modulo.

import 'package:flutter/material.dart';
import 'dart:async' as async show Future, Stream;
import 'package:http/http.dart' show get, post;

const String VERSION = '1.0.0';
final int MAX_REINTENTOS = 3;

enum EstadoConexion { conectado, desconectado, error }

mixin LoggableMixin {
  void registrar(String mensaje) {
    print(mensaje);
  }
}

class Sensor extends ChangeNotifier with LoggableMixin {
  final String id;
  late double _ultimo_valor;
  static int _instancias = 0;

  Sensor(this.id) {
    _instancias++;
    _ultimo_valor = 0.0;
  }

  Sensor.simulado(String id) : this(id) {
    _ultimo_valor = -1.0;
  }

  double get ultimoValor => _ultimo_valor;

  Future<double> leer() async {
    final resultado = await _fetch();
    notifyListeners();
    return resultado;
  }

  Future<double> _fetch() async {
    return 42.0;
  }

  @override
  String toString() => 'Sensor($id)';
}

class SensorTemperatura extends Sensor {
  final String unidad;

  SensorTemperatura(String id, {this.unidad = 'C'}) : super(id);

  @override
  Future<double> leer() async {
    final raw = await super.leer();
    return unidad == 'F' ? raw * 9 / 5 + 32 : raw;
  }
}

Future<void> inicializar(String ruta) async {
  await Future.delayed(Duration(seconds: 1));
  print('Inicializado: $ruta');
}

Map<String, dynamic> parsearConfig(String texto) {
  return {};
}