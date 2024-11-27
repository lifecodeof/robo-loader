import concurrent.futures
from enum import Enum, auto
import pickle
import signal
import subprocess
import sys
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


class E2EResult(Enum):
    SUCCESS = auto()
    FAILED = auto()
    TIMEOUT = auto()
    NOT_RUNNED = auto()


logs_path = ROOT_PATH / "logs"


def test_all():
    if logs_path.exists():
        rmrf(logs_path)
    logs_path.mkdir(exist_ok=True)

    passed_logs_path = logs_path / "passed"
    passed_logs_path.mkdir(exist_ok=True)

    failed_logs_path = logs_path / "failed"
    failed_logs_path.mkdir(exist_ok=True)

    ongoing_logs_path = logs_path / "ongoing"
    ongoing_logs_path.mkdir(exist_ok=True)

    test_script = Path(__file__).parent / "test_one.py"

    def test_module(module_path: Path) -> tuple[Path, TestResults, E2EResult]:
        def gracefully_terminte_children(process: subprocess.Popen):
            if sys.platform == "win32":
                subprocess.check_call(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            if process.poll() is not None:
                return

            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()

        test_runner = TestRunner()
        test_runner.run(module_path)
        if not test_runner.are_required_tests_passed():
            return module_path, test_runner.get_results(), E2EResult.NOT_RUNNED

        log_file = ongoing_logs_path / f"{module_path.stem}.log"

        def open_file(i: int = 0):
            nonlocal log_file
            _f = log_file

            try:
                if i > 0:
                    _f = _f.with_name(f"{module_path.stem}_{i}.log")
                return _f.open("w", encoding="utf-8", errors="replace")
            except PermissionError:
                return open_file(i + 1)

        with open_file() as log_io:
            # None means timeout
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-u",
                    str(test_script),
                    module_path.name,
                ],
                stderr=log_io,
                stdout=log_io,
                text=True,
                encoding="utf-8",
            )

            try:
                return_code = process.wait(180)
                e2e_result = E2EResult.SUCCESS if return_code == 0 else E2EResult.FAILED
            except subprocess.TimeoutExpired:
                log_io.write("\n\nTimeout (3m) exceeded.")
                rich.print(
                    f"[yellow]Timeout (3m) exceeded for module: {module_path.stem}"
                )
                e2e_result = E2EResult.TIMEOUT
                gracefully_terminte_children(process)

        try:
            if e2e_result == E2EResult.SUCCESS:
                rich.print(f"[green]Test passed for module: {module_path.stem}")
                log_file.rename(passed_logs_path / log_file.name)
            else:
                rich.print(f"[red]Test failed for module: {module_path.stem}")
                log_file.rename(failed_logs_path / log_file.name)
        except:
            pass

        return module_path, test_runner.get_results(), e2e_result

    module_paths = module_loader.get_module_paths()
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        results: dict[Path, tuple[TestResults, E2EResult]] = {}
        futures = [
            executor.submit(test_module, module_path) for module_path in module_paths
        ]

        with rich.progress.Progress() as progress:
            task = progress.add_task("Testing modules...", total=len(module_paths))
            for future in concurrent.futures.as_completed(futures):
                module_path, test_results, e2e_result = future.result()
                results[module_path] = (test_results, e2e_result)
                progress.advance(task)

    with (logs_path / "results.pickle").open("wb") as results_file:
        pickle.dump(results, results_file)

    return results


def report_results():
    with (logs_path / "results.pickle").open("rb") as results_file:
        results = pickle.load(results_file)

    rich.print("[bold]Test sonuçları:")
    console = rich.console.Console(record=True)
    for module_path, (test_results, e2e_result) in results.items():
        is_all_success = (
            all(result is not True for result in test_results.values())
            and e2e_result == E2EResult.SUCCESS
        )
        if is_all_success:
            console.print(f"[green]✓ {module_path.stem}")
            continue

        console.print(f"[red]✗ {module_path.stem}")
        for test, result in test_results.items():
            test_repr = f"{test.name} ({test.description})"
            if result is True:
                console.print(f"[green]  ✓ {test_repr}")
            else:
                console.print(f"[red]  ✗ {test_repr}: {result}")

        test_repr = "Genel test (Modülün çalışması ve durum belirtmesi gerekir)"
        match e2e_result:
            case E2EResult.SUCCESS:
                console.print(f"[green]  ✓ {test_repr}")
            case E2EResult.FAILED:
                console.print(f"[red]  ✗ {test_repr} (log dosyasına bakınız)")
            case E2EResult.TIMEOUT:
                console.print(f"[yellow]  ! {test_repr}: Zaman aşımı (3 dakika)")
            case E2EResult.NOT_RUNNED:
                console.print(
                    f"[yellow]  ! {test_repr}: Çalıştırılmadı (Zorunlu testler geçilemedi)"
                )

    console.save_html(
        str(logs_path / "test_results.html"), theme=rich.terminal_theme.MONOKAI
    )


def main():
    test_all()
    report_results()


if __name__ == "__main__":
    main()
