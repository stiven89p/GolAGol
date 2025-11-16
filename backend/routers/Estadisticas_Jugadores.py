from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from backend.modelos.Jugadores import Jugador
from backend.modelos.Equipos import Equipo
from backend.db import SessionDep
from pydantic import BaseModel

class GoleadorDTO(BaseModel):
    posicion: int
    jugador_nombre: str
    jugador_apellido: str
    jugador_foto: str | None
    equipo_nombre: str
    goles: int

router = APIRouter(prefix="/estadisticas_jugadores", tags=["estadisticas_jugadores"])

@router.get("/", response_model=List[Estadisticas_J])
async def obtener_estadistica_jugadores(session: SessionDep):
    return session.query(Estadisticas_J).all()

@router.get("/{equipo_id}", response_model=List[Estadisticas_J])
async def obtener_estadisticas_jugador(equipo_id: int, session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica

@router.get("/{equipo_id}/{temporada}", response_model=List[Estadisticas_J])
async def obtener_estadistica_jugador_temporada(equipo_id: int,temporada: int , session: SessionDep):
    estadistica = session.query(Estadisticas_J).filter(Estadisticas_J.equipo_id == equipo_id,Estadisticas_J.temporada == temporada).all()
    if not estadistica:
        raise HTTPException(status_code=404, detail="La estadística del jugador no existe")
    return estadistica

@router.get("/temporada/{temporada_id}/goleadores", response_model=List[GoleadorDTO])
async def obtener_goleadores_temporada(temporada_id: int, session: SessionDep, limit: int = 10):
    """Obtiene los goleadores de una temporada ordenados por cantidad de goles"""
    
    # Query con joins para obtener info del jugador y equipo
    estadisticas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.goles > 0)
        .order_by(Estadisticas_J.goles.desc())
    ).all()
    
    if not estadisticas:
        return []
    
    # Construir DTOs con posición
    goleadores = []
    for idx, (est, jugador, equipo) in enumerate(estadisticas[:limit], start=1):
        goleadores.append(GoleadorDTO(
            posicion=idx,
            jugador_nombre=jugador.nombre,
            jugador_apellido=jugador.apellido,
            jugador_foto=jugador.foto,
            equipo_nombre=equipo.nombre,
            goles=est.goles
        ))
    
    return goleadores



@router.get("/temporada/{temporada_id}/{equipo_id}/goleadores", response_model=List[GoleadorDTO])
async def obtener_goleadores_temporada_equipo(temporada_id: int, equipo_id: int, session: SessionDep, limit: int = 10):
    """Obtiene los goleadores de una temporada y equipo ordenados por cantidad de goles"""
    
    # Query con joins para obtener info del jugador y equipo
    estadisticas = session.exec(
        select(Estadisticas_J, Jugador, Equipo)
        .join(Jugador, Estadisticas_J.jugador_id == Jugador.jugador_id)
        .join(Equipo, Estadisticas_J.equipo_id == Equipo.equipo_id)
        .where(Estadisticas_J.temporada == temporada_id)
        .where(Estadisticas_J.equipo_id == equipo_id)
        .where(Estadisticas_J.goles > 0)
        .order_by(Estadisticas_J.goles.desc())
    ).all()
    
    if not estadisticas:
        return []
    
    # Construir DTOs con posición
    goleadores = []
    for idx, (est, jugador, equipo) in enumerate(estadisticas[:limit], start=1):
        goleadores.append(GoleadorDTO(
            posicion=idx,
            jugador_nombre=jugador.nombre,
            jugador_apellido=jugador.apellido,
            jugador_foto=jugador.foto,
            equipo_nombre=equipo.nombre,
            goles=est.goles
        ))
    
    return goleadores