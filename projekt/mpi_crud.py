from mpi4py import MPI
import boto3
import socket
import sys
import time

# ---------------- MPI ----------------
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
hostname = socket.gethostname()

# ---------------- DynamoDB Local ----------------
dynamodb = boto3.resource(
    "dynamodb",
    region_name="us-east-1",
    endpoint_url="http://172.31.27.56:8000",
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy"
)

table = dynamodb.Table("events")

# ---------------- Operacije ----------------
def create_event(event_id):
    item = {
        "eventId": event_id,
        "version": 1,
        "userId": f"worker-{rank}",
        "status": "CREATED",
        "timestamp": int(time.time()),
        "lamportClock": rank
    }
    table.put_item(Item=item)
    return f"WORKER {rank} ({hostname}) -> CREATE OK"

def read_event(event_id):
    r = table.get_item(Key={"eventId": event_id, "version": 1})
    return f"WORKER {rank} ({hostname}) -> READ: {r.get('Item')}"

def update_event(event_id):
    table.update_item(
        Key={"eventId": event_id, "version": 1},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": f"UPDATED_BY_{rank}"}
    )
    return f"WORKER {rank} ({hostname}) -> UPDATE OK"

def delete_event(event_id):
    table.delete_item(Key={"eventId": event_id, "version": 1})
    return f"WORKER {rank} ({hostname}) -> DELETE OK"

# ---------------- MASTER ----------------
if rank == 0:
    if len(sys.argv) < 3:
        print("Koristi: mpiexec -n 4 python3 mpi_crud.py <create|read|update|delete> <eventId>")
        sys.exit(0)

    operation = sys.argv[1]
    event_id  = sys.argv[2]

    print(f"\nMASTER ({hostname}) pokrece operaciju: {operation.upper()} za eventId={event_id}")
    print(f"Ukupno procesa: {size}\n")

    # šalji zadatak workerima
    for dest in range(1, size):
        comm.send((operation, event_id), dest=dest)

    # primi odgovore
    for src in range(1, size):
        msg = comm.recv(source=src)
        print(msg)

# ---------------- WORKERI ----------------
else:
    operation, event_id = comm.recv(source=0)

    if operation == "create":
        result = create_event(event_id)

    elif operation == "read":
        result = read_event(event_id)

    elif operation == "update":
        result = update_event(event_id)

    elif operation == "delete":
        result = delete_event(event_id)

    else:
        result = f"WORKER {rank}: Nepoznata operacija"

    comm.send(result, dest=0)