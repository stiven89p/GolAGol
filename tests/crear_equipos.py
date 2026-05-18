"""
Crea los equipos de la Liga BetPlay en la API.
Usa los logos descargados por download_logos.py si existen en tests/logos_equipos/.

Uso: python tests/crear_equipos.py
     python tests/crear_equipos.py --url http://localhost:8000
"""

import httpx
import argparse
from pathlib import Path

BASE_URL = "http://localhost:8000"
LOGOS_DIR = Path(__file__).parent / "logos_equipos"

EQUIPOS = [
    {"nombre": "Atlético Nacional",       "ciudad": "Medellín",       "estadio": "Estadio Atanasio Girardot",          "anio_fundacion": 1947, "titulos": 16},
    {"nombre": "Millonarios",             "ciudad": "Bogotá",         "estadio": "Estadio El Campín",                  "anio_fundacion": 1946, "titulos": 15},
    {"nombre": "América De Cali",         "ciudad": "Cali",           "estadio": "Estadio Olímpico Pascual Guerrero",  "anio_fundacion": 1927, "titulos": 13},
    {"nombre": "Deportivo Cali",          "ciudad": "Cali",           "estadio": "Estadio Deportivo Cali",             "anio_fundacion": 1912, "titulos": 9},
    {"nombre": "Junior",                  "ciudad": "Barranquilla",   "estadio": "Estadio Metropolitano Roberto Meléndez", "anio_fundacion": 1924, "titulos": 8},
    {"nombre": "Santa Fe",                "ciudad": "Bogotá",         "estadio": "Estadio El Campín",                  "anio_fundacion": 1941, "titulos": 9},
    {"nombre": "Deportes Tolima",         "ciudad": "Ibagué",         "estadio": "Estadio Manuel Murillo Toro",        "anio_fundacion": 1954, "titulos": 4},
    {"nombre": "Once Caldas",             "ciudad": "Manizales",      "estadio": "Estadio Palogrande",                 "anio_fundacion": 1961, "titulos": 4},
    {"nombre": "Independiente Medellín",  "ciudad": "Medellín",       "estadio": "Estadio Atanasio Girardot",          "anio_fundacion": 1913, "titulos": 5},
    {"nombre": "Deportivo Pereira",       "ciudad": "Pereira",        "estadio": "Estadio Hernán Ramírez Villegas",   "anio_fundacion": 1944, "titulos": 1},
    {"nombre": "Atlético Bucaramanga",    "ciudad": "Bucaramanga",    "estadio": "Estadio Alfonso López",              "anio_fundacion": 1949, "titulos": 1},
    {"nombre": "Envigado",                "ciudad": "Envigado",       "estadio": "Estadio Polideportivo Sur",          "anio_fundacion": 1986, "titulos": 0},
    {"nombre": "Jaguares De Córdoba",     "ciudad": "Montería",       "estadio": "Estadio Jaraguay",                   "anio_fundacion": 2013, "titulos": 0},
    {"nombre": "La Equidad",              "ciudad": "Bogotá",         "estadio": "Estadio Metropolitano de Techo",    "anio_fundacion": 1982, "titulos": 2},
    {"nombre": "Patriotas",               "ciudad": "Tunja",          "estadio": "Estadio La Independencia",           "anio_fundacion": 1955, "titulos": 0},
    {"nombre": "Fortaleza Ceif",          "ciudad": "Bogotá",         "estadio": "Estadio Metropolitano de Techo",    "anio_fundacion": 2015, "titulos": 0},
    {"nombre": "Boyacá Chicó",            "ciudad": "Tunja",          "estadio": "Estadio La Independencia",           "anio_fundacion": 2003, "titulos": 2},
    {"nombre": "Alianza Fc",              "ciudad": "Valledupar",     "estadio": "Estadio Sierra Nevada",              "anio_fundacion": 2017, "titulos": 0},
    {"nombre": "Llaneros",                "ciudad": "Villavicencio",  "estadio": "Estadio Bello Horizonte",            "anio_fundacion": 2012, "titulos": 0},
    {"nombre": "Cortuluá",                "ciudad": "Tuluá",          "estadio": "Estadio 12 de Octubre",              "anio_fundacion": 1971, "titulos": 0},
]


def buscar_logo(nombre: str) -> Path | None:
    if not LOGOS_DIR.exists():
        return None
    nombre_limpio = nombre.replace(" ", "_").replace("é", "e").replace("ó", "o").replace("á", "a").replace("í", "i").replace("ú", "u")
    for archivo in LOGOS_DIR.iterdir():
        if archivo.stem.lower() == nombre_limpio.lower():
            return archivo
    # Búsqueda parcial
    for archivo in LOGOS_DIR.iterdir():
        palabras = nombre_limpio.lower().split("_")
        if all(p in archivo.stem.lower() for p in palabras if len(p) > 3):
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
