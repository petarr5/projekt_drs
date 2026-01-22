import boto3

EVENT_ID = input("Unesi eventId za brisanje: ")

dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url='http://localhost:8000',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

table = dynamodb.Table('events')

table.delete_item(
    Key={"eventId": EVENT_ID, "version": 1}
)

print(" Event obrisan:", EVENT_ID)