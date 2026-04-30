from fastapi import FastAPI
import redis
import httpx
import json
import os
import time

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
RESPONSE_GENERATOR_URL = os.getenv("RESPONSE_GENERATOR_URL", "http://localhost:8001")
METRICS_URL = os.getenv("METRICS_URL", "http://localhost:8002")
CACHE_TTL = int(os.getenv("CACHE_TTL", 60))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def build_cache_key(query_type: str, params: dict) -> str:
    sorted_params = ":".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{query_type}:{sorted_params}"

def send_metric(event: str, latency: float, extra: dict = {}):
    try:
        with httpx.Client() as client:
            client.post(f"{METRICS_URL}/record", json={
                "event": event, "latency": latency, **extra
            }, timeout=1.0)
    except Exception:
        pass

@app.get("/query")
def handle_query(query_type: str, zone_id: str = None, zone_a: str = None,
                 zone_b: str = None, confidence_min: float = 0.0, bins: int = 5):
    
    params = {}
    if zone_id:
        params["zone_id"] = zone_id
    if zone_a:
        params["zone_a"] = zone_a
    if zone_b:
        params["zone_b"] = zone_b
    if query_type != "q5":
        params["confidence_min"] = confidence_min
    else:
        params["bins"] = bins

    cache_key = build_cache_key(query_type, params)
    start = time.time()

    # hit en caché
    cached = r.get(cache_key)
    if cached:
        latency = time.time() - start
        send_metric("hit", latency, {"query_type": query_type, "zone": zone_id or f"{zone_a}-{zone_b}"})
        return {"source": "cache", "data": json.loads(cached), "latency": latency}

    # delegar
    with httpx.Client() as client:
        response = client.get(f"{RESPONSE_GENERATOR_URL}/{query_type}", params=params, timeout=10.0)
        result = response.json()

    latency = time.time() - start

    #cache con ttl
    r.setex(cache_key, CACHE_TTL, json.dumps(result))
    send_metric("miss", latency, {"query_type": query_type, "zone": zone_id or f"{zone_a}-{zone_b}"})

    return {"source": "generator", "data": result, "latency": latency}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
