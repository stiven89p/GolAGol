from typing import List
from fastapi import APIRouter, HTTPException
from Backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from Backend.db import SessionDep

router = APIRouter(prefix="/estadisticas_jugadores", tags=["estadisticas_jugadores"])

@router.get("/", response_model=List[Estadisticas_J])
async def read_jugadores(session: SessionDep):
    return session.query(Estadisticas_J).all()

@router.get("/{equipo_id}", response_model=List[Estadisticas_J])
async def read_estadistica_jugador(equipo_id: int, session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica

@router.get("/{equipo_id}", response_model=List[Estadisticas_J])
async def read_estadistica_jugador(equipo_id: int, session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica