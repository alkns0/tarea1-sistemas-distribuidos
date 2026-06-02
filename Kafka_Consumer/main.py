import os
import json
import time
import httpx

from kafka import KafkaConsumer

KAFKA_SERVER = os.getenv(
    "KAFKA_SERVER",
    "kafka:9092"
)

CACHE_URL = os.getenv(
    "CACHE_SERVICE_URL",
    "http://cache_service:8000"
)

RESPONSE_GENERATOR_URL = os.getenv(
    "RESPONSE_GENERATOR_URL",
    "http://response_generator:8001"
)

METRICS_URL = os.getenv(
    "METRICS_URL",
    "http://metrics_service:8002"
)

consumer = KafkaConsumer(
    "queries-topic",
    bootstrap_servers=KAFKA_SERVER,
    value_deserializer=lambda m:
        json.loads(m.decode("utf-8")),
    group_id="query-consumers",
    auto_offset_reset="earliest"
)

print("Kafka Consumer iniciado...")


def send_metric(event, latency, query_type):

    try:

        with httpx.Client() as client:

            client.post(
                f"{METRICS_URL}/record",
                json={
                    "event": event,
                    "latency": latency,
                    "query_type": query_type
                },
                timeout=1.0
            )

    except Exception:
        pass


for msg in consumer:

    message = msg.value

    payload = message["payload"]

    query_type = payload["query_type"]

    start = time.time()

    try:

        # -------------------------
        # CACHE LOOKUP
        # -------------------------

        with httpx.Client() as client:

            cache_response = client.post(
                f"{CACHE_URL}/lookup",
                json={
                    "query_type": query_type,
                    "params": payload
                },
                timeout=5.0
            )

            cache_data = cache_response.json()

        # -------------------------
        # CACHE HIT
        # -------------------------

        if cache_data["hit"]:

            latency = time.time() - start

            print(
                f"HIT {query_type} "
                f"latency={latency:.4f}s"
            )

            send_metric(
                "hit",
                latency,
                query_type
            )

            continue

        # -------------------------
        # CACHE MISS
        # -------------------------

        print(f"MISS {query_type}")

        params = payload.copy()

        del params["query_type"]

        with httpx.Client() as client:

            response = client.get(
                f"{RESPONSE_GENERATOR_URL}/{query_type}",
                params=params,
                timeout=10.0
            )

            result = response.json()

        # -------------------------
        # STORE CACHE
        # -------------------------

        with httpx.Client() as client:

            client.post(
                f"{CACHE_URL}/store",
                json={
                    "query_type": query_type,
                    "params": payload,
                    "result": result
                },
                timeout=5.0
            )

        latency = time.time() - start

        print(
            f"STORED {query_type} "
            f"latency={latency:.4f}s"
        )

        send_metric(
            "miss",
            latency,
            query_type
        )

    except Exception as e:

        print(
            f"ERROR processing message: {e}"
        )