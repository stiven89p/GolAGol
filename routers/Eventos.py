from fastapi import APIRouter, HTTPException
from modelos.Equipos import Equipo
from modelos.Partidos import Partido
from modelos.Jugadores import Jugador
from modelos.Eventos import Evento, EventoCrear
from db import SessionDep

router = APIRouter(prefix="/eventos", tags=["eventos"])

@router.post("/", response_model=Evento)
async def create_evento(new_evento: EventoCrear, session: SessionDep):
    evento = Evento.model_validate(new_evento)
    partido = session.get(Partido, evento.partido_id)
    jugador = session.get(Jugador, evento.jugador_id)
    jugador_asociado = session.get(Jugador, evento.jugador_id)

    if not partido:
        raise HTTPException(status_code=404, detail="El partido no existe")

    equipo = session.get(Equipo, evento.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    if evento.equipo_id not in [partido.equipo_local_id, partido.equipo_visitante_id]:
        raise HTTPException(status_code=400, detail="El equipo no está participando en el partido")

    if evento.jugador_id and not jugador:
        raise HTTPException(status_code=404, detail="El jugador no existe")

    if evento.jugador_id and jugador.equipo_id != partido.equipo_id:
        raise HTTPException(status_code=400, detail="El jugador no pertenece al equipo que está participando en el partido")

    if evento.jugador_asociado_id:
        if evento.jugador_asociado_id and not jugador:
            raise HTTPException(status_code=404, detail="El jugador no existe")
        if evento.jugador_asociado_id and jugador_asociado.equipo_id != partido.equipo_id:
            raise HTTPException(status_code=400, detail="El jugador asociado no pertenece al equipo que está participando en el partido")

    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento
