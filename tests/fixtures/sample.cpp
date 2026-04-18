// tests/fixtures/sample.cpp
// Fixture minimo para testear c_parser.py
// Cubre: includes, defines, clase con herencia, constructor,
//        metodos virtuales, enum class, funciones sueltas, variables globales.

#include <iostream>
#include <vector>
#include <memory>
#include "sensor.h"

#define VERSION_MAYOR 2
#define MAX_BUFFER 1024
#define NOMBRE_APP "CodeMap"

const int TIMEOUT_MS = 5000;
static int instancias = 0;

enum class EstadoSensor { Activo, Inactivo, Error };

class Sensor {
public:
    std::string id;
    double ultimo_valor;

    Sensor(const std::string& id);
    virtual ~Sensor() = default;

    virtual double leer();
    virtual std::string toString() const;
    bool estaActivo() const;

protected:
    EstadoSensor estado;

private:
    void _inicializar();
};

Sensor::Sensor(const std::string& id) : id(id), estado(EstadoSensor::Activo) {
    ultimo_valor = 0.0;
    instancias++;
    _inicializar();
}

double Sensor::leer() {
    return ultimo_valor;
}

std::string Sensor::toString() const {
    return "Sensor(" + id + ")";
}

bool Sensor::estaActivo() const {
    return estado == EstadoSensor::Activo;
}

void Sensor::_inicializar() {
    ultimo_valor = -1.0;
}

class SensorADE9000 : public Sensor {
public:
    int canal;

    SensorADE9000(const std::string& id, int canal);
    double leer() override;

private:
    std::vector<double> _buffer;
};

SensorADE9000::SensorADE9000(const std::string& id, int canal)
    : Sensor(id), canal(canal) {
    _buffer.reserve(MAX_BUFFER);
}

double SensorADE9000::leer() {
    return Sensor::leer() * 1000.0;
}

double promedio(const std::vector<double>& valores) {
    if (valores.empty()) return 0.0;
    double suma = 0.0;
    for (const auto& v : valores) suma += v;
    return suma / valores.size();
}

std::string formatear(const Sensor& s) {
    return s.toString();
}