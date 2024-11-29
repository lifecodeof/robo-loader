import asyncio
import enum
import importlib.util
from multiprocessing.managers import ListProxy
import os
import sys
from multiprocessing import Manager, Process, Queue
from multiprocessing.synchronize import Event
from pathlib import Path
from queue import Empty
from time import sleep
from typing import Any, Callable, TextIO
import unittest
import unittest.mock
import warnings
from serial import Serial

from loguru import logger

from robo_loader.impl import transport
import robo_loader.impl.dummy_core as dummy_core
from robo_loader.impl.core_impl import CoreImpl
from robo_loader.impl.models import Command, Identifier
from robo_loader.impl.venv_manager import VenvManager
from robo_loader import ROOT_PATH


class _ModuleProcess(Process):
    def __init__(
        self,
        module_path: Path,
        core_args: dict,
        venvs_path: Path,
        log_path: Path | None,
        pathches: list[dict] | None = None,
        applied_patches: "ListProxy[unittest.mock._patch] | None" = None,
    ):
        super().__init__(daemon=True, name=f"ModuleProcess-{module_path.name}")
        self.module_path = module_path
        self.core_args = core_args
        self.venvs_path = venvs_path
        self.log_path = log_path
        self.pathches = pathches
        self.applied_patches = applied_patches

    @property
    def name(self) -> str:
        return self.module_path.name

    def run(self):
        try:
            import cv2  # type: ignore

            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
        except ImportError:
            pass

        if self.log_path is not None:

            def _redirect_stream(stream_name, target_file: Path):
                """Redirect a C-level stream like stdout or stderr."""

                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.touch()

                file = open(target_file, "w", buffering=1, encoding="utf-8")
                setattr(sys, stream_name, file)

            warnings.filterwarnings("ignore")
            logger.remove(0)
            logger.add(self.log_path)

            _redirect_stream(
                "stdout", self.log_path.with_stem(self.log_path.stem + ".stdout")
            )

            _redirect_stream(
                "stderr", self.log_path.with_stem(self.log_path.stem + ".stderr")
            )

        applied_patches: list[unittest.mock._patch] = []
        if self.pathches:
            for patch in self.pathches:
                applied_patches.append(unittest.mock.patch(**patch))

        try:
            for patch in applied_patches:
                patch.start()
            _run_module(
                self.module_path,
                self.core_args,
                self.venvs_path,
            )
        finally:
            if applied_patches:
                for patch in applied_patches:
                    patch.stop()

            if self.applied_patches is not None:
                self.applied_patches.extend(applied_patches)

            if self.log_path is not None:
                sys.stdout.flush()
                sys.stderr.flush()


class _ActionType(enum.Enum):
    CANCEL = 0
    DIED = 1
    COMMAND = 2
    INCOMING_VALUES = 3
    INCOMING_PARSED_VALUES = 4


_Action = tuple[_ActionType, Any]


def get_module_paths() -> list[Path]:
    modules_path = ROOT_PATH / "modules"
    if not modules_path.exists():
        return []

    return [d for d in modules_path.iterdir() if d.is_dir()]


def get_module_path(module_name: str) -> Path:
    path = ROOT_PATH / "modules" / module_name
    if not path.exists():
        raise FileNotFoundError(f"Module '{module_name}' does not exist.")
    return path


def load(
    module_paths: list[Path] | None = None,
    on_state_change: Callable[[Identifier, str], None] | None = None,
    on_message: Callable[[Identifier, str], None] | None = None,
    cancellation_event: Event | None = None,
    serial: Serial | None = None,
    ignore_deaths: bool = False,
    venvs_path: Path | None = None,
    value_queue: "Queue | None" = None,
    log_path: Path | None = None,
    patches: list[dict] | None = None,
):
    venvs_path = venvs_path or ROOT_PATH / "venvs"
    is_cancelled = (
        lambda: cancellation_event is not None and cancellation_event.is_set()
    )

    if module_paths is None:
        module_paths = get_module_paths()

    processes: list[_ModuleProcess] = []
    with Manager() as manager:
        try:
            applied_patches = manager.list()
            values = manager.dict()

            command_queue = manager.Queue()
            args = dict(values_shm=values, command_queue=command_queue)

            for module_dir in module_paths:
                process = _ModuleProcess(
                    module_dir, args, venvs_path, log_path, patches, applied_patches
                )
                processes.append(process)
                process.start()

            serial_buffer = b""

            def select_actions() -> list[_Action]:
                nonlocal serial_buffer

                while True:
                    actions = []
                    if is_cancelled():
                        actions.append((_ActionType.CANCEL, None))

                    try:
                        command = command_queue.get_nowait()
                        actions.append((_ActionType.COMMAND, command))
                    except Empty:
                        pass

                    if value_queue:
                        try:
                            values = value_queue.get_nowait()
                            actions.append((_ActionType.INCOMING_PARSED_VALUES, values))
                        except Empty:
                            pass

                    if serial is not None and serial.in_waiting > 0:
                        buf = serial.read_all()
                        if buf:
                            serial_buffer += buf

                        if b"\n" in serial_buffer:
                            line, serial_buffer = serial_buffer.split(b"\n", 1)
                            actions.append(
                                (_ActionType.INCOMING_VALUES, line.decode("utf-8"))
                            )

                    if not ignore_deaths:
                        died_processes = [p for p in processes if not p.is_alive()]
                        if len(died_processes) > 0:
                            actions.append((_ActionType.DIED, died_processes))

                    if len(actions) > 0:
                        return actions

                    sleep(0.01)

            transport_command = transport.TransportCommand(
                {
                    "Motor0 açısı": 0,
                    "Motor1 açısı": 0,
                }
            )

            def handle_command(command: Command):
                author = command["author"]
                title = command["title"]
                verb = command["verb"]
                value = command["value"]

                identifier = Identifier(
                    title=title,
                    author=author,
                )

                match verb:
                    case "Durum":
                        if on_state_change is not None:
                            on_state_change(identifier, value)
                    case "Mesaj":
                        if on_message is not None:
                            on_message(identifier, value)
                    case "Motor0 açısı" | "Motor1 açısı":
                        if serial is not None:
                            transport_command[verb] = int(value)
                            payload = transport.stringify_command(transport_command)
                            if payload:
                                serial.write(payload.encode("utf-8") + b"\n")
                    case _:
                        raise Exception(f"Unknown command verb: {verb}")

            reported_deaths = set()

            def handle_action(action: _Action):
                action_type, payload = action
                match action_type:
                    case _ActionType.CANCEL:
                        logger.info("Cancelling the loader.")
                        return True
                    case _ActionType.DIED:
                        module_names = [p.name for p in payload]
                        if ignore_deaths:
                            for name in module_names:
                                if name not in reported_deaths:
                                    logger.warning(f"{name} module has died.")
                                    reported_deaths.add(name)
                        else:
                            raise Exception(f"{module_names} modules has died.")
                    case _ActionType.COMMAND:
                        handle_command(payload)
                    case _ActionType.INCOMING_VALUES:
                        str_values = payload
                        logger.info(f"Feeding values: {str_values}")
                        parsed_values = transport.parse_serial_line(str_values)
                        if parsed_values:
                            values.update(parsed_values)
                    case _ActionType.INCOMING_PARSED_VALUES:
                        logger.info(f"Feeding values: {payload}")
                        values.update(payload)

            while True:
                actions = select_actions()
                should_break = False
                for action in actions:
                    should_break = should_break or handle_action(action)

                if should_break:
                    break
        finally:
            for p in processes:
                p.terminate()

            for p in processes:
                p.join()

        return list(applied_patches)


def _run_module(
    module_dir: Path,
    args: dict,
    venvs_path: Path,
):
    title_file = module_dir / "TITLE.txt"
    author_file = module_dir / "AUTHOR.txt"

    module_name = module_dir.name
    title = (
        title_file.read_text(encoding="utf-8").strip()
        if title_file.exists()
        else "Bilinmiyor"
    )
    author = (
        author_file.read_text(encoding="utf-8").strip()
        if author_file.exists()
        else "Bilinmiyor"
    )

    core_impl = CoreImpl(author=author, title=title, root_path=module_dir, **args)

    requirements_file = module_dir / "requirements.txt"
    venv_manager = VenvManager(module_name, venvs_path)
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
