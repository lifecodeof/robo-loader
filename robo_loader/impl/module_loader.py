import enum
from multiprocessing.managers import DictProxy
from multiprocessing import Manager, Queue
from multiprocessing.synchronize import Event
from pathlib import Path
from queue import Empty
from time import sleep
from typing import Any, Callable, cast
from serial import Serial

from loguru import logger

from robo_loader.impl import transport
from robo_loader.impl.models import Command, Identifier
from robo_loader.impl.module_process import ModuleProcess
from robo_loader import ROOT_PATH


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


class ModuleLoader:
    def __init__(
        self,
        module_paths: list[Path] | None = None,
        on_state_change: Callable[[Identifier, str], None] | None = None,
        on_message: Callable[[Identifier, str], None] | None = None,
        on_event: Callable[[Identifier, str, Any], None] | None = None,
        cancellation_event: Event | None = None,
        serial: Serial | None = None,
        ignore_deaths: bool = False,
        venvs_path: Path | None = None,
        value_queue: "Queue | None" = None,
        log_path: Path | None = None,
    ) -> None:
        self.module_paths = module_paths or get_module_paths()
        self.on_state_change = on_state_change
        self.on_message = on_message
        self.on_event = on_event
        self.cancellation_event = cancellation_event
        self.serial = serial
        self.ignore_deaths = ignore_deaths
        self.venvs_path = venvs_path or ROOT_PATH / "venvs"
        self.value_queue = value_queue
        self.log_path = log_path

        self._last_transport_command = transport.TransportCommand(
            {
                "Motor0 açısı": 0,
                "Motor1 açısı": 0,
            }
        )
        self._reported_deaths = set()
        self._serial_buffer = b""
        self.processes: list[ModuleProcess] = []

    def _is_cancelled(self):
        return self.cancellation_event is not None and self.cancellation_event.is_set()

    def load(self):
        with Manager() as manager:
            try:
                values = cast("DictProxy[str, Any]", manager.dict())
                command_queue = cast("Queue[Command]", manager.Queue())

                args = dict(values_shm=values, command_queue=command_queue)

                for module_dir in self.module_paths:
                    process = ModuleProcess(
                        module_dir, args, self.venvs_path, self.log_path
                    )
                    self.processes.append(process)
                    process.start()

                while True:
                    actions = self._select_actions(command_queue)
                    should_break = False
                    for action in actions:
                        should_break = should_break or self._handle_action(
                            action, values
                        )

                    if should_break:
                        break
            finally:
                for p in self.processes:
                    p.terminate()

                for p in self.processes:
                    p.join()

    def _handle_action(self, action: _Action, values: "DictProxy[str, Any]"):
        action_type, payload = action
        match action_type:
            case _ActionType.CANCEL:
                logger.info("Cancelling the loader.")
                return True
            case _ActionType.DIED:
                module_names = [p.name for p in payload]
                if self.ignore_deaths:
                    for name in module_names:
                        if name not in self._reported_deaths:
                            logger.warning(f"{name} module has died.")
                            self._reported_deaths.add(name)
                else:
                    raise Exception(f"{module_names} modules has died.")
            case _ActionType.COMMAND:
                self._handle_command(payload)
            case _ActionType.INCOMING_VALUES:
                str_values = payload
                logger.info(f"Feeding values: {str_values}")
                parsed_values = transport.parse_serial_line(str_values)
                if parsed_values:
                    values.update(parsed_values)
            case _ActionType.INCOMING_PARSED_VALUES:
                logger.info(f"Feeding values: {payload}")
                values.update(payload)

    def _handle_command(self, command: Command):
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
                if self.on_state_change is not None:
                    self.on_state_change(identifier, value)
            case "Mesaj":
                if self.on_message is not None:
                    self.on_message(identifier, value)
            case "Motor0 açısı" | "Motor1 açısı":
                if self.serial is not None:
                    self._last_transport_command[verb] = int(value)
                    payload = transport.stringify_command(self._last_transport_command)
                    if payload:
                        self.serial.write(payload.encode("utf-8") + b"\n")
            case "event":
                if self.on_event is not None:
                    event_name, event_value = value
                    self.on_event(identifier, event_name, event_value)
            case _:
                raise Exception(f"Unknown command verb: {verb}")

    def _select_actions(self, command_queue: "Queue[Command]") -> list[_Action]:
        while True:
            actions = []
            if self._is_cancelled():
                actions.append((_ActionType.CANCEL, None))

            try:
                command = command_queue.get_nowait()
                actions.append((_ActionType.COMMAND, command))
            except Empty:
                pass

            if self.value_queue:
                try:
                    values = self.value_queue.get_nowait()
                    actions.append((_ActionType.INCOMING_PARSED_VALUES, values))
                except Empty:
                    pass

            if self.serial is not None and self.serial.in_waiting > 0:
                buf = self.serial.read_all()
                if buf:
                    self._serial_buffer += buf

                if b"\n" in self._serial_buffer:
                    line, self._serial_buffer = self._serial_buffer.split(b"\n", 1)
                    actions.append((_ActionType.INCOMING_VALUES, line.decode("utf-8")))

            if not self.ignore_deaths:
                died_processes = [p for p in self.processes if not p.is_alive()]
                if len(died_processes) > 0:
                    actions.append((_ActionType.DIED, died_processes))

            if len(actions) > 0:
                return actions

            sleep(0.01)


if __name__ == "__main__":
    ModuleLoader().load()
