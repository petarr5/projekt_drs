import boto3
import time

EVENT_ID = input("Unesi eventId za update: ")

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url='http://localhost:8000/',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('events')

new_status = "UPDATED"
new_lamport = int(time.time())

table.update_item(
    Key={"eventId": EVENT_ID, "version": 1},
    UpdateExpression="SET #s = :s, lamportClock = :l",
    ExpressionAttributeNames={"#s": "status"},
    ExpressionAttributeValues={
        ":s": new_status,
        ":l": new_lamport
    }
)

print(" Event ažuriran:", EVENT_ID)
