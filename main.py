from fastapi import FastAPI

import routers.Equipos
from db import create_tables
app = FastAPI(lifespan=create_tables, title="Gol a Gol API")
app.include_router(routers.Equipos.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
