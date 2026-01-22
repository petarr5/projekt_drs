from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time

app = FastAPI(title="Replica Node")

storage = {}

class WriteRequest(BaseModel):
    key: str
    value: str
    version: float

@app.post("/write")
def write(req: WriteRequest):
    current = storage.get(req.key)

    if current and current["version"] > req.version:
        raise HTTPException(status_code=409, detail="Stale write")

    storage[req.key] = {
        "value": req.value,
        "version": req.version
    }

    return {"status": "ok"}

@app.get("/read/{key}")
def read(key: str):
    if key not in storage:
        raise HTTPException(status_code=404, detail="Not found")
    return storage[key]

@app.get("/data")
def data():
    return storage