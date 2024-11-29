import multiprocessing
import random
import threading
from unittest import mock

from loguru import logger
from robo_loader.impl.core_impl import CoreImpl
from robo_loader.impl.venv_manager import RequirementsError, VenvManager
from robo_loader.testing.test_model import TestContext, Tests
from multiprocessing import Event

from loguru import logger

from robo_loader.impl import module_loader

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

    def __init__(
        self, cancel_event: threading.Event, value_queue: "multiprocessing.Queue"
    ):
        super().__init__()
        self.cancel_event = cancel_event
        self.value_queue = value_queue

    def run(self):
        import time

        while not self.cancel_event.is_set():
            values = {}
            for label in RandomValueFeederThread.LABELS:
                values[label] = random.randint(0, 500)
            self.value_queue.put(values)
            time.sleep(10)


@tests(
    depends=[
        test_main_py_has_main_fn,
        test_requirements_installable,
    ]
)
def test_load_and_state_change(ctx: TestContext):
    """Modül yüklenebilmeli ve durum belirtmeli."""
    logger.info(f"Loading module {ctx.module_path.name}")
    cancel_event = Event()
    state_changed = False
    timeout_reached = False

    def handle_state_change(*_, **__):
        nonlocal state_changed
        state_changed = True
        cancel_event.set()
        logger.info("State changed")

    def handle_timeout():
        nonlocal timeout_reached
        if cancel_event.is_set():
            return

        logger.error("Module loading timed out after 1 minutes")
        timeout_reached = True
        cancel_event.set()

    timeout_thread = threading.Timer(60, handle_timeout)
    timeout_thread.start()

    try:
        module_loader.load(
            module_paths=[ctx.module_path],
            on_state_change=handle_state_change,
            on_message=lambda _, message: logger.warning(f"MESSAGE: {message}"),
            cancellation_event=cancel_event,
            log_path=ctx.log_file,
        )
        timeout_thread.cancel()

        if state_changed:
            return

        if timeout_reached:
            assert (
                False
            ), "core.set_state() çağrılmadığı için zaman aşımı gerçekleşti (1 dakika)."

        assert (
            False
        ), "Modül durum belirmedi/değiştirmedi. [core.set_state() çağrılmadı]"
    except KeyboardInterrupt:
        cancel_event.set()
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {ctx.module_path.name}"
        )
        assert False, "Modül yüklenirken hata oluştu. (log dosyalarını kontrol edin)"


@tests() # @tests(depends=[test_load_and_state_change])
def test_sound(ctx: TestContext):
    """Modül ses çalmalı."""
    logger.info(f"Loading module {ctx.module_path.name}")
    cancel_event = Event()
    timeout_reached = False

    def handle_timeout():
        nonlocal timeout_reached
        if cancel_event.is_set():
            return

        logger.error("Module loading timed out after 1 minutes")
        timeout_reached = True
        cancel_event.set()

    timeout_thread = threading.Timer(60, handle_timeout)
    timeout_thread.start()

    try:
        patches = module_loader.load(
            module_paths=[ctx.module_path],
            on_message=lambda _, message: logger.warning(f"MESSAGE: {message}"),
            cancellation_event=cancel_event,
            log_path=ctx.log_file,
            patches=[dict(target="robo_loader.impl.core_impl.CoreImpl.play_sound")],
        )
        timeout_thread.cancel()

        if timeout_reached:
            assert (
                False
            ), "core.play_sound() çağrılmadığı için zaman aşımı gerçekleşti (1 dakika)."

        assert (
            play_sound.call_count
        ), "Modül ses çalmadı. [core.play_sound() çağrılmadı]"

        for (sound_path,) in play_sound.call_args_list:
            exc = CoreImpl.validate_sound_path(ctx.module_path, sound_path)
            assert not exc, f"Geçersiz ses dosyası ({sound_path}) çalındı: {exc!r}"

    except KeyboardInterrupt:
        cancel_event.set()
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {ctx.module_path.name}"
        )
        assert False, "Modül yüklenirken hata oluştu. (log dosyalarını kontrol edin)"

tests.tests.reverse()
