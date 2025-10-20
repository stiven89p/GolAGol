from typing import List
from fastapi import APIRouter, HTTPException
from Backend.modelos.Equipos import Equipo, EquipoCrear, EquipoActualizar
from datetime import datetime
from Backend.modelos.Estadisticas_Equipos import Estadisticas_E
from Backend.db import SessionDep

router = APIRouter(prefix="/equipos", tags=["equipos"])

@router.post("/", response_model=Equipo)
async def crear_equipo(new_equipo: EquipoCrear, session: SessionDep):
    equipo = Equipo.model_validate(new_equipo)

    session.add(equipo)
    session.commit()
    session.refresh(equipo)

    return equipo

@router.get("/", response_model=List[Equipo])
async def obtener_equipos(session: SessionDep):
    return session.query(Equipo).filter(Equipo.activo == True).all()

@router.get("/{equipo_id}", response_model=Equipo)
async def obtener_equipo(equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")
    return equipo

@router.delete("/{equipo_id}", response_model=Equipo)
async def eliminar_equipo(equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    equipo.activo = False
    session.commit()
    return equipo

@router.patch("/{equipo_id}", response_model=Equipo)
async def actualizar_equipo(equipo_id: int, updated_equipo: EquipoActualizar, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")
    equipo_data = updated_equipo.model_dump(exclude_unset=True)
    for key, value in equipo_data.items():
        setattr(equipo, key, value)
    session.add(equipo)
    session.commit()
    session.refresh(equipo)
    return equipo