# ==========================================
# INTEGRADOR DE DATOS ENTRE APLICACIONES
# ==========================================

import csv
import json
import requests
import time
from pathlib import Path
from datetime import datetime

# Configuración del API
URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-04-APPSWEB"


def leer_proveedor_a(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    return datos


def leer_proveedor_b(ruta):
    with open(ruta, "r", encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo, delimiter=";")
        datos = list(lector)

    return datos

def normalizar_proveedor_a(registro):
    try:
        temperatura_f = registro["measurements"]["temperature_f"]
        viento_ms = registro["measurements"]["wind_speed_ms"]
        fecha_hora = registro.get("observed_at")

        if not fecha_hora:
            raise ValueError("Falta la fecha y hora de medición.")

        temperatura_c = (float(temperatura_f) - 32) * 5 / 9
        viento_kmh = float(viento_ms) * 3.6

        normalizado = {
            "ciudad": registro["station"]["city_name"],
            "pais": registro["station"]["country_code"],
            "latitud": float(registro["location"]["lat"]),
            "longitud": float(registro["location"]["lon"]),
            "temperatura_c": temperatura_c,
            "humedad": float(registro["measurements"]["relative_humidity"]),
            "viento_kmh": viento_kmh,
            "fecha_hora": fecha_hora,
            "origen": "proveedor_a"
        }

        # Se conserva el ID original solamente para trazabilidad interna.
        id_trazabilidad = registro.get("provider_record_id")

        return normalizado, id_trazabilidad, None

    except (KeyError, TypeError, ValueError) as error:
        return None, registro.get("provider_record_id"), str(error)


def normalizar_proveedor_b(registro):
    try:
        fecha_hora = registro["measurement_time"]

        if not fecha_hora:
            raise ValueError("Falta la fecha y hora de medición.")

        fecha_hora_iso = datetime.strptime(
            fecha_hora,
            "%d/%m/%Y %H:%M"
        ).isoformat() + "-05:00"

        normalizado = {
            "ciudad": registro["municipality"],
            "pais": registro["country"],
            "latitud": float(registro["latitude_deg"]),
            "longitud": float(registro["longitude_deg"]),
            "temperatura_c": float(registro["temp_celsius"]),
            "humedad": float(registro["humidity_pct"]),
            "viento_kmh": float(registro["wind_kmh"]),
            "fecha_hora": fecha_hora_iso,
            "origen": "proveedor_b"
        }

        # Se conserva el ID original solamente para trazabilidad interna.
        id_trazabilidad = registro.get("record_code")

        return normalizado, id_trazabilidad, None

    except (KeyError, TypeError, ValueError) as error:
        return None, registro.get("record_code"), str(error)


def validar_registro(registro):
    errores = []

    # Validar ciudad
    if not isinstance(registro.get("ciudad"), str) or not registro["ciudad"].strip():
        errores.append("La ciudad es obligatoria.")

    # Validar país
    if not isinstance(registro.get("pais"), str) or not registro["pais"].strip():
        errores.append("El país es obligatorio.")

    # Validar latitud
    try:
        latitud = float(registro["latitud"])
        if not -90 <= latitud <= 90:
            errores.append("La latitud debe estar entre -90 y 90.")
    except (KeyError, TypeError, ValueError):
        errores.append("La latitud debe ser un número.")

    # Validar longitud
    try:
        longitud = float(registro["longitud"])
        if not -180 <= longitud <= 180:
            errores.append("La longitud debe estar entre -180 y 180.")
    except (KeyError, TypeError, ValueError):
        errores.append("La longitud debe ser un número.")

    # Validar temperatura
    try:
        float(registro["temperatura_c"])
    except (KeyError, TypeError, ValueError):
        errores.append("La temperatura debe ser un número.")

    # Validar humedad
    try:
        humedad = float(registro["humedad"])
        if not 0 <= humedad <= 100:
            errores.append("La humedad debe estar entre 0 y 100.")
    except (KeyError, TypeError, ValueError):
        errores.append("La humedad debe ser un número.")

    # Validar viento
    try:
        viento = float(registro["viento_kmh"])
        if viento < 0:
            errores.append("La velocidad del viento no puede ser negativa.")
    except (KeyError, TypeError, ValueError):
        errores.append("La velocidad del viento debe ser un número.")

    # Validar fecha y hora
    try:
        datetime.fromisoformat(registro["fecha_hora"])
    except (KeyError, TypeError, ValueError):
        errores.append("La fecha y hora no tienen un formato válido.")

    # Validar origen
    if registro.get("origen") not in ["proveedor_a", "proveedor_b"]:
        errores.append("El origen no es válido.")

    return errores

def enviar_medicion(registro):
    url = f"{URL_BASE}/api/v1/mediciones"

    headers = {
        "Content-Type": "application/json",
        "X-Equipo": EQUIPO
    }

    try:
        respuesta = requests.post(
            url,
            json=registro,
            headers=headers,
            timeout=10
        )

        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = {
                "respuesta": respuesta.text
            }

        return respuesta.status_code, contenido

    except requests.exceptions.Timeout as error:
        return None, {
          "error": f"{type(error).__name__}: {str(error)}"
        }

    except requests.exceptions.ConnectionError as error:
        return None, {
            "error": f"{type(error).__name__}: {str(error)}"
        }

    except requests.exceptions.RequestException as error:
        return None, {
            "error": str(error)
        }

def enviar_con_reintentos(registro, max_intentos=3):
    for intento in range(1, max_intentos + 1):
        codigo, respuesta = enviar_medicion(registro)

        # Registro aceptado
        if codigo == 201:
            return {
                "resultado": "aceptada",
                "codigo_http": codigo,
                "respuesta": respuesta,
                "intentos": intento
            }

        # Errores 4xx: no se reintentan
        if codigo is not None and 400 <= codigo < 500:
            return {
                "resultado": "rechazada_api",
                "codigo_http": codigo,
                "respuesta": respuesta,
                "intentos": intento
            }

        # Errores de comunicación o errores 5xx
        if codigo is None or codigo >= 500:
            if intento < max_intentos:
               espera = intento * 2

               print(
                   f"  Reintentando en {espera} segundos... "
                   f"intento {intento + 1}/{max_intentos}"
               )

               time.sleep(espera)

               continue

            return {
                "resultado": "error_comunicacion",
                "codigo_http": codigo,
                "respuesta": respuesta,
                "intentos": intento
            }

        # Código HTTP inesperado
        return {
            "resultado": "rechazada_api",
            "codigo_http": codigo,
            "respuesta": respuesta,
            "intentos": intento
        }  

def consultar_mediciones():
    url = f"{URL_BASE}/api/v1/mediciones"

    parametros = {
        "equipo": EQUIPO
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=10
        )

        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = {
                "respuesta": respuesta.text
            }

        return respuesta.status_code, contenido

    except requests.exceptions.Timeout:
        return None, {
            "error": "Timeout al consultar las mediciones."
        }

    except requests.exceptions.ConnectionError:
        return None, {
            "error": "Error de conexión al consultar las mediciones."
        }

    except requests.exceptions.RequestException as error:
        return None, {
            "error": str(error)
        }

def obtener_mediciones_existentes():
    """
    Consulta las mediciones que ya están registradas en la API.
    Devuelve un conjunto de registros para evitar duplicados.
    """

    codigo, respuesta = consultar_mediciones()

    if codigo != 200 or not isinstance(respuesta, dict):
        print("No fue posible consultar las mediciones existentes.")
        return set()

    mediciones = respuesta.get("mediciones", [])

    existentes = set()

    campos = [
        "ciudad",
        "pais",
        "latitud",
        "longitud",
        "temperatura_c",
        "humedad",
        "viento_kmh",
        "fecha_hora",
        "origen"
    ]

    for medicion in mediciones:
        registro = {
            campo: medicion.get(campo)
            for campo in campos
        }

        clave = json.dumps(
            registro,
            sort_keys=True,
            ensure_ascii=False
        )

        existentes.add(clave)

    return existentes


def generar_clave_registro(registro):
    """
    Genera una clave única usando únicamente
    los campos definidos por el contrato de la API.
    """

    campos = [
        "ciudad",
        "pais",
        "latitud",
        "longitud",
        "temperatura_c",
        "humedad",
        "viento_kmh",
        "fecha_hora",
        "origen"
    ]

    datos = {
        campo: registro.get(campo)
        for campo in campos
    }

    return json.dumps(
        datos,
        sort_keys=True,
        ensure_ascii=False
    )

def main():
    ruta_a = Path("datos/proveedor_a.json")
    ruta_b = Path("datos/proveedor_b.csv")

    # Lectura controlada del proveedor A
    try:
        proveedor_a = leer_proveedor_a(ruta_a)

    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {ruta_a}.")
        return

    except json.JSONDecodeError:
        print(f"Error: el archivo {ruta_a} no contiene un JSON válido.")
        return

    except OSError as error:
        print(f"Error al leer {ruta_a}: {error}")
        return

    # Lectura controlada del proveedor B
    try:
        proveedor_b = leer_proveedor_b(ruta_b)

    except FileNotFoundError:
        print(f"Error: no se encontró el archivo {ruta_b}.")
        return

    except csv.Error as error:
        print(f"Error: el archivo {ruta_b} contiene un problema de formato CSV: {error}")
        return

    except OSError as error:
        print(f"Error al leer {ruta_b}: {error}")
        return

    # Verificar que el JSON de A tenga la estructura esperada
    if not isinstance(proveedor_a, dict) or "records" not in proveedor_a:
        print(
            f"Error: el archivo {ruta_a} no contiene "
            "la estructura esperada de registros."
        )
        return

    print("Proveedor A leído correctamente.")
    print("Proveedor B leído correctamente.")

    print(f"Registros del proveedor A: {len(proveedor_a['records'])}")
    print(f"Registros del proveedor B: {len(proveedor_b)}")

    normalizados_a = []
    errores_a = []

    for registro in proveedor_a["records"]:
        normalizado, id_trazabilidad, error = normalizar_proveedor_a(registro)

        if error:
         errores_a.append({
            "id": id_trazabilidad,
            "error": error
         })
        else:
         normalizados_a.append({
            "id_trazabilidad": id_trazabilidad,
            "registro": normalizado
         })

    print("\n--- RESULTADO PROVEEDOR A ---")
    print(f"Registros procesados: {len(proveedor_a['records'])}")
    print(f"Registros normalizados: {len(normalizados_a)}")
    print(f"Errores de normalización: {len(errores_a)}")

    print("\nErrores encontrados:")
    for error in errores_a:
        print(error)

    normalizados_b = []
    errores_b = []

    for registro in proveedor_b:
        normalizado, id_trazabilidad, error = normalizar_proveedor_b(registro)

        if error:
            errores_b.append({
             "id": id_trazabilidad,
             "error": error
            })
        else:
            normalizados_b.append({
                "id_trazabilidad": id_trazabilidad,
                "registro": normalizado
            })

    print("\n--- RESULTADO PROVEEDOR B ---")
    print(f"Registros procesados: {len(proveedor_b)}")
    print(f"Registros normalizados: {len(normalizados_b)}")
    print(f"Errores de normalización: {len(errores_b)}")

    print("\nErrores encontrados en B:")
    for error in errores_b:
        print(error)

     # Combinar registros normalizados de ambos proveedores
    normalizados = normalizados_a + normalizados_b

        # Validar registros según el contrato de la API
    validos = []
    errores_validacion = []

    for item in normalizados:
        registro = item["registro"]
        id_trazabilidad = item["id_trazabilidad"]

        errores = validar_registro(registro)

        if errores:
            errores_validacion.append({
                "id_trazabilidad": id_trazabilidad,
                "registro": registro,
                "errores": errores
            })
        else:
            validos.append(item)

    print("\n--- VALIDACIÓN LOCAL ---")
    print(f"Registros normalizados: {len(normalizados)}")
    print(f"Registros válidos: {len(validos)}")
    print(f"Registros rechazados por validación: {len(errores_validacion)}")

    print("\nErrores de validación:")
    for error in errores_validacion:
        print(error)

    carpeta_salida = Path("salida")
    carpeta_salida.mkdir(exist_ok=True)

    # Guardar todos los registros normalizados
    # El ID de trazabilidad se conserva internamente,
    # pero no se incluye en el contrato normalizado.

    ruta_normalizadas = carpeta_salida / "normalizadas.json"

    registros_para_guardar = [
        item["registro"] for item in normalizados
    ]

    with open(ruta_normalizadas, "w", encoding="utf-8") as archivo:
        json.dump(
            registros_para_guardar,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print(f"\nArchivo generado: {ruta_normalizadas}")

    print("\n--- CONSULTANDO MEDICIONES EXISTENTES ---")

    mediciones_existentes = obtener_mediciones_existentes()

    print(
        f"Mediciones actualmente registradas en la API: "
        f"{len(mediciones_existentes)}"
    )

    print("\n--- ENVÍO A LA API ---")

    resultados_api = []

    omitidas = 0
    posicion_envio = 0

    for item in validos:

        registro = item["registro"]
        id_trazabilidad = item["id_trazabilidad"]

        clave = generar_clave_registro(registro)

        # Verificar si la medición ya existe
        if clave in mediciones_existentes:

            omitidas += 1

            print(
                f"[OMITIDA] {id_trazabilidad} -> "
                f"ya existe en la API"
            )

            resultados_api.append({
                "posicion": None,
                "id_trazabilidad": id_trazabilidad,
                "registro": registro,
                "resultado": "ya_existia_api",
                "codigo_http": None,
                "respuesta": {
                    "mensaje": "La medición ya estaba registrada en la API."
                },
                "intentos": 0
            })

            continue

        posicion_envio += 1

        resultado = enviar_con_reintentos(registro)

        resultados_api.append({
            "posicion": posicion_envio,
            "id_trazabilidad": id_trazabilidad,
            "registro": registro,
            "resultado": resultado["resultado"],
            "codigo_http": resultado["codigo_http"],
            "respuesta": resultado["respuesta"],
            "intentos": resultado["intentos"]
        })

        print(
            f"[{posicion_envio}] "
            f"{id_trazabilidad} -> "
            f"{resultado['resultado']} "
            f"(HTTP {resultado['codigo_http']})"
        )

        # Agregar el registro al conjunto si fue aceptado
        if resultado["resultado"] == "aceptada":
            mediciones_existentes.add(clave)

        # Pequeña pausa entre solicitudes
        time.sleep(0.3)
    
    print("\n--- CONSULTA FINAL AL API ---")

    codigo_get, respuesta_get = consultar_mediciones()

    print(f"GET /api/v1/mediciones?equipo={EQUIPO}")
    print(f"HTTP {codigo_get}")

    if codigo_get == 200:
        print("Consulta realizada correctamente.")

        if isinstance(respuesta_get, dict):
            print(f"Respuesta: {respuesta_get}")

    else:
        print(f"Error en la consulta: {respuesta_get}")

        # Generar reporte final
    aceptadas = sum(
        1 for resultado in resultados_api
        if resultado["resultado"] == "aceptada"
    )

    rechazadas_api = sum(
        1 for resultado in resultados_api
        if resultado["resultado"] == "rechazada_api"
    )

    errores_comunicacion = sum(
        1 for resultado in resultados_api
        if resultado["resultado"] == "error_comunicacion"
    )

    ya_existian = sum(
        1 for resultado in resultados_api
        if resultado["resultado"] == "ya_existia_api"
    )

    reporte = {
        "equipo": EQUIPO,
        "resumen": {
            "proveedor_a": {
                "procesados": len(proveedor_a["records"]),
                "normalizados": len(normalizados_a),
                "errores_normalizacion": len(errores_a)
            },
            "proveedor_b": {
                "procesados": len(proveedor_b),
                "normalizados": len(normalizados_b),
                "errores_normalizacion": len(errores_b)
            },
            "total": {
                "procesados": len(proveedor_a["records"]) + len(proveedor_b),
                "normalizados": len(normalizados),
                "validos_localmente": len(validos),
                "rechazados_validacion": len(errores_validacion),
                "aceptados_api": aceptadas,
                "rechazados_api": rechazadas_api,
                "errores_comunicacion": errores_comunicacion,
                "ya_existian_api": ya_existian
            }
        },
        "errores_normalizacion": {
            "proveedor_a": errores_a,
            "proveedor_b": errores_b
        },
        "errores_validacion": errores_validacion,
        "resultados_api": resultados_api,
        "consulta_get": {
            "codigo_http": codigo_get,
            "respuesta": respuesta_get
        }
    }

    ruta_reporte = carpeta_salida / "reporte.json"

    with open(ruta_reporte, "w", encoding="utf-8") as archivo:
        json.dump(
            reporte,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print(f"\nReporte generado: {ruta_reporte}")
       
if __name__ == "__main__":
    main()
