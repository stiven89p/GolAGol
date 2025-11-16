from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated
from dotenv import load_dotenv
import os

load_dotenv()  # Carga el archivo .env

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")


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