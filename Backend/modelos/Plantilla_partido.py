from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Plantilla_PartidoBase(SQLModel):
    partido_id: int = Field(foreign_key="partido.partido_id", nullable=False, description="ID del partido")
    jugador_id: int = Field(foreign_key="jugador.jugador_id", nullable=False, description="ID del jugador")
    equipo: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo")

class Plantilla_Partido(Plantilla_PartidoBase, table=True):
    pass

class Plantilla_PartidoCrear(Plantilla_PartidoBase):
    pass

class Plantilla_PartidoActualizar(SQLModel):
    partido_id: Optional[int] = None
    jugador_id: Optional[int] = None
    equipo: Optional[int] = None