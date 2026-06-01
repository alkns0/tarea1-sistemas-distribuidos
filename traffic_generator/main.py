import numpy as np
import time
import os
import random
import uuid
import json

from kafka import KafkaProducer

# Configuración Kafka
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "queries-topic")

# Configuración tráfico
DISTRIBUTION = os.getenv("DISTRIBUTION", "zipf")
NUM_REQUESTS = int(os.getenv("NUM_REQUESTS", 1000))
RATE = float(os.getenv("RATE", 10))

# Zonas y queries
ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERY_TYPES = ["q1", "q2", "q3", "q4", "q5"]
CONFIDENCE_VALUES = [0.0, 0.5, 0.7, 0.9]

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


def zipf_distribution(n, s=1.5):
    weights = np.array([1 / (i ** s) for i in range(1, n + 1)])
    weights /= weights.sum()
    return weights


def generate_request(distribution="zipf"):

    if distribution == "zipf":

        zone_weights = zipf_distribution(len(ZONES))
        zone_id = np.random.choice(ZONES, p=zone_weights)

        query_weights = zipf_distribution(len(QUERY_TYPES))
        query_type = np.random.choice(
            QUERY_TYPES,
            p=query_weights
        )

    else:

        zone_id = random.choice(ZONES)
        query_type = random.choice(QUERY_TYPES)

    confidence_min = random.choice(CONFIDENCE_VALUES)

    params = {
        "query_type": query_type,
        "confidence_min": confidence_min
    }

    if query_type == "q4":

        zone_b = random.choice(
            [z for z in ZONES if z != zone_id]
        )

        params["zone_a"] = zone_id
        params["zone_b"] = zone_b

    elif query_type == "q5":

        params["zone_id"] = zone_id
        params["bins"] = random.choice([5, 10])

        del params["confidence_min"]

    else:

        params["zone_id"] = zone_id

    return params


def publish_request(params):

    message = {
        "request_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "retry_count": 0,
        "payload": params
    }

    producer.send(
        TOPIC,
        message
    )

    producer.flush()

    return message


def run():

    print(
        f"Iniciando generador de tráfico: "
        f"{NUM_REQUESTS} requests, "
        f"distribución={DISTRIBUTION}, "
        f"rate={RATE} req/s"
    )

    interval = 1.0 / RATE

    for i in range(NUM_REQUESTS):

        params = generate_request(DISTRIBUTION)

        try:

            message = publish_request(params)

            print(
                f"[{i+1}/{NUM_REQUESTS}] "
                f"Publicado "
                f"{params['query_type']} "
                f"id={message['request_id']}"
            )

        except Exception as e:

            print(
                f"Error publicando mensaje: {e}"
            )

        time.sleep(interval)


if __name__ == "__main__":

    # Esperar Kafka
    time.sleep(10)

    run()