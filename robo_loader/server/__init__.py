import uvicorn

from robo_loader.server.app import app


def main():
    uvicorn.run(app)
