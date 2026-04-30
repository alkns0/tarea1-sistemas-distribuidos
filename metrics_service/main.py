from fastapi import FastAPI
from pydantic import BaseModel #Validación de datos
from typing import Optional
import time

app = FastAPI()
events = []
start_time = time.time()
evictions = 0


class MetricEvent(BaseModel):
    event: str
    latency: float
    query_type: Optional[str] = ""
    zone: Optional[str] = ""
    evicted: Optional[bool] = False

@app.post("/record")
def record(metric: MetricEvent):
    global evictions
    events.append({
        "event": metric.event,
        "latency": metric.latency,
        "query_type": metric.query_type,
        "zone": metric.zone,
        "timestamp": time.time()
    })
    if metric.evicted:
        evictions += 1
    return {"ok": True}

@app.get("/stats")
def get_stats():
    if not events:
        return {"message": "Sin datos aún"}

    hits = [e for e in events if e["event"] == "hit"]
    misses = [e for e in events if e["event"] == "miss"]
    total = len(events)

    all_latencies = sorted([e["latency"] for e in events])
    hit_latencies = sorted([e["latency"] for e in hits])
    miss_latencies = sorted([e["latency"] for e in misses])

    def percentile(data, p):
        if not data:
            return 0
        idx = int(len(data) * p / 100)
        return data[min(idx, len(data) - 1)]

    elapsed = time.time() - start_time
    elapsed_minutes = elapsed / 60


    t_cache = sum(hit_latencies) / len(hit_latencies) if hit_latencies else 0
    t_db = sum(miss_latencies) / len(miss_latencies) if miss_latencies else 0
    n_hits = len(hits)
    n_misses = len(misses)

    cache_efficiency = ((n_hits * t_cache) - (n_misses * t_db)) / total if total > 0 else 0

    #METRICAS RETORNADAS
    return {
        "hit_rate": round(n_hits / total, 4) if total > 0 else 0,
        "throughput_rps": round(total / elapsed, 4) if elapsed > 0 else 0,
        "latency_p50": round(percentile(all_latencies, 50), 6),
        "latency_p95": round(percentile(all_latencies, 95), 6),
        "eviction_rate_per_min": round(evictions / elapsed_minutes, 4) if elapsed_minutes > 0 else 0,
        "cache_efficiency": round(cache_efficiency, 6)
    }

@app.get("/health")
def health():
    return {"status": "ok", "total_events": len(events)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
