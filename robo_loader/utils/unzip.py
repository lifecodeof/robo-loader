from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from pathlib import Path
import subprocess
import os
import sys
import tempfile
import concurrent
from rich.progress import Progress
from robo_loader import ROOT_PATH

from robo_loader.utils.fs import rmrf


def unzip_with_7z(archive_path: Path, target: Path) -> None:
    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"The archive {archive_path} does not exist.")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        command = [
            str(ROOT_PATH / "bin" / "7-Zip" / "7z.exe"),
            "x",
            str(archive_path),
            f"-o{temp_dir}",
            "-xr!site-packages",
            "-xr!venv",
            "-xr!.venv",
        ]

        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=sys.stderr)

        temp = Path(temp_dir)

        project_dir = infer_project_dir(temp)

        if target.exists():
            if target.is_dir():
                rmrf(target)
            else:
                target.unlink()

        if not target.parent.exists():
            target.parent.mkdir(parents=True)

        project_dir.rename(target)


def infer_project_dir(input_dir: Path) -> Path:
    contents = [p for p in input_dir.iterdir() if p.name != "__MACOSX"]

    if (input_dir / "requirements.txt").exists():
        return input_dir
    elif (rb := input_dir / "robo_core").exists():
        return infer_project_dir(rb)
    elif (rb := input_dir / "robo-core").exists():
        return infer_project_dir(rb)
    elif len(contents) == 1 and contents[0].is_dir():
        return infer_project_dir(contents[0])
    else:
        subprocess.call(["tree.com", str(input_dir)])
        raise Exception(f"Unknown archive structure")


def main():
    target_dir = ROOT_PATH / "modules"
    if not target_dir.exists():
        target_dir.mkdir(exist_ok=True)

    gdrive_path = ROOT_PATH / "gdrive"
    gdrive_files = list(gdrive_path.iterdir())

    target_files = list(target_dir.iterdir())

    with ThreadPoolExecutor(max_workers=10) as executor, Progress() as progress:
        task = progress.add_task("Deleting old files", total=len(target_files))
        futures = [executor.submit(rmrf, dir) for dir in target_files]

        for future in concurrent.futures.as_completed(futures):
            future.result()
            progress.advance(task)

    for file in progress.track(gdrive_files, description="Extracting files"):
        unzip_with_7z(file, target_dir / file.stem)


if __name__ == "__main__":
    main()
