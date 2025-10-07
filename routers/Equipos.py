from typing import List
from fastapi import APIRouter, HTTPException
from models import Equipo, EquipoCrear
from db import SessionDep

router = APIRouter(prefix="/equipos", tags=["equipos"])

@router.post("/", response_model=Equipo)
async def create_equipo(new_equipo: EquipoCrear, session: SessionDep):
    equipo = Equipo.model_validate(new_equipo)
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo

@router.get("/", response_model=List[Equipo])
async def read_equipos(session: SessionDep):
    return session.query(Equipo).all()

@router.get("/{equipo_id}", response_model=Equipo)
async def read_equipo(equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo