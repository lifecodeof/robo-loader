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

logs_path = ROOT_PATH / "logs"
logs_path.mkdir(exist_ok=True)


test_script = ROOT_PATH / "test_one.py"


def main():
    for log_file in logs_path.iterdir():
        if log_file.is_file():
            log_file.unlink()
        else:
            shutil.rmtree(log_file)

    (logs_path / "passed").mkdir(exist_ok=True)

    module_paths = module_loader.get_module_paths()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(test_module, module_path) for module_path in module_paths
        ]

        with rich.progress.Progress() as progress:
            task = progress.add_task("Testing modules...", total=len(module_paths))
            for future in concurrent.futures.as_completed(futures):
                future.result()
                progress.advance(task)


def test_module(module_path: Path):
    log_file = logs_path / f"{module_path.stem}.log"
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
    else:
        os.rename(log_file, (logs_path / "passed" / f"{module_path.stem}.log"))
        rich.print(f"[green]Test passed for module: {module_path.stem}")


if __name__ == "__main__":
    main()
