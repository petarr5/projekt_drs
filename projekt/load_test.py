import requests
import random
import time
import os
import uuid

REPLICAS = os.getenv("REPLICAS", "").split(",")

if not REPLICAS or REPLICAS == [""]:
    raise Exception("REPLICAS env var not set")

print("Load test started...")
print("Replicas:", REPLICAS)

users = ["dragan", "mate", "ela", "petar"]

counter = 0

while counter < 50:   # pošalji 50 događaja
    replica = random.choice(REPLICAS)

    payload = {
        "userId": random.choice(users),
        "description": f"Load test event #{counter}",
        "request_id": str(uuid.uuid4())
    }

    try:
        r = requests.post(
            f"{replica}/events",
            json=payload,
            timeout=6
        )

        print(f"Sent to {replica} -> {r.status_code}")

        if r.status_code != 200:
            print("Response:", r.text)

    except Exception as e:
        print(f"{replica} FAILED:", e)

    counter += 1
    time.sleep(0.5)

print("Load test finished.")