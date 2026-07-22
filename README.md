# Backend Dockerizado - FOG

Este directorio contiene la parte de servidor lista para desplegar en la nube usando Docker, sin depender de `.venv`.

## Estructura

- `server.py`: API HTTP para recibir datos IMU y exponer estado.
- `inference.py`: punto de entrada para predicción.
- `preprocessing.py`: preprocesamiento de señales.
- `custom_layers.py`: capas personalizadas de TensorFlow.
- `model/`: modelo exportado.

## Ejecutar con Docker

```bash
docker build -t fog-backend .
docker run -p 5050:5050 --env PORT=5050 --env HOST=0.0.0.0 fog-backend
```

## Ejecutar con Docker Compose

```bash
docker compose up --build
```

## Endpoints

- `GET /api/health`
- `GET /api/status`
- `POST /api/data`
- `POST /api/predict`

## Despliegue en Render

1. Crea un repositorio GitHub con el contenido de esta carpeta.
2. En Render, crea un nuevo servicio `Web Service`.
3. Conecta el repo y selecciona `Docker`.
4. Usa la ruta del Dockerfile: `./Dockerfile`.
5. El servicio expondrá la API en una URL pública.
6. Copia esa URL y úsala en el frontend como `backendUrl`.

## GitHub

Crea un repositorio nuevo y sube esta carpeta como proyecto backend.
