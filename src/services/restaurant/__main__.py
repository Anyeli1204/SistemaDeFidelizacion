import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("services.restaurant.app:app", host=host, port=8000, reload=False)