from pathlib import Path
import subprocess
import sys
import virtualenv
from loguru import logger
import runpy
from robo_loader import ROOT_PATH

# REQUIREMENT_CORRECTIONS = {
#     "os": None,
#     "threading": None,
#     "cv2": "opencv-python",
#     "wx": "wxPython",
#     "sklearn": "scikit-learn",
# }


class RequirementsError(Exception):
    pass


class VenvManager:
    venvs_path: Path

    def __init__(self, venv_name: str, venvs_path: Path | None = None) -> None:
        self.venv_name = venv_name
        self.venvs_path = venvs_path or ROOT_PATH / "venvs"
        self.venvs_path.mkdir(exist_ok=True)

        logger.info(f"Initializing venv manager in {self.venvs_path}")

    @property
    def venv_path(self) -> Path:
        return self.venvs_path / self.venv_name

    def ensure_venv(self) -> None:
        venv_path = self.venv_path.absolute()
        if not venv_path.exists():
            logger.info(f"Creating venv with {sys.executable}")
            virtualenv.cli_run([str(venv_path), "--python", sys.executable])
            logger.info(f"Created venv: {self.venv_name}")

    @property
    def interpreter_path(self) -> Path:
        return self.venv_path / "Scripts" / "python.exe"

    def ensure_requirements(self, requirements_path: Path) -> None:
        self.ensure_venv()

        installed_cache_file = self.venv_path / ".installed"
        # failed_cache_file = self.venv_path / ".failed"

        if (
            installed_cache_file.exists()
            and installed_cache_file.read_bytes() == requirements_path.read_bytes()
        ):
            return

        # if (
        #     failed_cache_file.exists()
        #     and failed_cache_file.read_bytes() == requirements_path.read_bytes()
        # ):
        #     raise RequirementsError(
        #         f"Failed to install requirements for venv: {self.venv_name}"
        #     )

        logger.info(f"Installing requirements for venv: {self.venv_name}")
        pip = subprocess.run(
            [
                str(self.interpreter_path),
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                str(requirements_path),
            ],
            capture_output=True,
        )

        if pip.returncode != 0:
            stderr = pip.stderr.decode("utf-8")
            # failed_cache_file.write_bytes(requirements_path.read_bytes())
            raise RequirementsError(
                f"Failed to install requirements for venv: {self.venv_name}\n{stderr}"
            )

        installed_cache_file.write_bytes(requirements_path.read_bytes())
        logger.info(f"Installed requirements for venv: {self.venv_name}")

    def activate(self):
        self.ensure_venv()
        activate_this_path = (
            self.venv_path / "Scripts" / "activate_this.py"
        ).absolute()
        runpy.run_path(str((activate_this_path)))
        logger.info(f"Activated venv: {self.venv_name}")
