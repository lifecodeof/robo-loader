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
from robo_loader.testing.runner import TestRunner, TestResults
from robo_loader.utils.fs import rmrf


logs_path = ROOT_PATH / "logs"
Results = dict[Path, TestResults]


def test_all():
    if logs_path.exists():
        rmrf(logs_path)
    logs_path.mkdir(exist_ok=True)

    def test_module(module_path: Path) -> tuple[Path, TestResults]:
        test_runner = TestRunner(logs_path / module_path.name)
        test_runner.run(module_path)

        return module_path, test_runner.get_results()

    module_paths = module_loader.get_module_paths()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
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
        is_all_success = all(result is True for result in test_results.values())
        if is_all_success:
            console.print(f"[green]✓ {module_path.stem}")
            continue

        console.print(f"[red]✗ {module_path.stem}")
        for test, result in test_results.items():
            test_repr = f"{test.name} ({test.description})"
            if result is True:
                console.print(f"[green]  ✓ {test_repr}")
            elif result is False:
                console.print(f"[yellow]  ! {test_repr}: Zorunlu testler geçilemedi")
            else:
                console.print(f"[red]  ✗ {test_repr}: {result}")

    console.save_html(
        str(logs_path / "test_results.html"), theme=rich.terminal_theme.MONOKAI
    )


def main():
    results = test_all()
    report_results(results)


if __name__ == "__main__":
    main()
