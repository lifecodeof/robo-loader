import asyncio
import enum
import importlib.util
import os
import sys
from multiprocessing import Manager, Process
from multiprocessing.synchronize import Event
from pathlib import Path
from queue import Empty
from time import sleep
from typing import Callable, TextIO
from serial import Serial

from loguru import logger

from loader import transport
import loader.dummy_core as dummy_core
from loader.core_impl import CoreImpl
from loader.models import Command, Identifier
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
    INCOMING_VALUES = 3


def get_module_paths() -> list[Path]:
    return [d for d in modules_path.iterdir() if d.is_dir()]


def load(
    module_paths: list[Path] | None = None,
    on_state_change: Callable[[Identifier, str], None] | None = None,
    on_message: Callable[[Identifier, str], None] | None = None,
    cancellation_event: Event | None = None,
    serial: Serial | None = None,
    ignore_deaths: bool = False,
):
    is_cancelled = (
        lambda: cancellation_event is not None and cancellation_event.is_set()
    )

    if module_paths is None:
        module_paths = get_module_paths()

    processes: list[Process] = []
    with Manager() as manager:
        values = manager.dict()

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

        serial_buffer = b""

        def select_action():
            nonlocal serial_buffer

            while True:
                if is_cancelled():
                    return (_ActionType.CANCEL, None)

                try:
                    command = command_queue.get_nowait()
                    return (_ActionType.COMMAND, command)
                except Empty:
                    pass

                if serial is not None and serial.in_waiting > 0:
                    buf = serial.read_all()
                    if buf:
                        serial_buffer += buf

                    if b"\n" in serial_buffer:
                        line, serial_buffer = serial_buffer.split(b"\n", 1)
                        return (_ActionType.INCOMING_VALUES, line.decode("utf-8"))

                if not ignore_deaths:
                    died_processes = [p for p in processes if not p.is_alive()]
                    if len(died_processes) > 0:
                        return (_ActionType.DIED, died_processes)

                sleep(0.01)

        def handle_command(command: Command):
            author = command["author"]
            title = command["title"]
            verb = command["verb"]
            value = command["value"]

            identifier = Identifier(
                title=title,
                author=author,
            )

            # logger.info(f"Command: {command}")

            match verb:
                case "Durum":
                    if on_state_change is not None:
                        on_state_change(identifier, value)
                case "Mesaj":
                    if on_message is not None:
                        on_message(identifier, value)
                case "Motor açısı":
                    if serial is not None:
                        payload = transport.stringify_command(
                            {"Motor açısı": int(value)}
                        )
                        serial.write(payload.encode("utf-8"))
                case _:
                    raise Exception(f"Unknown command verb: {verb}")

        reported_deaths = set()
        while True:
            action = select_action()
            match action[0]:
                case _ActionType.CANCEL:
                    logger.info("Cancelling the loader.")
                    break
                case _ActionType.DIED:
                    module_names = [p.name for p in action[1]]
                    if ignore_deaths:
                        for name in module_names:
                            if name not in reported_deaths:
                                logger.warning(f"{name} module has died.")
                                reported_deaths.add(name)
                    else:
                        raise Exception(f"{module_names} modules has died.")
                case _ActionType.COMMAND:
                    handle_command(action[1])
                case _ActionType.INCOMING_VALUES:
                    str_values = action[1]
                    logger.info(f"Values: {str_values}")
                    parsed_values = transport.parse_serial_line(str_values)
                    values.update(parsed_values)

        for p in processes:
            p.terminate()


def _run_module(module_dir: Path, args: dict):
    title_file = module_dir / "TITLE.txt"
    author_file = module_dir / "AUTHOR.txt"

    module_name = module_dir.name
    title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else "Bilinmiyor"
    author = author_file.read_text(encoding="utf-8").strip() if author_file.exists() else "Bilinmiyor"

    core_impl = CoreImpl(author=author, title=title, **args)

    requirements_file = module_dir / "requirements.txt"
    venv_manager = VenvManager(module_name)
    venv_manager.ensure_requirements(requirements_file)
    venv_manager.activate()

    sys.path.append(str(module_dir.absolute()))
    dummy_core.actual_impl = core_impl
    sys.modules["core"] = dummy_core
    os.chdir(module_dir)

    class FakeStdout(TextIO):
        def write(self, s: str):
            core_impl.sync_send_message(s)

        def flush(self) -> None: ...

        def isatty(self) -> bool:
            return False

    sys.stdout = FakeStdout()

    spec = importlib.util.spec_from_file_location(
        module_dir.name, module_dir / "main.py"
    )
    if spec is None:
        logger.warning(f"Module '{module_dir.name}' could not be imported. (No spec)")
        return

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise Exception(
            f"Module '{module_dir.name}' could not be imported. (No spec loader)"
        )

    try:
        spec.loader.exec_module(module)
    except:
        logger.exception(f"Module '{module_dir.name}' could not be imported.")
        raise

    if (not hasattr(module, "main")) or (not callable(module.main)):
        raise Exception(f"Module '{module_dir.name}' has no 'main' function.")

    try:
        asyncio.run(module.main(core_impl))  # type: ignore
    except:
        logger.exception(f"Module '{module_dir.name}' has thrown an exception.")
        raise


if __name__ == "__main__":
    load()
