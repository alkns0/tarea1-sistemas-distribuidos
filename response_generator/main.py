from fastapi import FastAPI
import pandas as pd
import numpy as np
import uvicorn
import os
import time
import random

app = FastAPI()

DATA_PATH = os.getenv("DATA_PATH", "/data/buildings.csv")

# Configurable desde docker-compose
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.2"))

# Zonas predefinidas
ZONES = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

# Precargar datos por zona en memoria
data = {}


def simulate_failure():
    """
    Simula fallas temporales para probar:
    - Retry Topic
    - DLQ
    - Recovery Rate
    - Recovery Time
    """
    if random.random() < FAILURE_RATE:
        raise Exception("Temporary failure")


def load_data():
    df = pd.read_csv(
        DATA_PATH,
        usecols=["latitude", "longitude", "area_in_meters", "confidence"]
    )

    for zone_id, bbox in ZONES.items():
        mask = (
            (df["latitude"] >= bbox["lat_min"])
            & (df["latitude"] <= bbox["lat_max"])
            & (df["longitude"] >= bbox["lon_min"])
            & (df["longitude"] <= bbox["lon_max"])
        )

        data[zone_id] = df[mask].to_dict("records")

        print(
            f"Zona {zone_id}: "
            f"{len(data[zone_id])} edificios cargados"
        )


def zone_area_km2(zone_id):
    z = ZONES[zone_id]

    lat_diff = abs(z["lat_max"] - z["lat_min"]) * 111

    lon_diff = (
        abs(z["lon_max"] - z["lon_min"])
        * 111
        * np.cos(
            np.radians(
                (z["lat_max"] + z["lat_min"]) / 2
            )
        )
    )

    return lat_diff * lon_diff


@app.on_event("startup")
def startup():
    load_data()


@app.get("/q1")
def q1_count(zone_id: str, confidence_min: float = 0.0):

    time.sleep(0.05)
    simulate_failure()

    records = data.get(zone_id, [])

    count = sum(
        1
        for r in records
        if r["confidence"] >= confidence_min
    )

    return {
        "zone_id": zone_id,
        "count": count,
        "confidence_min": confidence_min
    }


@app.get("/q2")
def q2_area(zone_id: str, confidence_min: float = 0.0):

    time.sleep(0.05)
    simulate_failure()

    records = data.get(zone_id, [])

    areas = [
        r["area_in_meters"]
        for r in records
        if r["confidence"] >= confidence_min
    ]

    if not areas:
        return {
            "zone_id": zone_id,
            "avg_area": 0,
            "total_area": 0,
            "n": 0
        }

    return {
        "zone_id": zone_id,
        "avg_area": np.mean(areas),
        "total_area": sum(areas),
        "n": len(areas)
    }


@app.get("/q3")
def q3_density(zone_id: str, confidence_min: float = 0.0):

    time.sleep(0.05)
    simulate_failure()

    count_result = q1_count(zone_id, confidence_min)

    area = zone_area_km2(zone_id)

    return {
        "zone_id": zone_id,
        "density_per_km2":
            count_result["count"] / area
            if area > 0 else 0
    }


@app.get("/q4")
def q4_compare(
    zone_a: str,
    zone_b: str,
    confidence_min: float = 0.0
):

    time.sleep(0.05)
    simulate_failure()

    da = q3_density(
        zone_a,
        confidence_min
    )["density_per_km2"]

    db = q3_density(
        zone_b,
        confidence_min
    )["density_per_km2"]

    return {
        "zone_a": zone_a,
        "density_a": da,
        "zone_b": zone_b,
        "density_b": db,
        "winner": zone_a if da > db else zone_b
    }


@app.get("/q5")
def q5_confidence_dist(
    zone_id: str,
    bins: int = 5
):

    time.sleep(0.05)
    simulate_failure()

    records = data.get(zone_id, [])

    scores = [
        r["confidence"]
        for r in records
    ]

    if not scores:
        return []

    counts, edges = np.histogram(
        scores,
        bins=bins,
        range=(0, 1)
    )

    return [
        {
            "bucket": i,
            "min": float(edges[i]),
            "max": float(edges[i + 1]),
            "count": int(counts[i])
        }
        for i in range(bins)
    ]


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001
    )