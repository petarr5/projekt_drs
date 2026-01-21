import boto3

DYNAMO_URL = "http://localhost:8000"
REGION = "us-east-1"

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION,
    endpoint_url=DYNAMO_URL,
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)

table = dynamodb.Table("events")