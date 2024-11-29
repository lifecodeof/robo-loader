import multiprocessing
import random
import threading
from multiprocessing import Event, Queue
from multiprocessing.synchronize import Event as EventType

from loguru import logger

from robo_loader.impl.module_loader import ModuleLoader
from robo_loader.impl.venv_manager import RequirementsError, VenvManager
from robo_loader.testing.test_model import TestContext, Tests

tests = Tests()


@tests()
def test_has_photo(ctx: TestContext):
    """Fotoğraf dosyası olmalı"""
    photo_path = ctx.module_path / "PHOTO.png"
    assert photo_path.exists(), "PHOTO.png fotoğrafı bulunamadı."


@tests()
def test_has_author(ctx: TestContext):
    """AUTHOR.txt dosyası olmalı"""
    author_path = ctx.module_path / "AUTHOR.txt"
    assert author_path.exists(), "AUTHOR.txt dosyası bulunamadı."
    if author_path.read_text().strip() == "":
        assert False, "AUTHOR.txt dosyası boş."


@tests()
def test_has_title(ctx: TestContext):
    """TITLE.txt dosyası olmalı"""
    title_path = ctx.module_path / "TITLE.txt"
    assert title_path.exists(), "TITLE.txt dosyası bulunamadı."
    if title_path.read_text().strip() == "":
        assert False, "TITLE.txt dosyası boş."


@tests()
def test_has_main_py(ctx: TestContext):
    """main.py dosyası olmalı"""
    main_py_path = ctx.module_path / "main.py"
    assert main_py_path.exists(), "main.py dosyası bulunamadı."


@tests(depends=[test_has_main_py])
def test_main_py_has_main_fn(ctx: TestContext):
    """main.py dosyasında main fonksiyonu olmalı"""
    import ast

    main_py_path = ctx.module_path / "main.py"
    main_py_contents = main_py_path.read_text(encoding="utf-8")
    main_py_tree = ast.parse(main_py_contents)
    for node in ast.walk(main_py_tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "main"
        ):
            assert isinstance(
                node, ast.AsyncFunctionDef
            ), "main fonksiyonu async olmalı."

            args_len = len(node.args.args)
            assert args_len == 1, "main fonksiyonunun sadece 1 parametresi olmalı"

            arg = node.args.args[0]
            assert arg.arg == "core", "main fonksiyonunun parametresi 'core' olmalı"

            break
    else:
        assert False, "main.py dosyasında main fonksiyonu bulunamadı."


@tests()
def test_requirements_installable(ctx: TestContext):
    """requirements.txt dosyasındaki paketler yüklenebilmeli"""
    venv_manager = VenvManager(ctx.module_path.name)
    try:
        venv_manager.ensure_requirements(ctx.module_path / "requirements.txt")
    except RequirementsError:
        assert False, "requirements.txt hatalı."


@tests(
    depends=[
        test_main_py_has_main_fn,
        test_requirements_installable,
    ]
)
def test_load_and_state_change(ctx: TestContext):
    """Modül yüklenebilmeli ve durum belirtmeli"""
    cancel_event = Event()
    state_changed = False

    def handle_state_change(*_, **__):
        nonlocal state_changed
        state_changed = True
        cancel_event.set()

    load_module(ctx, cancel_event, dict(on_state_change=handle_state_change))
    assert (
        state_changed
    ), "Modül durum belirmedi/değiştirmedi. [core.set_state() çağrılmadı]"


@tests(
    depends=[
        test_main_py_has_main_fn,
        test_requirements_installable,
    ]
)
def test_send_message_not_called(ctx: TestContext):
    """Mesajlar artık görünmeyecek"""
    cancel_event = Event()
    message_sent = False

    def handle_message(*_, **__):
        nonlocal message_sent
        message_sent = True
        cancel_event.set()

    load_module(ctx, cancel_event, dict(on_message=handle_message), 30)
    assert (
        not message_sent
    ), "Mesajlar artık görünmeyecek bunun yerine core.set_state() kullanın."


@tests(depends=[test_load_and_state_change])
def test_play_sound_called(ctx: TestContext):
    """Modül ses çalmalı"""
    logger.info("Testing if the module plays a sound")
    cancel_event = Event()
    sound_played = False

    def handle_event(_, event_name, _v):
        nonlocal sound_played
        if event_name == "play_sound":
            logger.info("Sound played")
            sound_played = True
            cancel_event.set()

    load_module(ctx, cancel_event, dict(on_event=handle_event))
    assert sound_played, "Modül ses çalmadı. [core.play_sound() çağrılmadı]"


class RandomValueFeederThread(threading.Thread):
    LABELS = [
        "Sıcaklık",
        "Nem",
        "Işık",
        "Mesafe",
        "Nabız",
        "Hava Kalitesi",
        "Gaz",
        "Titreşim",
        "Yağmur",
        "Yakınlık",
    ]

    def __init__(self, cancel_event: EventType, values_queue: Queue):
        super().__init__()
        self.cancel_event = cancel_event
        self.values_queue = values_queue

    def run(self):
        import time

        while not self.cancel_event.is_set():
            values = {}
            for label in RandomValueFeederThread.LABELS:
                values[label] = random.randint(0, 500)
            self.values_queue.put(values)
            time.sleep(10)


def load_module(
    ctx: TestContext,
    cancel_event: EventType,
    loader_kwargs: dict,
    timeout_seconds: int = 120,
):
    try:

        def handle_timeout():
            if cancel_event.is_set():
                return

            logger.error("Module loaded but expectation timed out after 2 minutes")
            cancel_event.set()

        timeout_thread = threading.Timer(timeout_seconds, handle_timeout)
        timeout_thread.start()

        values_queue = Queue()
        feeder_thread = RandomValueFeederThread(cancel_event, values_queue)
        feeder_thread.start()

        ModuleLoader(
            module_paths=[ctx.module_path],
            cancellation_event=cancel_event,
            log_path=ctx.log_file,
            values_queue=values_queue,
            **loader_kwargs,
        ).load()
        timeout_thread.cancel()
    except (KeyboardInterrupt, AssertionError):
        cancel_event.set()
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {ctx.module_path.name}"
        )
        assert False, "Modül yüklenirken hata oluştu. (log dosyalarını kontrol edin)"
