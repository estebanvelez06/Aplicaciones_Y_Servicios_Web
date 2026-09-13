# Análisis final — Taller 1: Integración de datos entre aplicaciones


## 1. Diferencias encontradas entre los contratos de los proveedores

Los proveedores A y B entregan información meteorológica con estructuras y nombres de campos diferentes, por lo que fue necesario realizar una normalización antes de enviar los datos a la API institucional.

| Contrato institucional | Proveedor A | Proveedor B | Transformación |
|---|---|---|---|
| `ciudad` | `station.city_name` | `municipality` | Cambio de nombre y estructura |
| `pais` | `station.country_code` | `country` | Cambio de nombre |
| `latitud` | `location.lat` | `latitude_deg` | Conversión a número |
| `longitud` | `location.lon` | `longitude_deg` | Conversión a número |
| `temperatura_c` | `measurements.temperature_f` | `temp_celsius` | A: °F a °C |
| `humedad` | `measurements.relative_humidity` | `humidity_pct` | Cambio de nombre y conversión numérica |
| `viento_kmh` | `measurements.wind_speed_ms` | `wind_kmh` | A: m/s a km/h |
| `fecha_hora` | `observed_at` | `measurement_time` | Conversión al formato ISO 8601 |
| `origen` | No existe | No existe | Se asigna `proveedor_a` o `proveedor_b` |

La principal diferencia fue que el proveedor A utiliza estructuras anidadas y unidades diferentes para temperatura y velocidad del viento, mientras que el proveedor B utiliza una estructura más plana y una fecha con un formato diferente.

---

## 2. Transformaciones realizadas

Para adaptar los registros al contrato institucional se realizaron las siguientes transformaciones:

- Se cambiaron los nombres de los campos de cada proveedor por los definidos en el contrato institucional.
- Se convirtieron los valores numéricos a tipos `float`.
- La temperatura del proveedor A se convirtió de grados Fahrenheit a grados Celsius mediante:

  `°C = (°F - 32) × 5 / 9`

- La velocidad del viento del proveedor A se convirtió de metros por segundo a kilómetros por hora:

  `km/h = m/s × 3.6`

- La fecha del proveedor B se convirtió desde `DD/MM/YYYY HH:MM` a ISO 8601.
- A las fechas del proveedor B se les agregó la zona horaria `-05:00`, requerida por la API.
- Se asignó el valor correspondiente de `origen` a cada registro.
- Los identificadores originales de los proveedores se conservaron únicamente como identificadores internos de trazabilidad y no fueron enviados en el body de la API.

Como resultado, de los 400 registros procesados, 392 pudieron ser normalizados correctamente.

---

## 3. Tipos de errores encontrados antes de enviar información

Durante el procesamiento se encontraron errores de normalización y errores de validación local.

De los 400 registros procesados:

- 392 fueron normalizados correctamente.
- 8 presentaron errores de normalización.
- 380 registros fueron válidos para ser enviados a la API.
- 12 registros fueron rechazados durante la validación local.

Los errores de normalización corresponden a registros cuyos datos no pudieron convertirse correctamente al formato requerido.

Los errores de validación corresponden a registros que pudieron ser normalizados, pero que incumplían alguna regla del contrato institucional, por ejemplo restricciones sobre rangos numéricos o datos obligatorios.

También se presentó inicialmente un error en las fechas del proveedor B. Las fechas se estaban enviando como:

`2026-09-01T06:00:00`

La API rechazó estos registros porque la fecha debía incluir información de zona horaria. Se corrigió la normalización para generar valores como:

`2026-09-01T06:00:00-05:00`

Después de esta corrección, los registros fueron aceptados correctamente.

---

## 4. Diferencias entre la validación local y la validación del servidor

La validación local se realiza antes de enviar los datos a la API y permite detectar problemas que pueden comprobarse directamente en el cliente, como:

- campos obligatorios vacíos;
- valores numéricos incorrectos;
- latitudes fuera del rango permitido;
- longitudes fuera del rango permitido;
- humedad fuera del rango permitido;
- velocidad del viento negativa;
- fechas con formato inválido;
- valores de `origen` no permitidos.

La validación del servidor es independiente y puede aplicar reglas adicionales que no necesariamente son conocidas por el cliente.

Esto se evidenció durante el desarrollo con las fechas del proveedor B. Los registros podían superar la validación local de Python porque la fecha tenía una estructura ISO válida, pero la API los rechazaba porque no incluían la zona horaria.

Por esta razón, la validación local no reemplaza la validación realizada por el servidor.

---

## 5. Decisión de implementación más importante

La decisión de implementación más importante fue separar el proceso en funciones con responsabilidades específicas.

Se utilizaron funciones diferentes para:

- lectura de los proveedores;
- normalización;
- validación;
- envío de mediciones;
- reintentos;
- consulta de mediciones existentes;
- generación de claves para evitar duplicados.

Esta separación permitió identificar y corregir de manera independiente los problemas encontrados durante la integración.

También fue importante implementar el control de duplicados mediante una consulta previa a la API. De esta manera, los registros que ya estaban almacenados no fueron enviados nuevamente.

Para los errores de comunicación y respuestas `5xx` se implementaron hasta tres intentos por registro, mientras que las respuestas `4xx` no se reintentaron automáticamente, siguiendo las reglas del contrato.

---

## Evidencia de ejecución real

La ejecución final del integrador produjo los siguientes resultados:

| Resultado | Cantidad |
|---|---:|
| Registros procesados | 400 |
| Registros normalizados | 392 |
| Registros válidos localmente | 380 |
| Registros rechazados localmente | 12 |
| Registros aceptados por la API durante la ejecución | 190 |
| Registros que ya existían en la API | 190 |
| Registros rechazados por la API | 0 |
| Errores de comunicación | 0 |

Como evidencia de una respuesta recibida desde la API, durante la ejecución se obtuvo una respuesta HTTP 201 para los registros aceptados, indicando que la medición fue registrada correctamente. También se recibió inicialmente una respuesta HTTP 422 cuando las fechas del proveedor B no incluían zona horaria, situación que posteriormente fue corregida.
La suma de los registros aceptados durante la ejecución y los que ya existían en la API corresponde a todos los registros válidos:

`190 + 190 = 380`

Finalmente, se realizó la consulta mediante `GET /api/v1/mediciones?equipo=EQUIPO-04-APPSWEB`.

La API respondió:

- Código HTTP: `200`
- Total de mediciones registradas: `380`

Esto confirmó que los 380 registros válidos quedaron registrados correctamente en la API institucional.