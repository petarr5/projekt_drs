import os
import boto3
import time
import socket
from decimal import Decimal
from event_queue import event_queue

WORKER_ID = socket.gethostname()

DYNAMO_HOST = os.getenv("DYNAMO_HOST", "localhost")

dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
    endpoint_url=f"http://{DYNAMO_HOST}:8000"
)

table = dynamodb.Table("events")

print(f"WORKER {WORKER_ID} started")

while True:
    if not event_queue.empty():
        event = event_queue.get()

        print(f"WORKER {WORKER_ID} processing event {event['eventId']}")

        item = {
            "eventId": event["eventId"],
            "version": Decimal(1),
            "eventName": event["eventName"],
            "eventDetails": event["eventDetails"],
            "payload": event["payload"],
            "lamportClock": Decimal(event["lamportClock"]),
            "timestamp": Decimal(event["timestamp"]),
            "status": event["status"],
            "sourceReplica": event["sourceReplica"],
            "processedBy": WORKER_ID
        }

        table.put_item(Item=item)
        print(f"WORKER {WORKER_ID} stored event")

    time.sleep(0.5)