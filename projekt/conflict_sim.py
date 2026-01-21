from mpi4py import MPI
import boto3
import time
import socket
from decimal import Decimal
from botocore.exceptions import ClientError

# ---------------- MPI ----------------
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
host = socket.gethostname()

MASTER_IP = "ip-172-31-27-56"   # tvoj master

# ---------------- DynamoDB ----------------
dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
    endpoint_url=f"http://{MASTER_IP}:8000"
)

table = dynamodb.Table("events")

EVENT_ID = "conflict-event"
VERSION = 1   # mora postojati jer je SORT KEY

# ---------------- MASTER ----------------
def master_create_base_event():
    item = {
        "eventId": EVENT_ID,
        "version": VERSION,
        "payload": "base",
        "lamportClock": Decimal(1),
        "status": "BASE",
        "timestamp": Decimal(int(time.time()))
    }

    table.put_item(Item=item)
    print(f"\nMASTER ({host}) -> Base event created")

    # signal workerima da krenu
    comm.bcast(True, root=0)

# ---------------- WORKER ----------------
def worker_update():
    # čekaj master signal
    comm.bcast(None, root=0)

    # svaki worker ima svoj lokalni Lamport clock
    local_clock = rank + 1
    new_status = f"UPDATED_BY_WORKER_{rank}"

    print(f"WORKER {rank} ({host}) -> pokusava update (clock={local_clock})")

    try:
        table.update_item(
            Key={
                "eventId": EVENT_ID,
                "version": VERSION
            },
            UpdateExpression="""
                SET lamportClock = :c,
                    #st = :s,
                    #ts = :t
            """,
            # mapiranje rezerviranih riječi
            ExpressionAttributeNames={
                "#st": "status",
                "#ts": "timestamp"
            },
            ExpressionAttributeValues={
                ":c": Decimal(local_clock),
                ":s": new_status,
                ":t": Decimal(int(time.time()))
            },

            # ✅ DETEKCIJA KONFLIKTA:
            # update je dozvoljen samo ako je moj clock veći
            ConditionExpression="lamportClock < :c"
        )

        print(f"WORKER {rank} ({host}) -> UPDATE OK ")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print(f"WORKER {rank} ({host}) -> KONFLIKT  (netko je vec upisao veci clock)")
        else:
            print(f"WORKER {rank} ({host}) -> GRESKA: {e}")

# ---------------- FINAL READ (MASTER) ----------------
def master_read_final():
    time.sleep(2)

    response = table.get_item(
        Key={
            "eventId": EVENT_ID,
            "version": VERSION
        }
    )

    print("\nFINAL STATE IN DATABASE:")
    print(response.get("Item"))

# ---------------- MAIN ----------------
if rank == 0:
    master_create_base_event()
    master_read_final()
else:
    worker_update()