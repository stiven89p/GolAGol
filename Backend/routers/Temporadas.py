from typing import List
from datetime import date
from fastapi import APIRouter, HTTPException, Form
from Backend.modelos.Temporada import Temporada, TemporadaCrear
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.modelos.Jugadores import Jugador
from Backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from Backend.db import SessionDep

router = APIRouter(prefix="/temporadas", tags=["temporadas"])

@router.post("/", response_model=Temporada)
async def crear_temporada(session: SessionDep,
                          fecha_inicio: date = Form(...),
                          fecha_fin: date = Form(...)
                          ):
    new_temporada = {
        "nombre": f"{fecha_inicio.year}/{fecha_fin.year}",
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }
    temporada = Temporada.model_validate(new_temporada)

    existing_temporada = session.get(Temporada, temporada.temporada_id)
    if existing_temporada:
        raise HTTPException(status_code=400, detail="La temporada ya existe")

    session.add(temporada)
    session.commit()
    session.refresh(temporada)

    equipos = session.query(Equipo).filter(Equipo.activo == True).all()
    for equipo in equipos:
        nueva_estadistica = Estadisticas_E(equipo_id=equipo.equipo_id, temporada=temporada.temporada_id)
        session.add(nueva_estadistica)
        for jugador in session.query(Jugador).filter(Jugador.equipo_id == equipo.equipo_id).all():
            nueva_estadistica_jugador = Estadisticas_J(jugador_id=jugador.jugador_id, temporada=temporada.temporada_id, equipo_id=jugador.equipo_id)
            session.add(nueva_estadistica_jugador)
    session.commit()

    return temporada

@router.patch("/{temporada_id}", response_model=Temporada)
async def finalizar_temporada(temporada_id: int, session: SessionDep):
    temporada = session.get(Temporada, temporada_id)
    if not temporada:
        raise HTTPException(status_code=404, detail="Temporada no encontrada")

    temporada.estado = "FINALIZADA"
    equipo_ganador = (
        session.query(Estadisticas_E)
        .filter(Estadisticas_E.temporada == temporada_id)
        .order_by(Estadisticas_E.puntos.desc())
        .order_by(Estadisticas_E.goles_favor.desc())
        .order_by(Estadisticas_E.goles_contra.desc())
        .first()
    )
    if equipo_ganador:
        equipo = session.get(Equipo, equipo_ganador.equipo_id)
        equipo.titulos += 1
        session.add(equipo)
    session.add(temporada)
    session.commit()
    session.refresh(temporada)

    return temporada

@router.get("/", response_model=List[Temporada])
async def obtener_temporadas(session: SessionDep):
    temporadas = session.query(Estadisticas_E).all()
    if not temporadas:
        raise HTTPException(status_code=404, detail="No se encontraron temporadas")
    return temporadas
