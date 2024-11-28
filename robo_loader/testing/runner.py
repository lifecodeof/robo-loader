from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, cast

from loguru import logger
from robo_loader.testing.unit_tests import tests

if TYPE_CHECKING:
    from loguru import Message


@dataclass(frozen=True)
class TestMeta:
    name: str
    description: str
    is_required: bool
    requires_required: bool


TestResults = dict[
    TestMeta, str | bool
]  # True: passed | False: not runned | str: error message

logger_setup_lock = Lock()


class TestRunner:
    results: TestResults | None = None
    logs_path: Path

    def __init__(self, logs_path: Path) -> None:
        self.logs_path = logs_path
        if not self.logs_path.exists():
            self.logs_path.mkdir()

    def run(self, module_path: Path):
        is_logger_setup = getattr(logger, "_test_runner_is_setup", False)
        if not is_logger_setup:
            with logger_setup_lock:
                is_logger_setup = getattr(logger, "_test_runner_is_setup", False)
                if not is_logger_setup:
                    try:
                        logger.remove(0)
                    except ValueError:
                        ...

                    def logger_sink(message: "Message"):
                        if file := message.record["extra"].get("_log_file"):
                            cast(Path, file).write_text(message, encoding="utf-8")

                    logger.add(logger_sink)
                    setattr(logger, "_test_runner_is_setup", True)

        self.results = {}
        for test in tests.tests:
            meta = TestMeta(
                name=test.__name__,
                description=test.__doc__ or "?",
                is_required=test.test_is_required,
                requires_required=test.test_requires_required,
            )

            if meta.requires_required and not self.are_required_tests_passed():
                self.results[meta] = False
                continue

            log_file = self.logs_path / f"{meta.name}.log"
            try:
                with logger.contextualize(_log_file=log_file):
                    test(module_path, log_file)
                self.results[meta] = True
            except Exception as e:
                self.results[meta] = str(e)

    def are_required_tests_passed(self) -> bool:
        for test_meta, result in self.get_results().items():
            if test_meta.is_required and result is not True:
                return False

        return True

    def get_results(self) -> TestResults:
        if self.results is None:
            raise ValueError("No tests ran yet")
        return self.results
