from fastapi import APIRouter, HTTPException
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from Backend.modelos.Jugadores import Jugador, JugadorCrear, JugadorActualizar
from Backend.db import SessionDep

router = APIRouter(prefix="/jugadores", tags=["jugadores"])

@router.post("/", response_model=Jugador)
async def create_jugador(new_jugador: JugadorCrear, session: SessionDep):
    jugador = Jugador.model_validate(new_jugador)
    estadistica = session.get(Estadisticas_J, jugador.jugador_id)

    if jugador.equipo_id:
        equipo = session.get(Equipo, jugador.equipo_id)
        if not equipo:
            raise HTTPException(status_code=404, detail="El equipo no existe")

    session.add(jugador)
    session.commit()
    session.refresh(jugador)

    return jugador

@router.get("/", response_model=list[Jugador])
async def read_jugadores(session: SessionDep):
    jugadores = session.query(Jugador).all()
    if not jugadores:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores")
    return jugadores

@router.get("/{jugador_id}", response_model=Jugador)
async def get_jugador(jugador_id: int, session: SessionDep):
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador

@router.put("/{jugador_id}", response_model=Jugador)
async def update_jugador(jugador_id: int, jugador_update: JugadorActualizar, session: SessionDep):
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    jugador_data = jugador_update.model_dump(exclude_unset=True)

    if "equipo_id" in jugador_data and jugador_data["equipo_id"] is not None:
        equipo = session.get(Equipo, jugador_data["equipo_id"])
        if not equipo:
            raise HTTPException(status_code=404, detail="El equipo no existe")

    for key, value in jugador_data.items():
        setattr(jugador, key, value)

    session.add(jugador)
    session.commit()
    session.refresh(jugador)
    return jugador
