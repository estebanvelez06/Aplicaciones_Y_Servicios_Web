Clase 4 — Datos e interacción entre aplicaciones

Esta práctica consiste en leer un archivo CSV de estudiantes, transformar sus datos utilizando Python y generar un archivo JSON.

Flujo

estudiantes.csv → Python → transformación → estudiantes_resumen.json

Tecnologías utilizadas
Python 3
csv
json
pathlib
Ejecución

Para ejecutar el programa:

python transformar_estudiantes.py

El programa lee los estudiantes del archivo CSV, transforma los registros, genera el archivo JSON y posteriormente deserializa el JSON para mostrar el primer estudiante y el total de registros.