import asyncio
import atexit
import enum
import importlib.util
import os
import sys
from multiprocessing import Manager, Process
from multiprocessing.synchronize import Event
from queue import Empty
from pathlib import Path
from time import sleep
from typing import Callable, NamedTuple

from loguru import logger

import loader.dummy_core as dummy_core
from loader.core_impl import CoreImpl
from loader.models import Identifier
from loader.venv_manager import VenvManager

modules_path = Path(__file__).parent.parent / "modules"


class _ModuleProcess(Process):
    module_path: Path
    core_args: dict

    def __init__(self, module_path: Path, core_args: dict):
        super().__init__()
        self.daemon = True
        self.module_path = module_path
        self.core_args = core_args

    @property
    def name(self) -> str:
        return self.module_path.name

    def run(self):
        _run_module(self.module_path, self.core_args)


class _ActionType(enum.Enum):
    CANCEL = 0
    DIED = 1
    COMMAND = 2


def get_module_paths() -> list[Path]:
    return [d for d in modules_path.iterdir() if d.is_dir()]


def load(
    module_paths: list[Path] | None = None,
    on_state_change: Callable[[Identifier, str], None] | None = None,
    on_message: Callable[[Identifier, str], None] | None = None,
    cancellation_event: Event | None = None,
):
    is_cancelled = (
        lambda: cancellation_event is not None and cancellation_event.is_set()
    )

    if module_paths is None:
        module_paths = get_module_paths()

    processes: list[Process] = []
    with Manager() as manager:
        values = manager.dict()
        values.update({"Sıcaklık": 40})

        command_queue = manager.Queue()
        args = dict(values_shm=values, command_queue=command_queue)

        for module_dir in module_paths:
            VenvManager(module_dir.name).ensure_requirements(
                module_dir / "requirements.txt"
            )

        for module_dir in module_paths:
            process = _ModuleProcess(module_dir, args)
            processes.append(process)
            process.start()

        values.update({"Nem": 40})

        def select_action():
            while True:
                if is_cancelled():
                    return (_ActionType.CANCEL, None)

                died_processes = [p for p in processes if not p.is_alive()]
                if len(died_processes) > 0:
                    return (_ActionType.DIED, died_processes)

                try:
                    command = command_queue.get_nowait()
                    return (_ActionType.COMMAND, command)
                except Empty:
                    pass

                sleep(0.01)

        while True:
            action = select_action()
            match action[0]:
                case _ActionType.CANCEL:
                    logger.info("Cancelling the loader.")
                    break
                case _ActionType.DIED:
                    module_names = [p.name for p in action[1]]
                    raise Exception(f"{module_names} modules has died.")
                case _ActionType.COMMAND:
                    command = action[1]

            author = command["author"]
            title = command["title"]
            verb = command["verb"]
            value = command["value"]

            identifier = Identifier(
                title=title,
                author=author,
            )

            logger.info(f"Command: {command}")

            match verb:
                case "Durum":
                    if on_state_change is not None:
                        on_state_change(identifier, value)
                case "Mesaj":
                    if on_message is not None:
                        on_message(identifier, value)
                case _:
                    logger.warning(f"Unknown command verb: {verb}")

        for p in processes:
            p.terminate()


def _run_module(module_dir: Path, args: dict):
    title_file = module_dir / "TITLE.txt"
    author_file = module_dir / "AUTHOR.txt"

    module_name = module_dir.name
    title = title_file.read_text() if title_file.exists() else "Bilinmiyor"
    author = author_file.read_text() if author_file.exists() else "Bilinmiyor"

    core_impl = CoreImpl(author=author, title=title, **args)

    requirements_file = module_dir / "requirements.txt"
    venv_manager = VenvManager(module_name)
    venv_manager.ensure_requirements(requirements_file)
    venv_manager.activate()

    sys.path.append(str(module_dir.absolute()))
    sys.modules["core"] = dummy_core
    os.chdir(module_dir)

    spec = importlib.util.spec_from_file_location(
        module_dir.name, module_dir / "main.py"
    )
    if spec is None:
        logger.warning(f"Module '{module_dir.name}' could not be imported. (No spec)")
        return

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        logger.warning(
            f"Module '{module_dir.name}' could not be imported. (No spec loader)"
        )
        return

    try:
        spec.loader.exec_module(module)
    except:
        logger.exception(f"Module '{module_dir.name}' could not be imported.")
        return

    if (not hasattr(module, "main")) or (not callable(module.main)):
        logger.warning(f"Module '{module_dir.name}' has no 'main' function.")
        return

    try:
        asyncio.run(module.main(core_impl))  # type: ignore
    except:
        logger.exception(f"Module '{module_dir.name}' has thrown an exception.")
        raise


if __name__ == "__main__":
    load()
