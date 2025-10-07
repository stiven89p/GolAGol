from sqlmodel import SQLModel, Field, Relationship

class EquipoBase(SQLModel):
    nombre: str | None = Field(description="nombre del equipo")
    ciudad: str | None = Field(description="ciudad del equipo")
    estadio: str | None = Field(description="estadio del equipo")
    anio_fundacion: int | None = Field(description="año de fundacion del equipo")

class Equipo(EquipoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class EquipoCrear(EquipoBase):
    pass