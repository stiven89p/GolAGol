from typing import Optional
from sqlmodel import SQLModel, Field
from utils.enumeraciones import TipoEvento

class EventoBase(SQLModel):
    minuto: int = Field(nullable=False, description="Minuto del evento")
    tipo: TipoEvento = Field(nullable=False, description="Tipo de evento")
    descripcion: Optional[str] = Field(default=None, description="Descripción adicional del evento")
    partido_id: int = Field(foreign_key="partido.partido_id", nullable=False, description="ID del partido asociado")
    equipo_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo asociado")
    jugador_id: int = Field(foreign_key="jugador.jugador_id", nullable=False, description="ID del jugador asociado")
    jugador_asociado_id: Optional[int] = Field(default=None, foreign_key="jugador.jugador_id", description="ID del jugador asociado (para sustituciones u otros eventos)")

class Evento(EventoBase, table=True):
    id_evento: Optional[int] = Field(default=None, primary_key=True)

class EventoCrear(EventoBase):
    pass

class EventoActualizar(SQLModel):
    minuto: Optional[int] = None
    tipo: Optional[TipoEvento] = None
    descripcion: Optional[str] = None
    partido_id: Optional[int] = None
    equipo_id: Optional[int] = None
    jugador_id: Optional[int] = None
    jugador_asociado_id: Optional[int] = None
