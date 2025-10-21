from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_crear_equipo():
    response = client.post(
        "/equipos/",
        data={
            "nombre": "Millonarios",
            "ciudad": "Bogotá",
            "estadio": "El Campín",
            "anio_fundacion": 1946,
            "titulos": 16
        }
    )
    assert response.status_code == 200
    result = response.json()

