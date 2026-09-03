
import csv
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"


def leer_estudiantes(ruta: Path) -> list[dict]:
    """Lee el archivo CSV y devuelve una lista de diccionarios."""
    with open(ruta, encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector)


def transformar_estudiante(estudiante: dict) -> dict:
    """Transforma un estudiante al formato del panel académico."""
    return {
        "id": estudiante["codigo"],
        "nombre_completo": f'{estudiante["nombre"]} {estudiante["apellido"]}',
        "semestre": int(estudiante["semestre"]),
        "promedio": float(estudiante["promedio"]),
        "estado": (
            "Activo"
            if estudiante["activo"].lower() == "true"
            else "Inactivo"
        ),
    }


def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(
            estudiantes,
            archivo,
            indent=2,
            ensure_ascii=False
        )


def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


print("Hola, Aplicaciones y Servicios Web")


# Leer los estudiantes desde el CSV
estudiantes = leer_estudiantes(RUTA_CSV)


# Transformar todos los registros
estudiantes_transformados = [
    transformar_estudiante(estudiante)
    for estudiante in estudiantes
]


# Guardar los estudiantes transformados en JSON
serializar_estudiantes(RUTA_JSON, estudiantes_transformados)

print(f"Archivo JSON generado: {RUTA_JSON}")


# Deserializar el JSON generado
estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)

print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")

