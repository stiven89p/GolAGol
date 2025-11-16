import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from backend.db import get_session
from main import app
from backend.modelos.Equipos import Equipo
import io


# Configuración de base de datos en memoria para tests
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ==================== TESTS PARA CREAR EQUIPOS ====================

def test_crear_equipo_con_logo_real(client: TestClient):
    """Test para crear un equipo usando un archivo real de escudo"""
    file_path = r"C:\Users\eposa\OneDrive\Escritorio\escudos\santafe.png"
    with open(file_path, "rb") as f:
        files = {
            "file": ("santafe.png", f, "image/png")
        }
        data = {
            "nombre": "Santa Fe",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1941,
            "titulos": 9
        }
        response = client.post("/equipos/", data=data, files=files)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["nombre"] == "Santa Fe"
    # Puedes agregar más asserts si lo necesitas