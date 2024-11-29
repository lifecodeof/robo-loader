from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, cast


@dataclass(frozen=True)
class TestContext:
    module_path: Path
    log_file: Path


class _TestFunction(Protocol):
    def __call__(self, ctx: TestContext) -> None: ...

    __name__: str
    __doc__: str


@dataclass(frozen=True)
class TestMeta:
    name: str
    description: str = field(repr=False)
    dependencies: frozenset["Test"]


class Test(_TestFunction):
    test_meta: TestMeta


class Tests:
    tests: list[Test]

    def __init__(self) -> None:
        self.tests = []

    def __call__(self, *, depends: list[Test] | None = None) -> Any:
        def wrapper(test: _TestFunction) -> Test:
            test = cast(Test, test)
            test.test_meta = TestMeta(
                name=test.__name__,
                description=test.__doc__ or "?",
                dependencies=frozenset(depends or []),
            )

            self.tests.append(test)
            return test

        return wrapper

    def get_test(self, test_meta: TestMeta) -> Test:
        for test in self.tests:
            if test.test_meta == test_meta:
                return test
        raise ValueError(f"Test not found: {test_meta.name}")
