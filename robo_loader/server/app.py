from contextlib import asynccontextmanager
from multiprocessing import Event, Manager, Process
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from multiprocessing import Queue
from typing import TypedDict
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from loguru import logger
from serial import Serial
from robo_loader.impl import module_loader
from robo_loader.impl.models import Identifier


class Container(TypedDict):
    author: str
    title: str
    content: str


messages: list[Container] = []
statuses: dict[str, Container] = {}


class TheProcess(Process):
    def __init__(self, state: dict, stop_event: EventType | None, statuses, messages):
        super().__init__()
        self.state = state
        self.stop_event = stop_event
        self.statuses: dict = statuses
        self.messages: list = messages
        self.value_queue = Queue()

    def run(self) -> None:
        logger.info("'The Process' is running")

        def on_message(idf: Identifier, message: str):
            self.messages.append(
                Container(author=idf["author"], title=idf["title"], content=message)
            )

            if len(self.messages) > 100:
                self.messages.pop(0)

        def on_state_change(idf: Identifier, state: str):
            self.statuses[idf["author"]] = Container(
                author=idf["author"], title=idf["title"], content=state
            )

        should_use_serial = self.state.get("use_serial", False)
        logger.info(f"Using serial: {should_use_serial}")
        serial = Serial("COM3", baudrate=115200) if should_use_serial else None

        module_loader.load(
            serial=serial,
            on_message=on_message,
            on_state_change=on_state_change,
            cancellation_event=self.stop_event,
            ignore_deaths=True,
            value_queue=self.value_queue,
            **self.state.get("loader_args", {}),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global statuses, messages

    with Manager() as manager:
        statuses = manager.dict()  # type: ignore
        messages = manager.list()  # type: ignore

        stop_event = Event()
        logger.info("Starting 'The Process'")
        the_process = TheProcess(app.state._state, stop_event, statuses, messages)
        the_process.start()

        app.state.values_queue = the_process.value_queue

        try:
            yield
        except KeyboardInterrupt:
            stop_event.set()
            raise

        stop_event.set()
        the_process.join()


app = FastAPI(lifespan=lifespan)


@app.get("/api/statuses")
def get_statuses():
    return dict(statuses)


@app.get("/api/messages")
def get_messages():
    return list(messages)


@app.post("/api/set_data")
async def set_data(request: Request):
    values_queue: Queue | None = getattr(app.state, "values_queue", None)
    if values_queue:
        data = await request.json()
        values_queue.put(data)


app.mount(
    "/",
    StaticFiles(directory=(Path(__file__).parent / "frontend" / "dist"), html=True),
    name="frontend",
)
