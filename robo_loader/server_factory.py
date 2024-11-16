from pathlib import Path
import typing
import uvicorn

from robo_loader.server.app import app


def start_server(*, use_serial: bool = False, **loader_args):
    app.state.loader_args = loader_args
    app.state.use_serial = use_serial
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    start_server()
