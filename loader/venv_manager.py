from pathlib import Path
import subprocess
import sys
import virtualenv
from loguru import logger
import runpy

REQUIREMENT_CORRECTIONS = {
    "os": None,
    "threading": None,
    "cv2": "opencv-python",
    "wx": "wxPython",
    "sklearn": "scikit-learn",
}

EXTRA_REQUIREMENTS = {
    "elif örencik": ["pandas"],
    "Emre Öztürk": ["setuptools"],
    "Zeynep Gökdağ": ["PyQt5"],
}


class VenvManager:
    venvs_path: Path

    def __init__(self, venv_name: str) -> None:
        self.venv_name = venv_name
        self.venvs_path = Path(__file__).parent.parent / "venvs"
        self.venvs_path.mkdir(exist_ok=True)

    def ensure_venv(self) -> None:
        venv_path = (self.venvs_path / self.venv_name).absolute()
        if not venv_path.exists():
            virtualenv.cli_run([str(venv_path), "--python", sys.executable])
            logger.info(f"Created venv: {self.venv_name}")

    def get_interpreter_path(self) -> Path:
        venv_path = self.venvs_path / self.venv_name
        return venv_path / "Scripts" / "python.exe"

    def ensure_requirements(self, requirements_path: Path) -> None:
        self.ensure_venv()

        installed_cache_file = self.venvs_path / self.venv_name / ".installed"
        if (
            installed_cache_file.exists()
            and installed_cache_file.read_text() == requirements_path.read_text()
        ):
            return

        requirements = [
            req.strip() for req in requirements_path.read_text().splitlines()
        ]

        has_made_changes = False
        for false_req, correct_req in REQUIREMENT_CORRECTIONS.items():
            if false_req in requirements:
                requirements.remove(false_req)
                has_made_changes = True
                if correct_req is not None:
                    requirements.append(correct_req)

        for author, extra_reqs in EXTRA_REQUIREMENTS.items():
            if author in self.venv_name:
                requirements.extend(extra_reqs)
                has_made_changes = True

        if has_made_changes:
            requirements_path.write_text("\n".join(requirements))

        interpreter_path = self.get_interpreter_path()
        logger.info(f"Installing requirements for venv: {self.venv_name}")
        pip = subprocess.run(
            [
                str(interpreter_path),
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
            raise Exception(
                f"Failed to install requirements for venv: {self.venv_name}\n{stderr}"
            )

        installed_cache_file.write_text(requirements_path.read_text())
        logger.info(f"Installed requirements for venv: {self.venv_name}")

    def activate(self):
        self.ensure_venv()
        activate_this_path = (
            self.venvs_path / self.venv_name / "Scripts" / "activate_this.py"
        ).absolute()
        runpy.run_path(str((activate_this_path)))
        logger.info(f"Activated venv: {self.venv_name}")


if __name__ == "__main__":
    venv_manager = VenvManager("test")
    venv_manager.ensure_venv()
    venv_manager.ensure_requirements(
        Path(r"C:\Users\Semih\Desktop\robo-loader\modules\robo_core\requirements.txt"),
    )
