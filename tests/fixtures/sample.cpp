// tests/fixtures/sample.cpp
// Fixture representativo de firmware embebido / C++ moderno.
// Cubre: includes sistema y locales, defines, enum class, clase base
// con metodos inline, clase derivada, constructores con lista de
// inicializacion, funciones libres, variables globales con calificadores.

#include <Arduino.h>
#include <Wire.h>
#include <vector>
#include <memory>
#include "SensorADE9000.h"
#include "config.h"

#define HW_VERSION 3
#define MAX_LECTURAS 512
#define ID_DISPOSITIVO "ADE9000-A"

const int PIN_ALERTA = 4;
const float FACTOR_ESCALA = 0.001f;
static int total_instancias = 0;

enum class EstadoSensor {
    Inactivo,
    Calibrando,
    Activo,
    Error
};

class SensorBase {
public:
    String id;
    float ultimo_valor;
    bool habilitado;

    SensorBase(const String& id, bool habilitado = true) {
        this->id = id;
        this->habilitado = habilitado;
        this->ultimo_valor = 0.0f;
        total_instancias++;
        _inicializar();
    }

    virtual float leer() {
        if (!habilitado) return -1.0f;
        return ultimo_valor;
    }

    virtual void calibrar(float referencia) {
        ultimo_valor = referencia;
        estado = EstadoSensor::Calibrando;
    }

    bool estaActivo() const {
        return estado == EstadoSensor::Activo && habilitado;
    }

    static int contarInstancias() {
        return total_instancias;
    }

protected:
    EstadoSensor estado;

    void _inicializar() {
        estado = EstadoSensor::Inactivo;
        Wire.begin();
    }
};

class SensorADE9000 : public SensorBase {
public:
    int canal;
    float factor_calibracion;

    SensorADE9000(const String& id, int canal) : SensorBase(id) {
        this->canal = canal;
        this->factor_calibracion = FACTOR_ESCALA;
        _buffer.reserve(MAX_LECTURAS);
        configurarRegistros();
    }

    float leer() override {
        float raw = _leerADC();
        ultimo_valor = raw * factor_calibracion;
        estado = EstadoSensor::Activo;
        return ultimo_valor;
    }

    void calibrar(float referencia) override {
        SensorBase::calibrar(referencia);
        factor_calibracion = referencia / _leerADC();
    }

    std::vector<float> leerLote(int n) {
        std::vector<float> resultados;
        for (int i = 0; i < n && i < MAX_LECTURAS; i++) {
            resultados.push_back(leer());
            delay(10);
        }
        return resultados;
    }

private:
    std::vector<float> _buffer;

    float _leerADC() {
        Wire.beginTransmission(canal);
        Wire.write(0x00);
        Wire.endTransmission();
        return (float)Wire.read() * 0.01f;
    }

    void configurarRegistros() {
        Wire.beginTransmission(canal);
        Wire.write(HW_VERSION);
        Wire.endTransmission();
    }
};

float calcularPromedio(const std::vector<float>& valores) {
    if (valores.empty()) return 0.0f;
    float suma = 0.0f;
    for (const float& v : valores) suma += v;
    return suma / (float)valores.size();
}

float calcularRMS(const std::vector<float>& valores) {
    if (valores.empty()) return 0.0f;
    float suma_cuadrados = 0.0f;
    for (const float& v : valores) suma_cuadrados += v * v;
    return sqrt(suma_cuadrados / (float)valores.size());
}

void setup() {
    Serial.begin(115200);
    pinMode(PIN_ALERTA, OUTPUT);
    Wire.begin();
}

void loop() {
    delay(1000);
    digitalWrite(PIN_ALERTA, HIGH);
}