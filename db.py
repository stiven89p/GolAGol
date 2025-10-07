from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated

# Datos de conexión a PostgreSQL
db_user = "postgres"
db_password = "3621518"
db_host = "localhost"
db_port = ("5433")
db_name = "GolAGol"

# URL de conexión PostgreSQL
db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Crea el engine de SQLAlchemy/SQLModel
engine = create_engine(db_url, echo=True, connect_args={"client_encoding": "utf8"})

# Crear las tablas cuando se inicia la app
def create_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# Sesión de base de datos
def get_session() -> Session:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]