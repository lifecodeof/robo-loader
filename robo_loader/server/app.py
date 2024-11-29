import multiprocessing
import multiprocessing.synchronize
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, cast

from fastapi import Body, Depends, FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from serial import Serial, SerialException

from robo_loader import ROOT_PATH
from robo_loader.impl import module_loader
from robo_loader.impl.module_process import ModuleInfo
from robo_loader.server.module_thread import (
    ModuleThread,
    Status,
    Statuses as StatusesType,
)
from robo_loader.server.module_thread_manager import ModuleThreadManager


class StateDep:
    def __init__(self, state_name: str):
        self.state_name = state_name

    def __call__(self, request: Request):
        return request.app.state._state[self.state_name]


# Dependencies
Mtm = Annotated[ModuleThreadManager, Depends(StateDep("module_thread_manager"))]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        serial = Serial("COM3", baudrate=115200)
    except SerialException:
        serial = None

    logger.info(f"Using serial: {serial}")

    logger.info("Starting ModuleThreadManager")
    module_thread_manager = ModuleThreadManager(serial)
    module_thread_manager.start()
    app.state.module_thread_manager = module_thread_manager

    try:
        yield
    finally:
        module_thread_manager.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/api/statuses")
def get_statuses(mtm: Mtm):
    return mtm.get_statuses()


@app.post("/api/set_data")
async def set_data(request: Request, mtm: Mtm):
    data = await request.json()
    mtm.set_values(data)


@app.get("/api/photo.png")
def get_photo(module_name: str):
    photo_path = ROOT_PATH / "modules" / module_name / "PHOTO.png"
    if not photo_path.exists():
        return Response(status_code=400, content=f"{photo_path} does not exist")
    return FileResponse(photo_path, media_type="image/png")


@app.get("/api/running_modules")
def get_running_modules(mtm: Mtm) -> list[str]:
    return mtm.get_running_module_names()


@app.get("/api/all_modules")
def get_all_modules():
    return [path.name for path in module_loader.get_module_paths()]


@app.get("/api/info")
def info(mtm: Mtm):
    return {module: ModuleInfo.to_str(info) for module, info in mtm.get_info().items()}


@app.get("/api/module_author_mapping")
def module_author_mapping():
    def get_author(path: Path):
        at = path / "AUTHOR.txt"
        return at.read_text(encoding="utf-8") if at.exists() else path.name

    return {path.name: get_author(path) for path in module_loader.get_module_paths()}


@app.post("/api/change_module")
def change_module(module_name: Annotated[str, Body(embed=True)], mtm: Mtm):
    if module_name == "Herkes":
        module_paths = module_loader.get_module_paths()
    else:
        path = Path(ROOT_PATH) / "modules" / module_name
        if not path.exists():
            return Response(status_code=400, content=f"{path} does not exist")
        module_paths = [path]

    mtm.replace_thread(module_paths)


app.mount(
    "/",
    StaticFiles(directory=(Path(__file__).parent / "frontend" / "dist"), html=True),
    name="frontend",
)
