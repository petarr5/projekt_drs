from fastapi import FastAPI, Request
import requests
import itertools

app = FastAPI()

BACKENDS = [
    "http://localhost:8081/",
    "http://localhost:8082/",
    "http://localhost:8083/",
]

cycle = itertools.cycle(BACKENDS)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request):
    backend = next(cycle)   # round-robin

    url = f"{backend}/{path}"
    method = request.method
    body = await request.body()
    headers = dict(request.headers)

    print("Forwarding to:", backend)

    resp = requests.request(
        method,
        url,
        data=body,
        headers=headers
    )

    return resp.json()