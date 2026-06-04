# Tarea 1 - Sistemas Distribuidos

## Descripción

Sistema distribuido de consultas geoespaciales sobre un dataset de Google Open Buildings para la Región Metropolitana de Chile.

El sistema utiliza Redis como caché para reducir la carga de procesamiento y mejorar el rendimiento frente a grandes volúmenes de consultas.

---

## Arquitectura

El sistema está compuesto por los siguientes servicios:

* **Traffic Generator**

  * Genera consultas sintéticas y las publica en Kafka.

* **Kafka Consumer**

  * Consume mensajes desde Kafka.
  * Consulta la caché.
  * Realiza reintentos automáticos ante fallos temporales.
  * Envía mensajes fallidos a una Dead Letter Queue (DLQ) cuando se supera el número máximo de reintentos.

* **Cache Service**

  * Gestiona el acceso a Redis.
  * Determina si una consulta corresponde a un Cache Hit o Cache Miss.
  * Implementa TTL configurable para las entradas almacenadas.

* **Response Generator**

  * Procesa las consultas sobre el dataset en memoria.
  * Simula fallos temporales para evaluar mecanismos de tolerancia a fallos.

* **Metrics Service**

  * Recolecta estadísticas y métricas del sistema.
  * Calcula hit rate, throughput y latencias.

* **Kafka**

  * Sistema de mensajería distribuida utilizado para desacoplar productores y consumidores.

* **Redis**

  * Sistema de caché utilizado para almacenar resultados de consultas frecuentes.

---

## Requisitos Previos

* Docker
* Docker Compose
* WSL (si se utiliza Windows)
* Dataset Google Open Buildings

### Descarga del Dataset

El archivo debe descargarse desde:

https://drive.google.com/file/d/10Rpq2eGxgcJhnOu_QOJcolKt3USaNHMg/view?usp=drive_link

Una vez descargado:

* Renombrar el archivo como:

```text
buildings.csv
```

* Ubicarlo dentro de la carpeta:

```text
data/
```

---

## Estructura del Proyecto

```text
.
│   .gitignore
│   docker-compose.yml
│   README.md
│
├───cache_service
│       dockerfile
│       main.py
│       requirements.txt
│
├───data
│       buildings.csv
│
├───Kafka_Consumer
│       dockerfile
│       main.py
│       requirements.txt
│
├───metrics_service
│       dockerfile
│       main.py
│       requirements.txt
│
├───response_generator
│       dockerfile
│       main.py
│       requirements.txt
│
└───traffic_generator
        dockerfile
        main.py
        requirements.txt
```

---

## Levantar el Sistema

Desde la carpeta raíz ejecutar:

```bash
docker compose up --build
```

---

## Verificar Estado de los Servicios

```bash
docker compose ps
```

---

## Importante

En algunas ejecuciones, los servicios **Kafka Consumer** y **Traffic Generator** pueden iniciarse antes de que Kafka o los demás servicios estén completamente disponibles.

Cuando esto ocurre, dichos contenedores pueden finalizar automáticamente.

Si sucede, simplemente reiniciarlos con:

```bash
docker compose restart kafka_consumer
docker compose restart traffic_generator
```

Luego verificar nuevamente:

```bash
docker compose ps
```

---

## Consultar Métricas

Para visualizar las métricas recolectadas por el sistema:

### Linux / WSL

```bash
curl http://localhost:8002/stats
```

### PowerShell

```powershell
(Invoke-WebRequest -UseBasicParsing http://localhost:8002/stats).Content
```

Ejemplo de salida:

```json
{
  "hit_rate": 0.89,
  "throughput_rps": 7.7,
  "latency_p50": 0.005,
  "latency_p95": 0.27,
  "eviction_rate_per_min": 0.0,
  "cache_efficiency": -0.04
}
```

---

## Funcionalidades Implementadas

### Caché

* Redis como sistema de caché.
* TTL configurable.
* Política de reemplazo LRU.
* Cache Hits y Cache Misses.

### Tolerancia a Fallos

* Simulación de fallos temporales.
* Reintentos automáticos.
* Recovery automático.
* Dead Letter Queue (DLQ).

### Procesamiento Distribuido

* Kafka como sistema de mensajería.
* Consumidores agrupados mediante Consumer Groups.
* Posibilidad de escalamiento horizontal agregando múltiples consumidores.

### Observabilidad

* Throughput.
* Hit Rate.
* Latencia P50.
* Latencia P95.
* Métricas de caché.

---

## Ejemplos de Consultas

Las consultas son generadas automáticamente por el Traffic Generator.

Los tipos de consultas disponibles son:

```text
Q1
Q2
Q3
Q4
Q5
```

Las zonas disponibles son:

```text
Z1
Z2
Z3
Z4
Z5
```

Ejemplos:

```text
q1(zone_id=Z1)
q2(zone_id=Z2)
q3(zone_id=Z3)
q4(zone_a=Z1, zone_b=Z4)
q5(zone_id=Z5)
```

---

## Notas

* El sistema fue diseñado para ejecutar experimentos de rendimiento utilizando Redis y Kafka.
* El Traffic Generator utiliza una distribución Zipf para generar patrones de acceso realistas.
* El sistema soporta reintentos automáticos y recuperación ante fallos temporales del servicio de procesamiento.
* Se pueden agregar más consumidores Kafka para realizar pruebas de escalamiento horizontal.
