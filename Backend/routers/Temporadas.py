from typing import List
from fastapi import APIRouter, HTTPException
from Backend.modelos.Temporada import Temporada, TemporadaCrear
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.modelos.Jugadores import Jugador
from Backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from Backend.db import SessionDep

router = APIRouter(prefix="/temporadas", tags=["temporadas"])

@router.post("/", response_model=Temporada)
async def create_temporada(new_temporada: TemporadaCrear, session: SessionDep):
    temporada = Temporada.model_validate(new_temporada)

    existing_temporada = session.get(Temporada, temporada.temporada_id)
    if existing_temporada:
        raise HTTPException(status_code=400, detail="La temporada ya existe")

    session.add(temporada)
    session.commit()
    session.refresh(temporada)

    equipos = session.query(Equipo).all()
    for equipo in equipos:
        nueva_estadistica = Estadisticas_E(equipo_id=equipo.equipo_id, temporada=temporada.temporada_id)
        session.add(nueva_estadistica)
        for jugador in session.query(Jugador).filter(Jugador.equipo_id == equipo.equipo_id).all():
            nueva_estadistica_jugador = Estadisticas_J(jugador_id=jugador.jugador_id, temporada=temporada.temporada_id, equipo_id=jugador.equipo_id)
            session.add(nueva_estadistica_jugador)
    session.commit()

    return temporada

@router.get("/", response_model=List[Temporada])
async def read_temporadas(session: SessionDep):
    temporadas = session.query(Estadisticas_E).all()
    if not temporadas:
        raise HTTPException(status_code=404, detail="No se encontraron temporadas")
    return temporadas
