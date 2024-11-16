from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from loguru import logger

from robo_loader.impl.module_loader import load
from robo_loader.server_factory import start_server
from robo_loader.utils.unzip import unzip_with_7z


def test_module(archive_path: Path):
    with TemporaryDirectory() as td:
        temp = Path(td)

        logger.info("Started testing with interpreter: " + sys.executable)

        module_path = temp / "modules" / "_current"
        logger.info("unzipping archive to: " + str(module_path))
        unzip_with_7z(archive_path, module_path)

        logger.info("starting server with module: " + str(module_path))

        venvs_path = temp / "venvs"
        venvs_path.mkdir(exist_ok=True)
        start_server(module_paths=[module_path], venvs_path=venvs_path)
