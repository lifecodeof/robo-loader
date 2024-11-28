from pathlib import Path
from typing import Any, Protocol, cast, overload


class _TestFunction(Protocol):
    def __call__(self, module_dir: Path, log_file: Path) -> None: ...

    __name__: str
    __doc__: str


class Test(_TestFunction):
    test_is_required: bool
    test_requires_required: bool


class Tests:
    tests: list[Test]

    def __init__(self) -> None:
        self.tests = []

    def __call__(self, *, is_required=False, requires_required=False) -> Any:
        def wrapper(test: _TestFunction) -> Test:
            test = cast(Test, test)
            test.test_is_required = is_required
            test.test_requires_required = requires_required

            self.tests.append(test)
            return test

        return wrapper
