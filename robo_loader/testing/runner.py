from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, cast

from loguru import logger
from robo_loader.testing.test_model import Test, TestContext, TestMeta
from robo_loader.testing.unit_tests import tests

if TYPE_CHECKING:
    from loguru import Message


class TestStatus(Enum):
    PASSED = object()
    FAILED = object()
    NOT_RUN = object()


@dataclass(frozen=True)
class TestResult:
    status: TestStatus
    message: str = ""


TestResults = dict[TestMeta, TestResult]

logger_setup_lock = Lock()


class TestRunner:
    logs_path: Path

    def __init__(self, logs_path: Path) -> None:
        self.logs_path = logs_path
        if not self.logs_path.exists():
            self.logs_path.mkdir()

    def run(self, module_path: Path):
        self._setup_logger()

        results: TestResults = {}
        test_queue = tests.tests.copy()

        while test_queue:
            test = test_queue.pop(0)
            meta = test.test_meta

            # If the test has no dependencies, run it immediately
            if not meta.dependencies:
                result = self._run_test(test, module_path)
                results[meta] = result
                continue

            unresolved_dependencies = [
                dep.test_meta
                for dep in meta.dependencies
                if dep.test_meta not in results
            ]
            # If the test has unresolved dependencies, defer it
            if unresolved_dependencies:
                test_queue.append(test)
                continue

            failed_dependencies = [
                dep.test_meta
                for dep in meta.dependencies
                if results[dep.test_meta].status is not TestStatus.PASSED
            ]
            # If the test has failed dependencies, mark it as not run
            if failed_dependencies:
                fd_repr = ", ".join([dep.name for dep in failed_dependencies])
                results[meta] = TestResult(
                    TestStatus.NOT_RUN,
                    f"Çalıştırılmadı. Başarısız gereksinimler: {fd_repr}",
                )
                continue

            # If the test has passed dependencies, run it
            result = self._run_test(test, module_path)
            results[meta] = result

        return results

    def _run_test(self, test: Test, module_path: Path):
        meta = test.test_meta

        log_file = self.logs_path / f"{meta.name}.log"
        try:
            with logger.contextualize(_test_runner_log_file=log_file):
                ctx = TestContext(module_path, log_file)
                test(ctx)
            return TestResult(TestStatus.PASSED)
        except Exception as e:
            return TestResult(TestStatus.FAILED, str(e))

    def _setup_logger(self):
        if not getattr(logger, "_test_runner_is_setup", False):
            with logger_setup_lock:
                if not getattr(logger, "_test_runner_is_setup", False):
                    try:
                        logger.remove(0)
                    except ValueError:
                        ...

                    def logger_sink(message: "Message"):
                        if file := message.record["extra"].get("_test_runner_log_file"):
                            cast(Path, file).write_text(message, encoding="utf-8")

                    logger.add(logger_sink)
                    setattr(logger, "_test_runner_is_setup", True)
