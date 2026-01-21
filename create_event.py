import boto3
import time
import random

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url='http://localhost:8000',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('events')

event_id = f"e{random.randint(1000,9999)}"

item = {
    "eventId": event_id,
    "version": 1,
    "userId": "user-1",
    "timestamp": int(time.time()),
    "status": "CREATED",
    "lamportClock": 1,
    "payload": "demo-event"
}

table.put_item(Item=item)
print(" Event kreiran:", event_id)