import multiprocessing
import multiprocessing.synchronize
from pathlib import Path
import queue
import threading

from fastapi.datastructures import State
from loguru import logger
from serial import Serial

from robo_loader.impl.models import Identifier
from robo_loader.impl.module_loader import ModuleLoader
from robo_loader.impl.module_process import ModuleInfo


class Status(Identifier):
    content: str


Statuses = dict[str, Status]


class ModuleThread(threading.Thread):
    def __init__(
        self,
        module_paths: list[Path],
        serial_in: "queue.Queue[bytes] | None" = None,
        serial_out: "queue.Queue[bytes] | None" = None,
        info_queue: "multiprocessing.Queue[tuple[str, ModuleInfo]] | None" = None,
    ):
        super().__init__()
        self.module_paths = module_paths
        self.serial_in = serial_in
        self.serial_out = serial_out
        self.info_queue = info_queue

        self.stop_event = multiprocessing.Event()
        self._values_queue = multiprocessing.Queue()
        self.status_lock = threading.Lock()
        self.statuses: Statuses = {}

    def run(self) -> None:
        logger.info("ModuleThread is running")

        def on_state_change(idf: Identifier, state: str):
            with self.status_lock:
                self.statuses[idf["module_name"]] = Status(**idf, content=state)

        ModuleLoader(
            module_paths=self.module_paths,
            on_state_change=on_state_change,
            cancellation_event=self.stop_event,
            ignore_deaths=True,
            values_queue=self._values_queue,
            serial_in=self.serial_in,
            serial_out=self.serial_out,
            info_queue=self.info_queue,
        ).load()

    def set_values(self, values: dict):
        self._values_queue.put(values)

    def cancel(self):
        self.stop_event.set()
