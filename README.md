# tarea1-sistemas-distribuidos

##Descripción

Sistema distribuído de consultas geoespaciales sobre un dataset de Google Open Buildings en la región Metropolitana.
El sistema de caché está basado en Redis y permite reducir la carga y aumentar el rendimiento frente a una carga de peticiones.


#Arquitectura
El sistema está conformado por 4 servicios independientes:
  -Traffic Generator : Encargado de generar consultas sintéticas.
  -Cache service : Se conecta y consulta a Redis para determinar si es un cache miss o cache hit.
  -Response Generator : Calcula en memoria
  -Metrics service : Encargado de las estadísticas y las métricas de las peticiones totales.

#Requisitos previos
  -Docker 
  -WSL si se está en Windows
  -Dataset de Open Google Buildings (Sólo toma en cuenta datos de la región metropolitana)

#Instrucciones de uso 
La estructura del proyecto debe tener esta forma: 

TAREA1
  docker-compose.yml
  cache_service
      -dockerfile
      -main.py
      -requirements.txt
  data
      -buildings.csv

  metrics_service
      -dockerfile
      -main.py
      -requirements.txt

  response_generator
      -dockerfile
      -main.py
      -requirements.txt

  traffic_generator
      -dockerfile
      -main.py
      -requirements.txt

  El archivo descargado de Google Open Buildings debe llamarse "buildings.csv" y debe estar dentro de la carpeta data/

  #Para levantar todos los servicios se utiliza el siguiente comando dentro de la carpeta de TAREA1
      docker compose up --build

  #Para verificar que los sistemas estén funcionando correctamente se utiliza el comando
      docker compose ps

  #Para ver las métricas de las peticiones generadas (Curl en el puerto asignado para metric_service)
    curl http://localhost:8002/stats

  #Ejemplos de queries (Parametrizable con el tipo de query (Q1 - Q5) y las zonas geograficas (Z1 - Z5)
    curl http://localhost:8000/query?query_type=q1&zone_id=Z1
    curl http://localhost:8000/query?query_type=q2&zone_id=Z2
  
  
