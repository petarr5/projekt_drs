from mpi4py import MPI
import os
import boto3
import time
import random
import socket
from decimal import Decimal

# MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
hostname = socket.gethostname()

TABLE_NAME = "events"
MASTER_IP = os.getenv("DYNAMO_HOST", "localhost")
DYNAMO_URL = f"http://{MASTER_IP}:8000"

# DynamoDB Local client
dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url=DYNAMO_URL,
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)
table = dynamodb.Table(TABLE_NAME)

lamport_clock = 0

def tick():
    global lamport_clock
    lamport_clock += 1
    return lamport_clock

# ================= MASTER =================
if rank == 0:
    print(f"\n MASTER pokrenut na {hostname}")
    print(f" Ukupno procesa: {size}")

    event_id = f"conflict-event-{int(time.time())}"

    # šalje isti event svim workerima
    for worker in range(1, size):
        comm.send(event_id, dest=worker, tag=1)

    print(f" MASTER poslao eventId = {event_id} svim workerima")

    # čeka potvrde
    for worker in range(1, size):
        msg = comm.recv(source=worker, tag=2)
        print(f" MASTER primio: {msg}")

    print("\n Svi workeri završili.\n")

# ================= WORKERI =================
else:
    print(f" WORKER {rank} pokrenut na {hostname}")

    # primi eventId
    event_id = comm.recv(source=0, tag=1)
    print(f" WORKER {rank} primio eventId = {event_id}")

    # slučajno kašnjenje → konflikt
    time.sleep(random.uniform(0.5, 2.0))

    clock = tick()

    item = {
        "eventId": event_id,
        "version": 1,
        "userId": f"worker-{rank}",
        "lamportClock": clock,
        "status": "UPDATED",
        "timestamp": int(time.time())
    }

    table.put_item(Item=item)

    print(f" WORKER {rank} upisao zapis (clock={clock})")

    # javi masteru
    comm.send(f"worker-{rank} završio na {hostname}", dest=0, tag=2)