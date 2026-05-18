"""
Crea los equipos de la Liga BetPlay en la API.
Usa los logos descargados por download_logos.py si existen en tests/logos_equipos/.

Uso: python tests/crear_equipos.py
     python tests/crear_equipos.py --url http://localhost:8000
"""

import httpx
import argparse
import unicodedata
from pathlib import Path

BASE_URL = "http://localhost:8000"
LOGOS_DIR = Path(__file__).parent / "logos_equipos"

EQUIPOS = [
    {"nombre": "Atlético Nacional",       "ciudad": "Medellín",       "estadio": "Estadio Atanasio Girardot",              "anio_fundacion": 1947, "titulos": 16},
    {"nombre": "Millonarios FC",          "ciudad": "Bogotá",         "estadio": "Estadio El Campín",                      "anio_fundacion": 1946, "titulos": 15},
    {"nombre": "América de Cali",         "ciudad": "Cali",           "estadio": "Estadio Olímpico Pascual Guerrero",      "anio_fundacion": 1927, "titulos": 13},
    {"nombre": "Deportivo Cali",          "ciudad": "Cali",           "estadio": "Estadio Deportivo Cali",                 "anio_fundacion": 1912, "titulos": 9},
    {"nombre": "Junior FC",               "ciudad": "Barranquilla",   "estadio": "Estadio Metropolitano Roberto Meléndez", "anio_fundacion": 1924, "titulos": 8},
    {"nombre": "Independiente Santa Fe",  "ciudad": "Bogotá",         "estadio": "Estadio El Campín",                      "anio_fundacion": 1941, "titulos": 9},
    {"nombre": "Deportes Tolima",         "ciudad": "Ibagué",         "estadio": "Estadio Manuel Murillo Toro",            "anio_fundacion": 1954, "titulos": 4},
    {"nombre": "Once Caldas",             "ciudad": "Manizales",      "estadio": "Estadio Palogrande",                     "anio_fundacion": 1961, "titulos": 4},
    {"nombre": "Independiente Medellín",  "ciudad": "Medellín",       "estadio": "Estadio Atanasio Girardot",              "anio_fundacion": 1913, "titulos": 5},
    {"nombre": "Deportivo Pereira",       "ciudad": "Pereira",        "estadio": "Estadio Hernán Ramírez Villegas",        "anio_fundacion": 1944, "titulos": 1},
    {"nombre": "Atlético Bucaramanga",    "ciudad": "Bucaramanga",    "estadio": "Estadio Alfonso López",                  "anio_fundacion": 1949, "titulos": 1},
    {"nombre": "Boyacá Chicó",            "ciudad": "Tunja",          "estadio": "Estadio La Independencia",               "anio_fundacion": 2003, "titulos": 2},
    {"nombre": "Jaguares de Córdoba",     "ciudad": "Montería",       "estadio": "Estadio Jaraguay",                       "anio_fundacion": 2013, "titulos": 0},
    {"nombre": "Alianza FC",              "ciudad": "Valledupar",     "estadio": "Estadio Sierra Nevada",                  "anio_fundacion": 2017, "titulos": 0},
    {"nombre": "Llaneros FC",             "ciudad": "Villavicencio",  "estadio": "Estadio Bello Horizonte",                "anio_fundacion": 2012, "titulos": 0},
    {"nombre": "Fortaleza FC",            "ciudad": "Bogotá",         "estadio": "Estadio Metropolitano de Techo",         "anio_fundacion": 2015, "titulos": 0},
    {"nombre": "Águilas Doradas",         "ciudad": "Rionegro",       "estadio": "Estadio Alberto Grisales",               "anio_fundacion": 1994, "titulos": 0},
    {"nombre": "Internacional de Bogotá", "ciudad": "Bogotá",         "estadio": "Estadio Metropolitano de Techo",         "anio_fundacion": 2019, "titulos": 0},
    {"nombre": "Cúcuta Deportivo",        "ciudad": "Cúcuta",         "estadio": "Estadio General Santander",              "anio_fundacion": 1924, "titulos": 1},
    {"nombre": "Deportivo Pasto",         "ciudad": "Pasto",          "estadio": "Estadio Departamental Libertad",         "anio_fundacion": 1949, "titulos": 0},
]


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower().replace(" ", "_")


def buscar_logo(nombre: str) -> Path | None:
    if not LOGOS_DIR.exists():
        return None
    nombre_norm = normalizar(nombre)
    for archivo in LOGOS_DIR.iterdir():
        if normalizar(archivo.stem) == nombre_norm:
            return archivo
    # Búsqueda parcial
    for archivo in LOGOS_DIR.iterdir():
        stem_norm = normalizar(archivo.stem)
        palabras = nombre_norm.split("_")
        if all(p in stem_norm for p in palabras if len(p) > 3):
            return archivo
    return None


def crear_equipo(client: httpx.Client, equipo: dict, url: str) -> bool:
    logo_path = buscar_logo(equipo["nombre"])

    data = {
        "nombre":          equipo["nombre"],
        "ciudad":          equipo["ciudad"],
        "estadio":         equipo["estadio"],
        "anio_fundacion":  str(equipo["anio_fundacion"]),
        "titulos":         str(equipo["titulos"]),
    }

    if logo_path:
        with open(logo_path, "rb") as f:
            files = {"file": (logo_path.name, f, "image/png")}
            r = client.post(f"{url}/equipos/", data=data, files=files)
    else:
        r = client.post(f"{url}/equipos/", data=data)

    if r.status_code == 200:
        print(f"  OK   {equipo['nombre']}" + (f" (logo: {logo_path.name})" if logo_path else " (sin logo)"))
        return True
    elif r.status_code == 400 and "ya existe" in r.text:
        print(f"  SKIP {equipo['nombre']} (ya existe)")
        return True
    else:
        print(f"  ERR  {equipo['nombre']} — {r.status_code}: {r.text}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=BASE_URL, help="URL base de la API")
    args = parser.parse_args()

    print(f"Creando equipos en {args.url}...\n")
    ok = err = 0

    with httpx.Client(timeout=30) as client:
        for equipo in EQUIPOS:
            if crear_equipo(client, equipo, args.url):
                ok += 1
            else:
                err += 1

    print(f"\nResultado: {ok} OK, {err} errores")


if __name__ == "__main__":
    main()
