"""
Descarga los logos de los equipos de la Liga BetPlay desde 365scores.
Requiere: pip install playwright requests && python -m playwright install chromium
"""

import asyncio
import os
import re
import httpx
from pathlib import Path
from playwright.async_api import async_playwright


URL = "https://www.365scores.com/es/football/league/liga-betplay-620/standings"
OUTPUT_DIR = Path(__file__).parent / "logos_equipos"


async def obtener_equipos(page) -> list[dict]:
    await page.goto(URL, wait_until="networkidle", timeout=60000)

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
                const nombre = img ? (img.alt || match[1]) : match[1];
                const src = img ? img.src : null;
                resultado.push({ id, nombre, logo_url: src });
            }
            return resultado;
        }
        """
    )
    return equipos


async def descargar_logo(client: httpx.AsyncClient, equipo: dict, carpeta: Path):
    url = equipo.get("logo_url")
    nombre = re.sub(r'[^\w\- ]', '', equipo["nombre"]).strip().replace(" ", "_")

    if not url or not url.startswith("http"):
        print(f"  [sin URL] {equipo['nombre']}")
        return

    try:
        r = await client.get(url, follow_redirects=True, timeout=15)
        r.raise_for_status()

        ext = url.split(".")[-1].split("?")[0]
        if ext not in ("png", "jpg", "jpeg", "svg", "webp"):
            ext = "png"

        ruta = carpeta / f"{nombre}.{ext}"
        ruta.write_bytes(r.content)
        print(f"  OK  {equipo['nombre']} -> {ruta.name}")
    except Exception as e:
        print(f"  ERR {equipo['nombre']}: {e}")


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Abriendo página...")
        equipos = await obtener_equipos(page)
        await browser.close()

    if not equipos:
        print("No se encontraron equipos. Prueba con headless=False para depurar.")
        return

    print(f"\nEquipos encontrados: {len(equipos)}")
    for e in equipos:
        print(f"  {e['nombre']} — {e['logo_url']}")

    print(f"\nDescargando logos en '{OUTPUT_DIR}/'...")
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        tareas = [descargar_logo(client, e, OUTPUT_DIR) for e in equipos]
        await asyncio.gather(*tareas)

    print("\nListo.")


if __name__ == "__main__":
    asyncio.run(main())
