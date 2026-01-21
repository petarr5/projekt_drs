import requests
import time
import random
import os
import uuid

# ---------------- CONFIG ----------------
REPLICAS = os.getenv("REPLICAS", "")
if not REPLICAS:
    raise Exception("REPLICAS environment variable is not set!")

REPLICA_URLS = [r.strip() for r in REPLICAS.split(",")]

print("\nFault tolerance demo started...")
print("Using replicas:")
for r in REPLICA_URLS:
    print(" ", r)

TIMEOUT = 6        # veći timeout (DynamoDB zna biti spor)
DELAY = 0.5        # mali razmak između zahtjeva

# ---------------- FUNCTIONS ----------------
def send_request():
    """
    Pokušava poslati zahtjev na jednu od replika.
    Ako jedna padne – automatski pokušava drugu.
    """

    random.shuffle(REPLICA_URLS)

    payload = {
        "userId": f"user-{random.randint(1,3)}",
        "description": "fault-tolerance-test",
        "request_id": str(uuid.uuid4())
    }

    for url in REPLICA_URLS:
        try:
            r = requests.post(
                f"{url}/events",
                json=payload,
                timeout=TIMEOUT
            )

            print(f" {url} -> {r.status_code}")

            if r.status_code == 200:
                return True

        except Exception as e:
            print(f" {url} FAILED -> {e}")

    print("  All replicas failed!")
    return False


# ---------------- PHASE 1 ----------------
print("\nPhase 1: All replicas active\n")

for _ in range(10):
    send_request()
    time.sleep(DELAY)


# ---------------- USER ACTION ----------------
print("\n  Now manually STOP one FastAPI replica (CTRL+C on one server)")
print("Waiting 10 seconds...\n")
time.sleep(10)


# ---------------- PHASE 2 ----------------
print("\nPhase 2: One replica down, system continues\n")

for _ in range(15):
    send_request()
    time.sleep(DELAY)

print("\nDemo finished.")