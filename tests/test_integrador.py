import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrador import (
    normalizar_proveedor_a,
    normalizar_proveedor_b,
    validar_registro
)


def test_normalizacion_proveedor_a():
    registro = {
        "station": {
            "city_name": "Medellín",
            "country_code": "CO"
        },
        "location": {
            "lat": 6.25,
            "lon": -75.56
        },
        "measurements": {
            "temperature_f": 77,
            "relative_humidity": 60,
            "wind_speed_ms": 5
        },
        "observed_at": "2026-09-01T10:00:00-05:00",
        "provider_record_id": "TEST-A-001"
    }

    normalizado, id_trazabilidad, error = normalizar_proveedor_a(registro)

    assert error is None
    assert id_trazabilidad == "TEST-A-001"
    assert normalizado["ciudad"] == "Medellín"
    assert normalizado["pais"] == "CO"


def test_conversion_temperatura_fahrenheit_a_celsius():
    registro = {
        "station": {
            "city_name": "Medellín",
            "country_code": "CO"
        },
        "location": {
            "lat": 6.25,
            "lon": -75.56
        },
        "measurements": {
            "temperature_f": 77,
            "relative_humidity": 60,
            "wind_speed_ms": 5
        },
        "observed_at": "2026-09-01T10:00:00-05:00",
        "provider_record_id": "TEST-A-002"
    }

    normalizado, _, error = normalizar_proveedor_a(registro)

    assert error is None
    assert normalizado["temperatura_c"] == 25.0


def test_conversion_viento_ms_a_kmh():
    registro = {
        "station": {
            "city_name": "Medellín",
            "country_code": "CO"
        },
        "location": {
            "lat": 6.25,
            "lon": -75.56
        },
        "measurements": {
            "temperature_f": 77,
            "relative_humidity": 60,
            "wind_speed_ms": 10
        },
        "observed_at": "2026-09-01T10:00:00-05:00",
        "provider_record_id": "TEST-A-003"
    }

    normalizado, _, error = normalizar_proveedor_a(registro)

    assert error is None
    assert normalizado["viento_kmh"] == 36.0


def test_registro_valido():
    registro = {
        "ciudad": "Medellín",
        "pais": "CO",
        "latitud": 6.25,
        "longitud": -75.56,
        "temperatura_c": 25.0,
        "humedad": 60,
        "viento_kmh": 20,
        "fecha_hora": "2026-09-01T10:00:00-05:00",
        "origen": "proveedor_a"
    }

    errores = validar_registro(registro)

    assert errores == []


def test_registro_invalido():
    registro = {
        "ciudad": "",
        "pais": "CO",
        "latitud": 200,
        "longitud": -75.56,
        "temperatura_c": 25.0,
        "humedad": 150,
        "viento_kmh": -10,
        "fecha_hora": "fecha-invalida",
        "origen": "proveedor_a"
    }

    errores = validar_registro(registro)

    assert len(errores) > 0
    assert "La ciudad es obligatoria." in errores
    assert "La latitud debe estar entre -90 y 90." in errores
    assert "La humedad debe estar entre 0 y 100." in errores
    assert "La velocidad del viento no puede ser negativa." in errores
    assert "La fecha y hora no tienen un formato válido." in errores


def test_caso_limite_humedad():
    registro = {
        "ciudad": "Medellín",
        "pais": "CO",
        "latitud": 6.25,
        "longitud": -75.56,
        "temperatura_c": 25.0,
        "humedad": 100,
        "viento_kmh": 0,
        "fecha_hora": "2026-09-01T10:00:00-05:00",
        "origen": "proveedor_a"
    }

    errores = validar_registro(registro)

    assert errores == []