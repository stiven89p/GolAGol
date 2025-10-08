from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field

class PartidoBase(SQLModel):
    fecha: date = Field(nullable=False, description="Fecha del partido")
    estadio: str = Field(nullable=False, description="Estadio del partido")
    equipo_local_id: int = Field(foreign_key="equipo.id_equipo", nullable=False, description="ID del equipo local")
    equipo_visitante_id: int = Field(foreign_key="equipo.id_equipo", nullable=False, description="ID del equipo visitante")



class Partido(PartidoBase, table=True):
    id_partido: Optional[int] = Field(default=None, primary_key=True)


class PartidoCrear(PartidoBase):
    pass


class PartidoActualizar(SQLModel):
    fecha: Optional[date] = None
    estadio: Optional[str] = None
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None
