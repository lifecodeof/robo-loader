from pathlib import Path
import shutil
import subprocess
import os
import tempfile
from rich import progress

from loguru import logger

target = Path(__file__).parent.parent / "modules"


def unzip_with_7z(archive_path: Path) -> None:
    """
    Unzips an archive using 7z.

    :param archive_path: Path to the archive file.
    :param extract_to: Directory where the files should be extracted.
    """

    if not os.path.exists(archive_path):
        raise FileNotFoundError(f"The archive {archive_path} does not exist.")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        command = ["7z", "x", str(archive_path), f"-o{temp_dir}", "-xr!site-packages"]

        try:
            subprocess.check_call(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            logger.exception("Failed to extract archive")

        temp = Path(temp_dir)
        temp_contents = list(temp.iterdir())

        archive_name = archive_path.stem
        project_dir = infer_project_dir(temp)
        project_dir.rename(target / archive_name)


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
    gdrive_path = Path(__file__).parent.parent / "gdrive"
    gdrive_files = list(gdrive_path.iterdir())

    target_files = list(target.iterdir())

    for dir in progress.track(target_files, description="Deleting old files"):
        shutil.rmtree(dir)

    for file in progress.track(gdrive_files, description="Extracting files"):
        if (target / file.stem).exists():
            logger.info(f"Skipping {file.stem} as it already exists")

        unzip_with_7z(file)


if __name__ == "__main__":
    main()
