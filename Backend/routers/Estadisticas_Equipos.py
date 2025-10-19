from typing import List
from fastapi import APIRouter, HTTPException
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.db import SessionDep

router = APIRouter(prefix="/estadisticas_equipos", tags=["estadisticas_equipos"])

@router.get("/", response_model=List[Estadisticas_E])
async def read_equipos(session: SessionDep):
    return session.query(Estadisticas_E).all()

@router.get("/{id_estadistica}", response_model=Estadisticas_E)
async def read_estadistica_equipo(id_estadistica: int, session: SessionDep):
    estadistica = session.get(Estadisticas_E, id_estadistica)
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del equipo no existe")
    return estadistica
