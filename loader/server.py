import uvicorn

from loader.server.app import app


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    start_server()
