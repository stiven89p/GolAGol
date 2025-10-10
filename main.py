from fastapi import FastAPI
from db import SessionDep
import time
from sqlalchemy import text
import routers.Eventos
import routers.Equipos
import routers.Partidos
import routers.Jugadores
import routers.Temporadas
from db import create_tables
app = FastAPI(lifespan=create_tables, title="Gol a Gol API")
app.include_router(routers.Equipos.router)
app.include_router(routers.Partidos.router)
app.include_router(routers.Eventos.router)
app.include_router(routers.Jugadores.router)
app.include_router(routers.Temporadas.router)



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
