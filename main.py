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
import time

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
    return templates.TemplateResponse("index.html", {"request": request, "cache_bust": int(time.time())})

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
        "equipo_local_id": partido.equipo_local_id,
        "equipo_local_nombre": getattr(equipo_local, "nombre", ""),
        "equipo_local_logo": logo_url(getattr(equipo_local, "logo", None)),
        "equipo_visitante_id": partido.equipo_visitante_id,
        "equipo_visitante_nombre": getattr(equipo_visitante, "nombre", ""),
        "equipo_visitante_logo": logo_url(getattr(equipo_visitante, "logo", None)),
    }

    return templates.TemplateResponse("partido.html", {"request": request, "partido": detalle})

@app.get("/equipo/{equipo_id}")
async def equipo(request: Request, equipo_id: int, session: SessionDep):
    from backend.modelos.Estadisticas_Equipos import Estadisticas_E
    from backend.utils.enumeraciones import EstadoPartidos
    from sqlalchemy import or_
    
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"
    
    # Obtener resultados recientes (últimos 5 partidos finalizados)
    el = aliased(Equipo)
    ev = aliased(Equipo)
    
    partidos_finalizados = (
        session.query(Partido, el, ev)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(
            or_(Partido.equipo_local_id == equipo_id, Partido.equipo_visitante_id == equipo_id),
            Partido.estado == EstadoPartidos.FINALIZADO
        )
        .order_by(Partido.fecha.desc())
        .all()
    )
    
    resultados = []
    for partido, eq_local, eq_visitante in partidos_finalizados:
        es_local = partido.equipo_local_id == equipo_id
        if es_local:
            resultado = f"{partido.goles_local} - {partido.goles_visitante}"
            eq_oponente = eq_visitante
        else:
            resultado = f"{partido.goles_visitante} - {partido.goles_local}"
            eq_oponente = eq_local

        resultados.append({
            "resultado": resultado,
            "oponente": eq_oponente.nombre,
            "oponente_logo": logo_url(getattr(eq_oponente, "logo", None)),
            "fecha": partido.fecha.strftime("%d/%m/%Y")
        })
    
    # Obtener próximos partidos (programados)
    partidos_programados = (
        session.query(Partido, el, ev)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(
            or_(Partido.equipo_local_id == equipo_id, Partido.equipo_visitante_id == equipo_id),
            Partido.estado == EstadoPartidos.PROGRAMADO
        )
        .order_by(Partido.fecha.asc())
        .limit(5)
        .all()
    )
    
    proximos = []
    for partido, eq_local, eq_visitante in partidos_programados:
        es_local = partido.equipo_local_id == equipo_id
        eq_oponente = eq_visitante if es_local else eq_local
        
        proximos.append({
            "oponente": eq_oponente.nombre,
            "oponente_logo": logo_url(eq_oponente.logo),
            "fecha": partido.fecha.strftime("%d/%m/%Y"),
            "hora": partido.hora.strftime("%H:%M") if partido.hora else None,
            "lugar": partido.estadio
        })
    
    # Obtener estadísticas del equipo
    stats = session.query(Estadisticas_E).filter(Estadisticas_E.equipo_id == equipo_id).all()
    
    estadisticas = []
    for stat in stats:
        estadisticas.append({
            "temporada": f"Temporada {stat.temporada}",
            "partidos_jugados": stat.partidos_jugados,
            "victorias": stat.victorias,
            "empates": stat.empates,
            "derrotas": stat.derrotas,
            "goles_favor": stat.goles_favor,
            "goles_contra": stat.goles_contra,
            "puntos": stat.puntos,
            "tarjetas_amarillas": stat.tarjetas_amarillas,
            "tarjetas_rojas": stat.tarjetas_rojas
        })
    
    return templates.TemplateResponse("equipo.html", {
        "request": request,
        "equipo": equipo,
        "resultados": resultados,
        "proximos": proximos,
        "estadisticas": estadisticas
    })
