import concurrent.futures
import os
import shutil
import subprocess
import sys
from pathlib import Path

import rich
import rich.live
import rich.progress
import rich.status

from robo_loader import ROOT_PATH
from robo_loader.impl import module_loader


def main():
    logs_path = ROOT_PATH / "logs"
    shutil.rmtree(logs_path)
    logs_path.mkdir(exist_ok=True)

    passed_logs_path = logs_path / "passed"
    passed_logs_path.mkdir(exist_ok=True)

    failed_logs_path = logs_path / "failed"
    failed_logs_path.mkdir(exist_ok=True)

    ongoing_logs_path = logs_path / "ongoing"
    ongoing_logs_path.mkdir(exist_ok=True)

    test_script = Path(__file__).parent / "test_one.py"

    def test_module(module_path: Path):
        log_file = ongoing_logs_path / f"{module_path.stem}.log"
        with log_file.open("w", encoding="utf-8") as log_io:
            return_code = subprocess.call(
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

        if return_code != 0:
            rich.print(f"[red]Test failed for module: {module_path.stem}")
            log_file.rename(failed_logs_path / log_file.name)
        else:
            rich.print(f"[green]Test passed for module: {module_path.stem}")
            log_file.rename(passed_logs_path / log_file.name)

    module_paths = module_loader.get_module_paths()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(test_module, module_path) for module_path in module_paths
        ]

        with rich.progress.Progress() as progress:
            task = progress.add_task("Testing modules...", total=len(module_paths))
            for future in concurrent.futures.as_completed(futures):
                future.result()
                progress.advance(task)


if __name__ == "__main__":
    main()
