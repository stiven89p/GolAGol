from fastapi import FastAPI, Request
from Backend.db import SessionDep
import time
from sqlalchemy import text
import Backend.routers.Partidos
import Backend.routers.Temporadas
import Backend.routers.Equipos
import Backend.routers.Eventos
import Backend.routers.Jugadores
import Backend.routers.Estadisticas_Equipos
import Backend.routers.Estadisticas_Jugadores
from Backend.db import create_tables
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(lifespan=create_tables, title="Gol a Gol API")

# 🔹 CORS habilitado para permitir peticiones desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o ["http://127.0.0.1:5500"] si usas VS Code Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Rutas del proyecto
app.include_router(Backend.routers.Equipos.router)
app.include_router(Backend.routers.Partidos.router)
app.include_router(Backend.routers.Eventos.router)
app.include_router(Backend.routers.Jugadores.router)
app.include_router(Backend.routers.Temporadas.router)
app.include_router(Backend.routers.Estadisticas_Equipos.router)
app.include_router(Backend.routers.Estadisticas_Jugadores.router)


templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check(session: SessionDep):
    start = time.time()
    try:
        session.exec(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    duration = round((time.time() - start) * 1000, 2)
    return {
        "status": "ok" if db_status == "connected" else "error",
        "database": db_status,
        "response_time_ms": duration
    }
