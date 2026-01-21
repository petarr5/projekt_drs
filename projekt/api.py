from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import boto3
import time
import uuid
import os
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler

# -------------------------
# Logging setup
# -------------------------
LOG_FILE = "event_service.log"

logger = logging.getLogger("event-service")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# Log u datoteku (rotacija)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,   # 5 MB
    backupCount=3
)
file_handler.setFormatter(formatter)

# Log u konzolu
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Event Service started")

# -------------------------
# FastAPI setup
# -------------------------
app = FastAPI(title="Distributed Event Service")

# -------------------------
# DynamoDB setup (LOCAL)
# -------------------------
DYNAMO_HOST = os.getenv("DYNAMO_HOST", "127.0.0.1")

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=f"http://{DYNAMO_HOST}:8000",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)

table = dynamodb.Table("events")

# -------------------------
# Models
# -------------------------
class EventCreate(BaseModel):
    userId: str
    description: str
    request_id: str


class EventUpdate(BaseModel):
    description: str
    expected_version: int

# -------------------------
# Helpers
# -------------------------
def now_ts() -> int:
    return int(time.time())


def make_idempotency_key(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def check_idempotency(idempotency_key: str):
    response = table.scan(
        FilterExpression="idempotency_key = :k",
        ExpressionAttributeValues={":k": idempotency_key}
    )
    if response.get("Items"):
        return response["Items"][0]
    return None


def get_latest_event(event_id: str):
    response = table.scan(
        FilterExpression="eventId = :e",
        ExpressionAttributeValues={":e": event_id}
    )

    items = response.get("Items", [])
    if not items:
        return None

    latest = max(items, key=lambda e: int(e["version"]))
    return latest

# -------------------------
# CREATE EVENT (idempotent)
# -------------------------
@app.post("/events")
def create_event(event: EventCreate):
    logger.info(f"CREATE event user={event.userId} desc={event.description}")
    idempotency_payload = {
        "op": "POST",
        "userId": event.userId,
        "description": event.description
    }

    idem_key = make_idempotency_key(idempotency_payload)
    existing = check_idempotency(idem_key)

    if existing:
        logger.info(f"Idempotent POST – event already exists: {existing['eventId']}")
        return {
            "message": "Idempotent POST – event already exists",
            "event": existing
        }

    event_id = str(uuid.uuid4())
    ts = now_ts()

    item = {
        "eventId": event_id,
        "version": 1,
        "userId": event.userId,
        "description": event.description,
        "timestamp": Decimal(ts),
        "idempotency_key": idem_key,
        "request_id": event.request_id,
        "deleted": False
    }

    table.put_item(Item=item)

    logger.info(f"Event created: {event_id}")
    return {
        "message": "Event created",
        "event": item
    }

# -------------------------
# QUERY EVENTS (with filters)
# -------------------------
@app.get("/events/query")
def query_events(
    userId: Optional[str] = Query(None),
    startTime: Optional[int] = Query(None),
    endTime: Optional[int] = Query(None)
):
    logger.info(f"QUERY events user={userId} from={startTime} to={endTime}")

    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    logger.info(f"Total items scanned: {len(items)}")

    if not items:
        return {"count": 0, "events": []}

    # Najnovija verzija po eventId
    latest = {}
    for e in items:
        eid = str(e.get("eventId"))
        version_raw = e.get("version", 0)
        try:
            version = int(version_raw)
        except Exception:
            version = 0

        if eid not in latest or version > int(latest[eid].get("version", 0)):
            latest[eid] = e

    events = list(latest.values())

    now = now_ts()
    if startTime is None and endTime is None:
        startTime = now - 24 * 60 * 60
        endTime = now

    filtered = []
    for event in events:
        if event.get("deleted"):
            continue

        if userId is not None:
            if str(event.get("userId", "")).strip() != str(userId).strip():
                continue

        try:
            ts = int(float(event.get("timestamp", 0)))
        except Exception:
            continue

        if startTime is not None and ts < int(startTime):
            continue
        if endTime is not None and ts > int(endTime):
            continue

        filtered.append(event)

    filtered.sort(key=lambda e: int(float(e.get("timestamp", 0))), reverse=True)

    logger.info(f"Filtered events count: {len(filtered)}")
    return {
        "filters": {"userId": userId, "startTime": startTime, "endTime": endTime},
        "count": len(filtered),
        "events": filtered
    }

# -------------------------
# GET ALL EVENTS (latest only)
# -------------------------
@app.get("/events")
def get_all_events():
    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    latest = {}
    for e in items:
        eid = e["eventId"]
        if eid not in latest or int(e["version"]) > int(latest[eid]["version"]):
            latest[eid] = e

    events = [e for e in latest.values() if not e.get("deleted")]
    events.sort(key=lambda e: int(e["timestamp"]), reverse=True)

    logger.info(f"GET all events – total returned: {len(events)}")
    return {"count": len(events), "events": events}

# -------------------------
# GET EVENT (latest version)
# -------------------------
@app.get("/events/{event_id}")
def get_event(event_id: str):
    read_start = time.time()
    item = get_latest_event(event_id)

    if not item or item.get("deleted"):
        logger.warning(f"GET event failed – not found: {event_id}")
        raise HTTPException(status_code=404, detail="Event not found")

    latency_ms = (time.time() - read_start) * 1000
    logger.info(f"GET event success: {event_id}, latency={latency_ms:.2f}ms")

    return {
        "event": item,
        "consistency": {
            "read_latency_ms": round(latency_ms, 2),
            "note": "Latest version fetched"
        }
    }

# -------------------------
# UPDATE EVENT (optimistic locking)
# -------------------------
@app.put("/events/{event_id}")
def update_event(event_id: str, payload: EventUpdate):
    current = get_latest_event(event_id)

    if not current or current.get("deleted"):
        logger.warning(f"UPDATE event failed – not found: {event_id}")
        raise HTTPException(status_code=404, detail="Event not found")

    current_version = int(current.get("version", 0))

    if current_version != payload.expected_version:
        logger.warning(f"UPDATE event version conflict: {event_id}")
        raise HTTPException(
            status_code=409,
            detail=f"Version conflict: current={current_version}, expected={payload.expected_version}"
        )

    new_item = {
        **current,
        "version": current_version + 1,
        "description": payload.description,
        "timestamp": Decimal(now_ts()),
    }

    table.put_item(Item=new_item)
    logger.info(f"Event updated: {event_id}, new version={new_item['version']}")

    return {
        "message": "Event updated",
        "eventId": event_id,
        "old_version": current_version,
        "new_version": new_item["version"]
    }

# -------------------------
# DELETE EVENT (soft delete)
# -------------------------
@app.delete("/events/{event_id}")
def delete_event(event_id: str):
    current = get_latest_event(event_id)

    if not current or current.get("deleted"):
        logger.warning(f"DELETE event failed – not found: {event_id}")
        raise HTTPException(status_code=404, detail="Event not found")

    deleted_item = {
        **current,
        "version": int(current["version"]) + 1,
        "deleted": True,
        "timestamp": Decimal(now_ts())
    }

    table.put_item(Item=deleted_item)
    logger.info(f"Event deleted: {event_id}, deleted version={deleted_item['version']}")

    return {
        "message": "Event deleted",
        "eventId": event_id,
        "deleted_version": deleted_item["version"]
    }