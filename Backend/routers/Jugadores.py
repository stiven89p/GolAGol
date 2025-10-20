from fastapi import APIRouter, HTTPException, Form
from datetime import date
from Backend.modelos.Equipos import Equipo
from Backend.modelos.Jugadores import Jugador, JugadorCrear, JugadorActualizar
from Backend.utils.enumeraciones import PosicionJugador
from Backend.db import SessionDep

router = APIRouter(prefix="/jugadores", tags=["jugadores"])

@router.post("/", response_model=Jugador)
async def crear_jugador(session: SessionDep,
                        nombre: str = Form(...),
                        apellido: str = Form(...),
                        fecha_nacimiento: date = Form(...),
                        posicion: PosicionJugador = Form(...),
                        nacionalidad: str = Form(...),
                        equipo_id: int = Form(...)
                        ):
    new_jugador = JugadorCrear(
        nombre=nombre,
        apellido=apellido,
        fecha_nacimiento=fecha_nacimiento,
        posicion=posicion,
        nacionalidad=nacionalidad,
        equipo_id=equipo_id,
    )
    jugador = Jugador.model_validate(new_jugador)

    if jugador.equipo_id:
        equipo = session.get(Equipo, jugador.equipo_id)
        if not equipo:
            raise HTTPException(status_code=404, detail="El equipo no existe")

    session.add(jugador)
    session.commit()
    session.refresh(jugador)

    return jugador

@router.get("/", response_model=list[Jugador])
async def obtener_jugadores(session: SessionDep):
    jugadores = session.query(Jugador).all()
    if not jugadores:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores")
    return jugadores

@router.get("/{jugador_id}", response_model=Jugador)
async def obtener_jugador(jugador_id: int, session: SessionDep):
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador

@router.get("/{Posicion}/", response_model=list[Jugador])
async def obtener_jugador_posicion(Posicion: PosicionJugador , session: SessionDep):
    jugador = session.query(Jugador).filter(Jugador.posicion == Posicion).all()
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador

@router.patch("/{jugador_id}", response_model=Jugador)
async def actualizar_jugador(jugador_id: int, jugador_update: JugadorActualizar, session: SessionDep):
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
