from contextlib import asynccontextmanager
from multiprocessing import Event, Manager, Process
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from typing import TypedDict
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from serial import Serial
from loader.impl import load
from loader.impl.models import Identifier


class Container(TypedDict):
    author: str
    title: str
    content: str


messages: list[Container] = []
statuses: dict[str, Container] = {}


class TheProcess(Process):
    def __init__(self, stop_event: EventType, statuses, messages):
        super().__init__()
        self.stop_event = stop_event
        self.statuses: dict = statuses
        self.messages: list = messages

    def run(self) -> None:
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

        serial = Serial("COM3", baudrate=115200)

        load.load(
            serial=serial,
            on_message=on_message,
            on_state_change=on_state_change,
            cancellation_event=self.stop_event,
            ignore_deaths=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global statuses, messages

    with Manager() as manager:
        statuses = manager.dict()  # type: ignore
        messages = manager.list()  # type: ignore

        stop_event = Event()
        the_process = TheProcess(stop_event, statuses, messages)
        the_process.start()

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


app.mount(
    "/",
    StaticFiles(directory=(Path(__file__).parent / "frontend" / "dist"), html=True),
    name="frontend",
)
