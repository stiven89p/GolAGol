"""
Descarga los planteles de la Liga BetPlay desde 365scores y los crea en la API.
Requiere: pip install playwright httpx && python -m playwright install chromium

Uso: python tests/scrape_jugadores.py
     python tests/scrape_jugadores.py --url http://localhost:8000
     python tests/scrape_jugadores.py --debug        # muestra el navegador
"""

import asyncio
import argparse
import unicodedata
import re
import httpx
from playwright.async_api import async_playwright

URL_STANDINGS = "https://www.365scores.com/es/football/league/liga-betplay-620/standings"
BASE_URL = "http://localhost:8000"

POSICION_MAP = {
    "portero": "portero", "arquero": "portero", "goalkeeper": "portero",
    "defensa": "defensor", "defensor": "defensor", "defender": "defensor",
    "lateral": "defensor", "central": "defensor",
    "centrocampista": "mediocampista", "mediocampista": "mediocampista",
    "volante": "mediocampista", "midfielder": "mediocampista",
    "interior": "mediocampista", "pivote": "mediocampista",
    "carrilero": "mediocampista", "media punta": "mediocampista",
    "delantero": "delantero", "atacante": "delantero", "forward": "delantero",
    "extremo": "delantero", "centro delantero": "delantero",
    "segunda punta": "delantero",
}

PAIS_MAP = {
    "colombia": "Colombiana", "venezuela": "Venezolana", "argentina": "Argentina",
    "brasil": "Brasileña", "brazil": "Brasileña", "uruguay": "Uruguaya",
    "ecuador": "Ecuatoriana", "perú": "Peruana", "peru": "Peruana",
    "chile": "Chilena", "paraguay": "Paraguaya", "bolivia": "Boliviana",
    "costa rica": "Costarricense", "panamá": "Panameña", "panama": "Panameña",
    "honduras": "Hondureña", "mexico": "Mexicana", "méxico": "Mexicana",
    "usa": "Estadounidense", "united states": "Estadounidense",
    "spain": "Española", "españa": "Española", "france": "Francesa",
    "portugal": "Portuguesa", "nigeria": "Nigeriana", "ghana": "Ghanesa",
    "senegal": "Senegalesa", "cameroon": "Camerunesa", "camerún": "Camerunesa",
}


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def mapear_posicion(texto: str) -> str:
    t = normalizar(texto)
    # Primero buscar frases completas (más específicas)
    for clave, valor in sorted(POSICION_MAP.items(), key=lambda x: -len(x[0])):
        if normalizar(clave) in t:
            return valor
    return "mediocampista"


def mapear_nacionalidad(texto: str) -> str:
    t = normalizar(texto).replace("-", " ")
    for clave, valor in PAIS_MAP.items():
        if normalizar(clave) in t:
            return valor
    return texto.strip().title() if texto.strip() else "Colombiana"


def calcular_fecha_nacimiento(fecha: str) -> str:
    """Convierte fecha dd/mm/yyyy o año yyyy a formato YYYY-MM-DD."""
    if not fecha:
        return "2000-01-01"
    m = re.search(r"(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})", fecha)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    m = re.search(r"\b(19|20)\d{2}\b", fecha)
    if m:
        return f"{m.group(0)}-01-01"
    return "2000-01-01"


def split_nombre_apellido(nombre_completo: str) -> tuple[str, str]:
    partes = nombre_completo.strip().split()
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], partes[0]
    return partes[0], " ".join(partes[1:])


# ── Playwright helpers ─────────────────────────────────────────────────────────

async def obtener_equipos_365(page) -> list[dict]:
    """Extrae nombre, slug e id de cada equipo desde la página de standings."""
    print("Cargando standings...")
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
                const slug = match[1];
                const id   = match[2];
                if (vistos.has(id)) continue;
                vistos.add(id);
                const img = el.querySelector('img');
                const nombre = img ? (img.alt || slug.replace(/-/g, ' ')) : slug.replace(/-/g, ' ');
                resultado.push({ id, slug, nombre });
            }
            return resultado;
        }
        """
    )
    return equipos


async def obtener_hrefs_plantel(page, equipo: dict, dump: bool = False) -> list[str]:
    """Visita la página de squad y devuelve las URLs de perfil de cada jugador."""
    url = f"https://www.365scores.com/es/football/team/{equipo['slug']}-{equipo['id']}/squad"
    await page.goto(url, wait_until="networkidle", timeout=60000)

    # Scroll gradual para activar lazy loading del plantel completo
    for _ in range(10):
        await page.evaluate("window.scrollBy(0, 600)")
        await page.wait_for_timeout(300)
    await page.wait_for_load_state("networkidle")

    if dump:
        info = await page.evaluate("""
            () => {
                const hrefs = Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.getAttribute('href'))
                    .filter(h => h && h.includes('football'))
                    .slice(0, 50);
                const texto = document.body.innerText.substring(0, 1500);
                return { hrefs, texto };
            }
        """)
        print("\n── HREFS encontrados:")
        for h in info["hrefs"]:
            print("  ", h)
        print("\n── TEXTO de la página:")
        print(info["texto"][:1000])
        return []

    hrefs = await page.evaluate("""
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="/football/player/"]'));
            const vistos = new Set();
            const resultado = [];
            for (const link of links) {
                const href = link.getAttribute('href');
                const m = href.match(/\\/football\\/player\\/([^/]+)-(\\d+)/);
                if (!m) continue;
                if (vistos.has(m[2])) continue;
                vistos.add(m[2]);
                resultado.push(href);
            }
            return resultado;
        }
    """)
    return hrefs


async def scrapear_perfil_jugador(page, href: str) -> dict | None:
    """Visita el perfil de un jugador y extrae sus datos desde el HTML estructurado."""
    url = f"https://www.365scores.com{href}" if href.startswith("/") else href
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception:
        print(f"      timeout: {url}")
        return None

    data = await page.evaluate("""
        () => {
            // Nombre: primer h1 de la página
            const nameEl = document.querySelector('h1');
            const nombre = nameEl ? nameEl.textContent.trim() : '';
            if (!nombre) return null;

            // Posición: elemento con "profile_role" en su clase
            const posEl = document.querySelector('[class*="profile_role"]');
            const posicion = posEl ? posEl.textContent.trim() : '';

            // Bio: contiene "Nombre (País, edad) es un jugador..."
            const bioEl = document.querySelector('[class*="_bio"]');
            const bio = bioEl ? bioEl.textContent.trim() : '';
            // Extrae el país del patrón "(Colombia, 40)"
            const bioMatch = bio.match(/\\(([^,)]+),\\s*\\d+\\)/);
            const nacionalidad = bioMatch ? bioMatch[1].trim() : '';

            // Tarjetas de detalle: pares main_text / sub_text
            // sub_text "Dorsal" → main_text es el número de camiseta
            // sub_text "10/02/1986" aparece bajo el main_text "40 años"
            let numero = 0;
            let nacimiento = '';

            const mainEls = Array.from(document.querySelectorAll('[class*="details_card_main_text"]'));
            const subEls  = Array.from(document.querySelectorAll('[class*="details_card_sub_text"]'));

            for (let i = 0; i < subEls.length; i++) {
                const sub  = (subEls[i].textContent  || '').trim();
                const main = mainEls[i] ? (mainEls[i].textContent || '').trim() : '';

                if (/^[Dd]orsal$/.test(sub)) {
                    numero = parseInt(main) || 0;
                }
                // Fecha de nacimiento: sub_text con formato dd/mm/yyyy (bajo la edad)
                if (/^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/.test(sub)) {
                    nacimiento = sub;
                }
            }

            // Foto: imagen de perfil del jugador (aumentar resolución a 200px)
            const imgEl = document.querySelector('[class*="profile_image"]');
            let fotoUrl = imgEl ? imgEl.src : '';
            if (fotoUrl) {
                fotoUrl = fotoUrl.replace(/w_\\d+,h_\\d+/, 'w_200,h_200');
            }

            return { nombre, posicion, numero, nacimiento, nacionalidad, fotoUrl };
        }
    """)

    return data


# ── API helpers ────────────────────────────────────────────────────────────────

def obtener_equipos_api(api_url: str) -> dict[str, int]:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{api_url}/equipos/")
        r.raise_for_status()
    return {e["nombre"]: e["equipo_id"] for e in r.json()}


def descargar_foto(client: httpx.Client, url: str) -> bytes | None:
    """Descarga la foto del jugador desde 365scores."""
    if not url or not url.startswith("http"):
        return None
    try:
        r = client.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def crear_jugador(client: httpx.Client, jugador: dict, equipo_id: int, api_url: str) -> bool:
    nombre, apellido = split_nombre_apellido(jugador["nombre"])
    if not nombre or not apellido:
        return False

    data = {
        "nombre":           nombre,
        "apellido":         apellido,
        "fecha_nacimiento": calcular_fecha_nacimiento(jugador.get("nacimiento", "")),
        "posicion":         mapear_posicion(jugador.get("posicion", "")),
        "nacionalidad":     mapear_nacionalidad(jugador.get("nacionalidad", "")),
        "numero_camiseta":  str(jugador.get("numero") or 0),
        "equipo_id":        str(equipo_id),
    }

    foto_bytes = descargar_foto(client, jugador.get("fotoUrl", ""))
    if foto_bytes:
        slug = re.sub(r"\s+", "_", nombre.lower())
        files = {"foto": (f"{slug}.png", foto_bytes, "image/png")}
        r = client.post(f"{api_url}/jugadores/", data=data, files=files)
    else:
        r = client.post(f"{api_url}/jugadores/", data=data)

    nombre_completo = f"{nombre} {apellido}"

    if r.status_code == 200:
        foto_ok = "📷" if foto_bytes else ""
        print(f"    OK   {nombre_completo} ({data['posicion']}, #{data['numero_camiseta']}) {foto_ok}")
        return True
    elif r.status_code == 400 and "ya existe" in r.text:
        print(f"    SKIP {nombre_completo} (ya existe)")
        return True
    else:
        print(f"    ERR  {nombre_completo} — {r.status_code}: {r.text[:80]}")
        return False


# ── Main ───────────────────────────────────────────────────────────────────────

async def main(api_url: str, debug: bool, dump: bool = False):
    print(f"Obteniendo equipos de la API ({api_url})...")
    try:
        equipos_api = obtener_equipos_api(api_url)
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        return
    print(f"Equipos en la API: {len(equipos_api)}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not debug)
        page = await browser.new_page()

        equipos_365 = await obtener_equipos_365(page)
        print(f"Equipos en 365scores: {len(equipos_365)}\n")

        ok_total = err_total = 0

        with httpx.Client(timeout=30) as client:
            for equipo_365 in equipos_365:
                equipo_id = None
                for nombre_api, eid in equipos_api.items():
                    if normalizar(nombre_api) == normalizar(equipo_365["nombre"]) or \
                       normalizar(equipo_365["nombre"]) in normalizar(nombre_api) or \
                       normalizar(nombre_api) in normalizar(equipo_365["nombre"]):
                        equipo_id = eid
                        break

                if equipo_id is None:
                    print(f"⚠  '{equipo_365['nombre']}' no encontrado en la API — omitiendo")
                    continue

                print(f"\n── {equipo_365['nombre']} (id 365: {equipo_365['id']})")
                hrefs = await obtener_hrefs_plantel(page, equipo_365, dump=dump)

                if not hrefs:
                    if dump:
                        break
                    print("   Sin jugadores encontrados (revisa con --dump)")
                    continue

                print(f"   {len(hrefs)} jugadores encontrados, obteniendo perfiles...")

                ok = err = 0
                for href in hrefs:
                    jugador = await scrapear_perfil_jugador(page, href)
                    if jugador and jugador.get("nombre"):
                        if crear_jugador(client, jugador, equipo_id, api_url):
                            ok += 1
                        else:
                            err += 1
                    await page.wait_for_timeout(300)

                print(f"   → {ok} OK, {err} errores")
                ok_total  += ok
                err_total += err

        await browser.close()

    print(f"\nTotal: {ok_total} jugadores creados, {err_total} errores")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",   default=BASE_URL, help="URL base de la API")
    parser.add_argument("--debug", action="store_true", help="Muestra el navegador")
    parser.add_argument("--dump",  action="store_true", help="Muestra los hrefs y texto del primer equipo")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.debug, args.dump))
