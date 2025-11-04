from fastapi import FastAPI, Request, UploadFile, File, Form
from jinja2.bccache import Bucket
from Backend.db import SessionDep
from fastapi.staticfiles import StaticFiles
import time
from Backend.utils.bucket import upload_file
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

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # tu frontend
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
    return templates.TemplateResponse("PartidosProgramados.jsx", {"request": request})

@app.post("/bucket")
async def create_bucket(file: UploadFile = File(...) ):
    result = await upload_file(file)
    return result


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
