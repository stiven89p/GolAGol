from fastapi import APIRouter, HTTPException
from modelos.Equipos import Equipo
from modelos.Partidos import Partido, PartidoCrear, PartidoActualizar
from db import SessionDep

router = APIRouter(prefix="/partidos", tags=["partidos"])

@router.post("/", response_model=Partido)
async def create_partido(new_partido: PartidoCrear, session: SessionDep):
    partido = Partido.model_validate(new_partido)

    equipo_local = session.get(Equipo, partido.equipo_local_id)
    if not equipo_local:
        raise HTTPException(status_code=404, detail="El equipo local no existe")
    equipo_visitante = session.get(Equipo, partido.equipo_visitante_id)
    if not equipo_visitante:
        raise HTTPException(status_code=404, detail="El equipo visitante no existe")
    if partido.equipo_local_id == partido.equipo_visitante_id:
        raise HTTPException(status_code=400, detail="Un equipo no puede jugar contra sí mismo")

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido