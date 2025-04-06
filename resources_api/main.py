from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from models import Resource1
from crud import create_resource, get_resource, update_resource, delete_resource

app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/resources/", response_model=Resource1)
def create_resource_endpoint(resource: Resource1):
    with Session(engine) as session:
        return create_resource(session, resource)

@app.get("/resources/{resource_id}", response_model=Resource1)
def get_resource_endpoint(resource_id: int):
    with Session(engine) as session:
        resource = get_resource(session, resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        return resource

@app.put("/resources/{resource_id}", response_model=Resource1)
def update_resource_endpoint(resource_id: int, resource: Resource1):
    with Session(engine) as session:
        return update_resource(session, resource_id, resource)

@app.delete("/resources/{resource_id}")
def delete_resource_endpoint(resource_id: int):
    with Session(engine) as session:
        delete_resource(session, resource_id)
        return {"ok": True}