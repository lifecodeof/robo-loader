from contextlib import suppress
import multiprocessing
from pathlib import Path
from queue import Empty, Queue
import threading

from loguru import logger
from robo_loader.server.module_thread import ModuleThread, Statuses
from robo_loader.impl.module_process import InfoQueue
from serial import Serial


class SerialReaderThread(threading.Thread):
    def __init__(self, serial: Serial, cancel_event: threading.Event) -> None:
        super().__init__()
        self.serial = serial
        self.serial_in = Queue()
        self.serial_out = Queue()
        self.cancel_event = cancel_event

    def run(self) -> None:
        while not self.cancel_event.is_set():
            if self.serial.in_waiting > 0:
                buf = self.serial.read_all()
                if buf:
                    self.serial_out.put(buf)

            try:
                data = self.serial_in.get_nowait()
                self.serial.write(data)
            except Empty:
                pass


class InfoReaderThread(threading.Thread):
    def __init__(self, info_queue: "InfoQueue", cancel_event: threading.Event) -> None:
        super().__init__()
        self.info_queue = info_queue
        self.cancel_event = cancel_event
        self.info = {}

    def reset(self) -> None:
        self.info.clear()

    def run(self) -> None:
        while not self.cancel_event.is_set():
            with suppress(Empty):
                module_name, module_info = self.info_queue.get(timeout=1)
                self.info[module_name] = module_info


class ModuleThreadManager:
    def __init__(self, serial: Serial | None) -> None:
        self.cancel_event = threading.Event()
        self.serial_reader_thread = serial and SerialReaderThread(
            serial, self.cancel_event
        )

        self.info_queue = multiprocessing.Queue()
        self.info_reader_thread = InfoReaderThread(self.info_queue, self.cancel_event)

        self.threads: list[ModuleThread] = []

    def set_values(self, values: dict) -> None:
        for thread in self.threads:
            thread.set_values(values)

    def get_statuses(self) -> Statuses:
        return {k: v for thread in self.threads for k, v in thread.statuses.items()}

    def start(self) -> None:
        self.info_reader_thread.start()
        if self.serial_reader_thread:
            self.serial_reader_thread.start()

    def replace_thread(self, module_paths: list[Path]):
        self.cancel_threads()
        self.add_thread(module_paths)

    def add_thread(self, module_paths: list[Path]):
        serial_in = self.serial_reader_thread and self.serial_reader_thread.serial_in
        serial_out = self.serial_reader_thread and self.serial_reader_thread.serial_out

        thread = ModuleThread(
            module_paths=module_paths,
            serial_in=serial_in,
            serial_out=serial_out,
            info_queue=self.info_queue,
        )

        self.threads.append(thread)
        thread.start()
        logger.info(f"Started thread for {module_paths}")

    def cancel_threads(self) -> None:
        while self.threads:
            thread = self.threads.pop()
            thread.cancel()

        self.info_reader_thread.reset()

    def get_running_module_names(self) -> list[str]:
        return [
            module_path.name
            for thread in self.threads
            if thread.is_alive()
            for module_path in thread.module_paths
        ]

    def cancel(self):
        self.cancel_threads()
        self.cancel_event.set()

    def get_info(self):
        return self.info_reader_thread.info
