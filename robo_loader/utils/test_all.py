import concurrent.futures
from pathlib import Path

import rich
import rich.live
import rich.progress
import rich.status
import rich.terminal_theme
import rich.theme
import rich.themes

from robo_loader import ROOT_PATH
from robo_loader.impl import module_loader
from robo_loader.testing.runner import TestRunner, TestResults, TestStatus
from robo_loader.utils.fs import rmrf
from rich.markup import escape as e

logs_path = ROOT_PATH / "logs"
Results = dict[Path, TestResults]


class UngracefulThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor):
    def __exit__(self, *args):
        self.shutdown(wait=False, cancel_futures=True)
        return False


def test_all():
    if logs_path.exists():
        rmrf(logs_path)
    logs_path.mkdir(exist_ok=True)

    def test_module(module_path: Path) -> tuple[Path, TestResults]:
        test_runner = TestRunner(logs_path / module_path.name)
        test_results = test_runner.run(module_path)

        return module_path, test_results

    module_paths = module_loader.get_module_paths()
    with UngracefulThreadPoolExecutor(max_workers=10) as executor:
        results: Results = {}
        futures = [
            executor.submit(test_module, module_path) for module_path in module_paths
        ]

        with rich.progress.Progress() as progress:
            task = progress.add_task("Testing modules...", total=len(module_paths))
            for future in concurrent.futures.as_completed(futures):
                module_path, test_results = future.result()
                results[module_path] = test_results
                progress.advance(task)

    return results


def report_results(results: Results):
    rich.print("[bold]Test sonuçları:")
    console = rich.console.Console(record=True)
    for module_path, test_results in results.items():
        is_all_success = all(
            result.status is TestStatus.PASSED for result in test_results.values()
        )
        if is_all_success:
            console.print(f"[green]✓ {e(module_path.stem)}")
            continue

        console.print(f"[red]✗ {e(module_path.stem)}")
        for test, result in test_results.items():
            test_repr = f"{test.name} ({test.description})"
            match result.status:
                case TestStatus.PASSED:
                    console.print(f"[green]  ✓ {e(test_repr)}")
                case TestStatus.NOT_RUN:
                    console.print(f"[yellow]  ! {e(test_repr)}: {e(result.message)}")
                case TestStatus.FAILED:
                    console.print(f"[red]  ✗ {e(test_repr)}: {e(result.message)}")

    console.save_html(
        str(logs_path / "test_results.html"), theme=rich.terminal_theme.MONOKAI
    )


def package_to_share():
    import shutil

    share_dir = ROOT_PATH / "share"
    if share_dir.exists():
        rmrf(share_dir)
    share_dir.mkdir()

    html_file = logs_path / "test_results.html"
    shutil.copy(html_file, share_dir / "test_results.html")

    shutil.make_archive(str(share_dir / "logs"), "zip", logs_path)


def main():
    results = test_all()
    report_results(results)
    package_to_share()


if __name__ == "__main__":
    main()
