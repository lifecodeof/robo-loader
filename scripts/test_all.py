import os
from pathlib import Path
import shutil
import subprocess
import sys
import concurrent.futures

import rich
from rich import table
import rich.live
import rich.progress
import rich.status

logs_path = Path(__file__).parent.parent / "logs"
logs_path.mkdir(exist_ok=True)


test_script = Path(__file__).parent / "test_one.py"


def main():
    from setup_path import setup_sys_path

    setup_sys_path()

    from loader import load

    for log_file in logs_path.iterdir():
        if log_file.is_file():
            log_file.unlink()
        else:
            shutil.rmtree(log_file)
    
    (logs_path / "passed").mkdir(exist_ok=True)

    module_paths = load.get_module_paths()

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
