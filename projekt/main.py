from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import time
import random

app = FastAPI(title="Quorum Read / Write Demo")

# -------------------------
# Quorum configuration
# -------------------------
N = 3   # broj replika
W = 2   # write quorum
R = 2   # read quorum

if R + W <= N:
    raise Exception("Invalid quorum configuration!")

# -------------------------
# Simulated replicas
# -------------------------
# Svaka replika je jednostavan dictionary
replicas: List[Dict[str, dict]] = [
    {}, {}, {}
]

# -------------------------
# Models
# -------------------------
class WriteRequest(BaseModel):
    key: str
    value: str


class ReadResponse(BaseModel):
    key: str
    value: str
    version: float
    replicas_used: int

# -------------------------
# Helpers
# -------------------------
def now_version():
    return time.time()


def write_to_replica(replica_id: int, key: str, value: str, version: float) -> bool:
    """
    Simulira upis na repliku.
    Namjerno ponekad faila da simulira mrežne probleme.
    """
    if random.random() < 0.1:   # 10% šanse da replika ne odgovori
        return False

    replicas[replica_id][key] = {
        "value": value,
        "version": version
    }
    return True


def read_from_replica(replica_id: int, key: str):
    """
    Čitanje sa replike.
    """
    return replicas[replica_id].get(key)

# -------------------------
# WRITE (Quorum)
# -------------------------
@app.post("/write")
def quorum_write(req: WriteRequest):
    version = now_version()
    acks = 0

    for replica_id in range(N):
        success = write_to_replica(replica_id, req.key, req.value, version)
        if success:
            acks += 1

        if acks >= W:
            break

    if acks < W:
        raise HTTPException(
            status_code=500,
            detail=f"Write failed – only {acks}/{W} replicas acknowledged"
        )

    return {
        "message": "Write successful",
        "key": req.key,
        "value": req.value,
        "version": version,
        "acks": acks
    }

# -------------------------
# READ (Quorum)
# -------------------------
@app.get("/read/{key}", response_model=ReadResponse)
def quorum_read(key: str):
    responses = []

    for replica_id in range(N):
        data = read_from_replica(replica_id, key)
        if data:
            responses.append(data)

        if len(responses) >= R:
            break

    if len(responses) < R:
        raise HTTPException(
            status_code=404,
            detail=f"Read failed – only {len(responses)}/{R} replicas responded"
        )

    # Uzmi najnoviju verziju
    latest = max(responses, key=lambda x: x["version"])

    return {
        "key": key,
        "value": latest["value"],
        "version": latest["version"],
        "replicas_used": len(responses)
    }

# -------------------------
# DEBUG – stanje replika
# -------------------------
@app.get("/replicas")
def show_replicas():
    return replicas