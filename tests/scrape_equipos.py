"""
Scrape y crea los equipos de la Liga BetPlay desde 365scores en la API.
Descarga el logo de cada equipo en memoria y lo sube directamente, sin pasar por disco.
Requiere: pip install playwright httpx && python -m playwright install chromium

Uso: python tests/scrape_equipos.py
     python tests/scrape_equipos.py --url http://localhost:8000
     python tests/scrape_equipos.py --debug
"""

import asyncio
import argparse
import re
import unicodedata
import httpx
from playwright.async_api import async_playwright

URL_STANDINGS = "https://www.365scores.com/es/football/league/liga-betplay-620/standings"
BASE_URL = "http://localhost:8000"

# Datos estáticos de cada equipo (ciudad, estadio, etc.)
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

# Índice normalizado para búsqueda rápida
_EQUIPOS_IDX = {
    unicodedata.normalize("NFD", e["nombre"]).encode("ascii", "ignore").decode().lower(): e
    for e in EQUIPOS
}


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def buscar_datos_equipo(nombre_365: str) -> dict | None:
    """Busca los datos estáticos del equipo por nombre aproximado."""
    n = normalizar(nombre_365)
    # Coincidencia exacta
    if n in _EQUIPOS_IDX:
        return _EQUIPOS_IDX[n]
    # Coincidencia parcial: el nombre scraped está contenido en el nuestro o viceversa
    for clave, datos in _EQUIPOS_IDX.items():
        if n in clave or clave in n:
            return datos
    # Coincidencia por palabras clave (todas las palabras de más de 3 letras)
    palabras = [p for p in re.split(r'\s+', n) if len(p) > 3]
    for clave, datos in _EQUIPOS_IDX.items():
        if palabras and all(p in clave for p in palabras):
            return datos
    return None


async def obtener_equipos_365(page) -> list[dict]:
    """Extrae nombre y URL del logo de cada equipo desde la página de standings."""
    print("Cargando standings de 365scores...")
    await page.goto(URL_STANDINGS, wait_until="networkidle", timeout=60000)

    equipos = await page.eval_on_selector_all(
        "a[href*='/football/team/']",
        """
        elements => {
            const vistos = new Set();
            const resultado = [];
            for (const el of elements) {
                const href = el.getAttribute('href');
                const match = href.match(/\\/football\\/team\\/([^/]+)-(\\d+)/);
                if (!match) continue;
                const id = match[2];
                if (vistos.has(id)) continue;
                vistos.add(id);
                const img = el.querySelector('img');
                const nombre = img ? (img.alt || match[1].replace(/-/g, ' ')) : match[1].replace(/-/g, ' ');
                const logo_url = img ? img.src : null;
                resultado.push({ id, nombre, logo_url });
            }
            return resultado;
        }
        """
    )
    return equipos


def descargar_logo(client: httpx.Client, url: str) -> bytes | None:
    if not url or not url.startswith("http"):
        return None
    try:
        r = client.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def crear_equipo(client: httpx.Client, datos: dict, logo_bytes: bytes | None, api_url: str) -> bool:
    data = {
        "nombre":         datos["nombre"],
        "ciudad":         datos["ciudad"],
        "estadio":        datos["estadio"],
        "anio_fundacion": str(datos["anio_fundacion"]),
        "titulos":        str(datos["titulos"]),
    }

    if logo_bytes:
        slug = re.sub(r"\s+", "_", normalizar(datos["nombre"]))
        files = {"file": (f"{slug}.png", logo_bytes, "image/png")}
        r = client.post(f"{api_url}/equipos/", data=data, files=files)
    else:
        r = client.post(f"{api_url}/equipos/", data=data)

    if r.status_code == 200:
        logo_ok = "(con logo)" if logo_bytes else "(sin logo)"
        print(f"  OK   {datos['nombre']} {logo_ok}")
        return True
    elif r.status_code == 400 and "ya existe" in r.text:
        print(f"  SKIP {datos['nombre']} (ya existe)")
        return True
    else:
        print(f"  ERR  {datos['nombre']} - {r.status_code}: {r.text[:80]}")
        return False


async def main(api_url: str, debug: bool):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not debug)
        page = await browser.new_page()
        equipos_365 = await obtener_equipos_365(page)
        await browser.close()

    print(f"Equipos encontrados en 365scores: {len(equipos_365)}\n")

    ok = err = sin_match = 0

    with httpx.Client(timeout=30) as client:
        for eq in equipos_365:
            datos = buscar_datos_equipo(eq["nombre"])
            if datos is None:
                print(f"  SKIP '{eq['nombre']}' - sin coincidencia en la lista local")
                sin_match += 1
                continue

            logo_bytes = descargar_logo(client, eq.get("logo_url"))
            if crear_equipo(client, datos, logo_bytes, api_url):
                ok += 1
            else:
                err += 1

        # Crear equipos de la lista local que no aparecieron en 365scores (sin logo)
        nombres_creados = {normalizar(eq["nombre"]) for eq in equipos_365 if buscar_datos_equipo(eq["nombre"])}
        for datos in EQUIPOS:
            if normalizar(datos["nombre"]) not in nombres_creados:
                print(f"\n  (no encontrado en 365scores) {datos['nombre']}")
                if crear_equipo(client, datos, None, api_url):
                    ok += 1
                else:
                    err += 1

    print(f"\nResultado: {ok} OK, {err} errores, {sin_match} sin coincidencia")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",   default=BASE_URL, help="URL base de la API")
    parser.add_argument("--debug", action="store_true", help="Muestra el navegador")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.debug))
