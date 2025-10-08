from fastapi import HTTPException
from sqlmodel import Session, select
from modelos.Equipos import Equipo

def validar_equipo_existe(equipo_id: int, session: Session, tipo: str = "equipo") -> None:
    equipo = session.exec(
        select(Equipo).where(Equipo.id_equipo == equipo_id)
    ).first()
    if not equipo:
        raise HTTPException(status_code=400, detail=f"El {tipo} no existe")
