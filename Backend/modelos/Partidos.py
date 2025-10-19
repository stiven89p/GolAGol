from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field

class PartidoBase(SQLModel):
    fecha: date = Field(nullable=False, description="Fecha del partido")
    jornada: int = Field(nullable=False, description="Jornada del partido")
    estadio: str = Field(nullable=False, description="Estadio del partido")
    temporada_id: int = Field(foreign_key="temporada.temporada_id", nullable=False, description="ID de la temporada")
    equipo_local_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo local")
    equipo_visitante_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo visitante")



class Partido(PartidoBase, table=True):
    partido_id: Optional[int] = Field(default=None, primary_key=True)
    goles_local: Optional[int] = Field(default=0, nullable=False, description="Goles del equipo local")
    goles_visitante: Optional[int] = Field(default=0, nullable=False, description="Goles del equipo visitante")
    estado: str = Field(default="programado", nullable=False, description="Estado del partido (pendiente, en curso, finalizado)")


class PartidoCrear(PartidoBase):
    pass


class PartidoActualizar(SQLModel):
    fecha: Optional[date] = None
    jornada: Optional[int] = None
    estadio: Optional[str] = None
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None