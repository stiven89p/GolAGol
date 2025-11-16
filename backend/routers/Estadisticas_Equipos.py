from typing import List
from fastapi import APIRouter, HTTPException
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.db import SessionDep

router = APIRouter(prefix="/estadisticas_equipos", tags=["estadisticas_equipos"])

@router.get("/", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipos(session: SessionDep):
    return session.query(Estadisticas_E).all()

@router.get("/eqipo/{equipo_id}", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipo(equipo_id: int, session: SessionDep):
    estadistica = session.query(Estadisticas_E).filter(Estadisticas_E.equipo_id == equipo_id).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del equipo no existe")
    return estadistica

@router.get("/eqipo/{equipo_id}/{temporada}", response_model=List[Estadisticas_E])
async def obtener_estadistica_equipo_temporada(equipo_id: int,temporada: int , session: SessionDep):
    estadistica = session.query(Estadisticas_E).filter(Estadisticas_E.equipo_id == equipo_id, Estadisticas_E.temporada == temporada)
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del equipo no existe")
    return estadistica

