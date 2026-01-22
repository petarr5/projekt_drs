from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import time

app = FastAPI(title="Quorum Coordinator")

REPLICAS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003"
]

N = len(REPLICAS)
W = 2
R = 2

if R + W <= N:
    raise Exception("Invalid quorum config!")

class WriteRequest(BaseModel):
    key: str
    value: str

@app.post("/write")
def quorum_write(req: WriteRequest):
    version = time.time()
    acks = 0
    errors = []

    for replica in REPLICAS:
        try:
            r = requests.post(
                f"{replica}/write",
                json={
                    "key": req.key,
                    "value": req.value,
                    "version": version
                },
                timeout=1
            )
            if r.status_code == 200:
                acks += 1
        except Exception as e:
            errors.append(str(e))

    if acks < W:
        raise HTTPException(
            status_code=500,
            detail=f"Write failed: only {acks}/{W} replicas acknowledged"
        )

    return {
        "message": "Write successful",
        "acks": acks,
        "version": version
    }

@app.get("/read/{key}")
def quorum_read(key: str):
    responses = []

    for replica in REPLICAS:
        try:
            r = requests.get(f"{replica}/read/{key}", timeout=1)
            if r.status_code == 200:
                responses.append(r.json())
        except:
            pass

        if len(responses) >= R:
            break

    if len(responses) < R:
        raise HTTPException(
            status_code=404,
            detail=f"Read failed: only {len(responses)}/{R} replicas responded"
        )


    latest = max(responses, key=lambda x: x["version"])

    return {
        "key": key,
        "value": latest["value"],
        "version": latest["version"],
        "replicas_used": len(responses)
    }