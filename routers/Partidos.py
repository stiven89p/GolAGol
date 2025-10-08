from typing import List
from fastapi import APIRouter, HTTPException
from modelos.Partidos import Partido, PartidoCrear, PartidoActualizar
from utils.verificaciones import *
from db import SessionDep

router = APIRouter(prefix="/partidos", tags=["partidos"])

@router.post("/", response_model=Partido)
async def create_partido(new_partido: PartidoCrear, session: SessionDep):
    partido = Partido.model_validate(new_partido)

    validar_equipo_existe(partido.equipo_local_id, session, "equipo local")
    validar_equipo_existe(partido.equipo_visitante_id, session, "equipo visitante")

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido