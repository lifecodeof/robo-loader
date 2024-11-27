from dataclasses import dataclass
from os import name
from pathlib import Path
from typing import Literal, TypedDict
from robo_loader.testing.utils import Test
from robo_loader.testing.unit_tests import tests


@dataclass(frozen=True)
class TestMeta:
    name: str
    description: str
    is_required: bool


TestResults = dict[TestMeta, str | Literal[True]]


class TestRunner:
    results: TestResults | None = None

    def run(self, module_path: Path):
        self.results = {}
        for test in tests.tests:
            meta = TestMeta(
                name=test.__name__,
                description=test.__doc__ or "?",
                is_required=test.test_is_required,
            )
            try:
                test(module_path)
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
