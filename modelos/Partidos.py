from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class PartidoBase(SQLModel):
    fecha: str = Field(nullable=False, description="fecha del partido")
    estadio: str = Field(nullable=False, description="estadio del partido")
    equipo_local_id: int = Field(foreign_key="equipo.id_equipo", nullable=False, description="ID del equipo local")
    equipo_visitante_id: int = Field(foreign_key="equipo.id_equipo", nullable=False, description="ID del equipo visitante")
    goles_local: int = Field(default=0, nullable=False, description="goles del equipo local")
    goles_visitante: int = Field(default=0, nullable=False, description="goles del equipo visitante")

class Partido(PartidoBase, table=True):
    id_partido: int | None = Field(default=None, primary_key=True)

class PartidoCrear(PartidoBase, table=True):
    pass

class PartidoActualizar(SQLModel):
    fecha: Optional[str] = None
    estadio: Optional[str] = None
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None
    goles_local: Optional[int] = None
    goles_visitante: Optional[int] = None


