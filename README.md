# Laboratorio 8 — Fidelización en restaurantes (CS3081)

Programa de puntos con **microservicios**, **RabbitMQ** (EDA) y arquitectura **hexagonal**.

**Repositorio:** [Anyeli1204/SistemaDeFidelizacion](https://github.com/Anyeli1204/SistemaDeFidelizacion)

## Qué hace

1. El **restaurante** registra un consumo → se publica un evento en RabbitMQ.
2. El **worker de recompensas** suma puntos y guarda la cuenta (SQLite).
3. Opcional: **notificaciones** por correo.
4. El **cliente** consulta su saldo (API aparte).

## Requisitos

- Python 3.11+
- RabbitMQ del curso (ver `.env.example`)
- Copiar `.env.example` → `.env` y poner la contraseña del curso

## Cómo ejecutar

```powershell
pip install -e ".[dev]"
$env:PYTHONPATH="src"
python -m services.restaurant      # :8000
python -m services.rewards         # worker
python -m services.consulta        # :8001
python -m services.notification    # opcional
```

## Probar

- **Postman:** `postman/Laboratorio-8-Fidelizacion.postman_collection.json`
- **Swagger:** http://localhost:8000/docs y http://localhost:8001/docs
- **Tests:** `pytest -m "not integration" -q`
- **SonarQube:** https://sonarqube.ingsoftware.lat/ — proyecto `Anyeli_Tamara_t1`

## Frontend

Carpeta `frontend/`: HTML simple para probar registro y consulta de puntos (complemento a Postman).

```powershell
cd frontend
python -m http.server 5500
```

Abrir http://localhost:5500 (con el backend en marcha).

## Estructura

```
src/          # dominio, aplicación, infraestructura, servicios
tests/
postman/
frontend/     # UI de prueba (opcional)
```
