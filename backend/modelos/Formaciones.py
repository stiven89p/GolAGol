from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class FormacionBase(SQLModel):
    equipo_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo dueño de la formación")
    portero_id: int = Field(foreign_key="jugador.jugador_id", nullable=False, description="ID del jugador que es portero")
    defensas: int = Field(default=0, ge=0, le=10, description="Cantidad de defensas en la formación")
    mediocampistas: int = Field(default=0, ge=0, le=10, description="Cantidad de mediocampistas en la formación")
    delanteros: int = Field(default=0, ge=0, le=10, description="Cantidad de delanteros en la formación")

class Formacion(FormacionBase, table=True):
    formacion_id: Optional[int] = Field(default=None, primary_key=True)
    jugadores: List["FormacionJugador"] = Relationship(back_populates="formacion")

class FormacionCrear(FormacionBase):
    pass

class FormacionDTO(SQLModel):
    formacion_id: int
    equipo_id: int
    portero_id: int
    defensas: int
    mediocampistas: int
    delanteros: int
    titulares: list[dict]
    suplentes: list[dict]
    total: int = 11


class FormacionJugador(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    formacion_id: int = Field(foreign_key="formacion.formacion_id", nullable=False)
    jugador_id: int = Field(foreign_key="jugador.jugador_id", nullable=False)
    titular: bool = Field(default=True, description="True si es parte del 11 inicial, False si es suplente")
    posicion: str = Field(description="Posición del jugador en el momento de registrar la formación")
    formacion: Optional[Formacion] = Relationship(back_populates="jugadores")