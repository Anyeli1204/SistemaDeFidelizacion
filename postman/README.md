# Postman — Laboratorio 8

## Importar

1. Abre **Postman**.
2. **Import** → arrastra o selecciona:
   - `Laboratorio-8-Fidelizacion.postman_collection.json`
   - `Laboratorio-8-Local.postman_environment.json` (opcional)
3. En la esquina superior derecha, elige el entorno **Laboratorio 8 — Local**.

## Swagger (alternativa en el navegador)

| Servicio | Swagger UI | OpenAPI JSON |
|----------|------------|--------------|
| Restaurante | http://localhost:8000/docs | http://localhost:8000/openapi.json |
| Consulta | http://localhost:8001/docs | http://localhost:8001/redoc |

## Orden de ejecución

1. Configura `.env` con el RabbitMQ del curso (`RABBITMQ_HOST`, usuario, contraseña).
2. Terminal: `export PYTHONPATH=src` y `python -m services.restaurant` (8000)
3. Terminal: `python -m services.rewards`
4. Terminal: `python -m services.consulta` (8001)
5. En Postman: carpeta **03 — Flujo completo** → **Run collection**
