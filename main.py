from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from jinja2.bccache import Bucket
from fastapi.staticfiles import StaticFiles
from backend.utils.bucket import upload_file
from sqlalchemy import text
from sqlalchemy.orm import aliased
import backend.routers.Partidos
import backend.routers.Temporadas
import backend.routers.Equipos
import backend.routers.Eventos
import backend.routers.Jugadores
from backend.modelos.Equipos import Equipo
import backend.routers.Estadisticas_Equipos
import backend.routers.Estadisticas_Jugadores
from backend.db import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.modelos.Partidos import Partido

app = FastAPI(lifespan=create_tables, title="Gol a Gol API")

from fastapi.middleware.cors import CORSMiddleware

# Montar archivos estáticos ANTES de las rutas
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 🔹 Rutas del proyecto
app.include_router(backend.routers.Equipos.router)
app.include_router(backend.routers.Partidos.router)
app.include_router(backend.routers.Eventos.router)
app.include_router(backend.routers.Jugadores.router)
app.include_router(backend.routers.Temporadas.router)
app.include_router(backend.routers.Estadisticas_Equipos.router)
app.include_router(backend.routers.Estadisticas_Jugadores.router)
@app.post("/bucket")
async def create_bucket(file: UploadFile = File(...) ):
    result = await upload_file(file)
    return result

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/partido/{partido_id}", response_class=HTMLResponse)
async def partido_detalle(request: Request, partido_id: int, session: SessionDep):
    el = aliased(Equipo)
    ev = aliased(Equipo)

    row = (
        session.query(Partido, el, ev)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(Partido.partido_id == partido_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido, equipo_local, equipo_visitante = row

    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        # si ya es url absoluta o ruta desde static, dejarla
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        # caso común: almacena 'img/archivo.png' o solo 'archivo.png'
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"

    detalle = {
        "partido_id": partido.partido_id,
        "estado": partido.estado,
        "fecha": partido.fecha,
        "hora": partido.hora.strftime("%H:%M") if partido.hora else None,
        "lugar": partido.estadio,
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante,
        "equipo_local_nombre": getattr(equipo_local, "nombre", ""),
        "equipo_local_logo": logo_url(getattr(equipo_local, "logo", None)),
        "equipo_visitante_nombre": getattr(equipo_visitante, "nombre", ""),
        "equipo_visitante_logo": logo_url(getattr(equipo_visitante, "logo", None)),
    }

    return templates.TemplateResponse("partido.html", {"request": request, "partido": detalle})

@app.get("/equipo/{equipo_id}")
async def equipo(request: Request, equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return templates.TemplateResponse("equipo.html", {"request": request, "equipo": equipo})
