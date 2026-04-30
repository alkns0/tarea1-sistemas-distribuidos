import httpx
import numpy as np
import time
import os
import random

CACHE_URL = os.getenv("CACHE_SERVICE_URL", "http://localhost:8000") #Coneccion con cache_service
DISTRIBUTION = os.getenv("DISTRIBUTION", "zipf") #Tipo de distribución
NUM_REQUESTS = int(os.getenv("NUM_REQUESTS", 1000)) #1000 requests
RATE = float(os.getenv("RATE", 10))

#Zonas y tipo de queries
ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERY_TYPES = ["q1", "q2", "q3", "q4", "q5"]
CONFIDENCE_VALUES = [0.0, 0.5, 0.7, 0.9]


#Distribución ZIPF de trafico
def zipf_distribution(n, s=1.5):
    weights = np.array([1 / (i ** s) for i in range(1, n + 1)])
    weights /= weights.sum()
    return weights


#Generación de trafico 
def generate_request(distribution="zipf"):
    if distribution == "zipf":

        zone_weights = zipf_distribution(len(ZONES))
        zone_id = np.random.choice(ZONES, p = zone_weights)

        query_weights = zipf_distribution(len(QUERY_TYPES))
        query_type = np.random.choice(QUERY_TYPES, p = query_weights)

    else:  # uniforme
        zone_id = random.choice(ZONES)
        query_type = random.choice(QUERY_TYPES)

    confidence_min = random.choice(CONFIDENCE_VALUES)
    params = {"query_type": query_type, "confidence_min": confidence_min}

    if query_type == "q4":
        zone_b = random.choice([z for z in ZONES if z != zone_id])
        params["zone_a"] = zone_id
        params["zone_b"] = zone_b

    elif query_type == "q5":
        params["zone_id"] = zone_id
        params["bins"] = random.choice([5, 10])
        del params["confidence_min"]

    else:
        params["zone_id"] = zone_id

    return params

#Corre la generacion de trafico
def run():
    print(f"Iniciando generador de tráfico: {NUM_REQUESTS} requests, distribución={DISTRIBUTION}, rate={RATE} req/s")
    interval = 1.0 / RATE
    
    for i in range(NUM_REQUESTS):
        params = generate_request(DISTRIBUTION)
        try:
            with httpx.Client() as client:
                resp = client.get(f"{CACHE_URL}/query", params=params, timeout=10.0)
                data = resp.json()
                print(f"[{i+1}/{NUM_REQUESTS}] {params['query_type']} | source={data.get('source')} | latency={data.get('latency', 0):.4f}s")
        except Exception as e:
            print(f"Error en request {i}: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    time.sleep(5) 
    run()