from fastapi import FastAPI
import redis
import json
import os

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 60))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

def build_cache_key(query_type: str, params: dict) -> str:
    sorted_params = ":".join(
        f"{k}={v}"
        for k, v in sorted(params.items())
    )

    return f"{query_type}:{sorted_params}"


@app.post("/lookup")
def lookup(payload: dict):

    query_type = payload["query_type"]
    params = payload["params"]

    cache_key = build_cache_key(
        query_type,
        params
    )

    cached = r.get(cache_key)

    if cached:

        return {
            "hit": True,
            "data": json.loads(cached)
        }

    return {
        "hit": False
    }


@app.post("/store")
def store(payload: dict):

    query_type = payload["query_type"]
    params = payload["params"]
    result = payload["result"]

    cache_key = build_cache_key(
        query_type,
        params
    )

    r.setex(
        cache_key,
        CACHE_TTL,
        json.dumps(result)
    )

    return {
        "stored": True
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )