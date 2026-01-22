import boto3
from datetime import datetime
import uuid

REGION = "us-east-1"   # ovo već znamo iz poruke errora
TABLE_NAME = "events"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

event = {
    "id": str(uuid.uuid4()),
    "timestamp": datetime.utcnow().isoformat(),
    "title": "Prvi test event",
    "location": "BiH"
}

try:
    table.put_item(Item=event)
    print(" Event uspješno spremljen:")
    print(event)

    response = table.scan()
    print("\n Eventi u tablici:")
    for item in response["Items"]:
        print(item)

except Exception as e:
    print(" Greška:", e)