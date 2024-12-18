import asyncio
from enum import Enum
import importlib.util
from multiprocessing.managers import ListProxy
import os
import sys
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TypeAlias
import warnings

from loguru import logger

import robo_loader.impl.dummy_core as dummy_core
from robo_loader.impl.core_impl import CoreImpl
from robo_loader.impl.venv_manager import VenvManager


class ModuleInfo(Enum):
    STARTING = 0
    INSTALLING_REQS = 1
    LOADING = 2
    RUNNING = 3
    STOPPED = 4
    ERRORED = 5

    @staticmethod
    def to_str(info: "ModuleInfo") -> str:
        match info:
            case ModuleInfo.STARTING:
                return "Başlatılıyor"
            case ModuleInfo.INSTALLING_REQS:
                return "Gereksinimler kuruluyor"
            case ModuleInfo.LOADING:
                return "Yükleniyor"
            case ModuleInfo.RUNNING:
                return "Çalışıyor"
            case ModuleInfo.STOPPED:
                return "Durduruldu"
            case ModuleInfo.ERRORED:
                return "Hata"

        return "Bilinmiyor"


InfoQueue: TypeAlias = "Queue[tuple[str, ModuleInfo]]"


class ModuleProcess(Process):
    def __init__(
        self,
        module_path: Path,
        core_args: dict,
        venvs_path: Path,
        log_path: Path | None,
        info_queue: "InfoQueue | None",
    ):
        super().__init__(daemon=True, name=f"ModuleProcess-{module_path.name}")
        self.module_path = module_path
        self.core_args = core_args
        self.venvs_path = venvs_path
        self.log_path = log_path
        self.info_queue = info_queue

    @property
    def name(self) -> str:
        return self.module_path.name

    def run(self):
        os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"
        os.environ["OPENCV_LOG_LEVEL"] = "OFF"

        try:
            import cv2  # type: ignore

            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
        except ImportError:
            pass

        self.setup_logging()

        self._run_module(
            self.module_path,
            self.core_args,
            self.venvs_path,
        )

    def setup_logging(self):
        if self.log_path is not None:

            def _redirect_stream(stream_name, target_file: Path):
                """Redirect a C-level stream like stdout or stderr."""

                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.touch()

                file = open(target_file, "w", buffering=1, encoding="utf-8")
                setattr(sys, stream_name, file)

            warnings.filterwarnings("ignore")
            logger.remove(0)
            logger.add(self.log_path)

            _redirect_stream(
                "stdout", self.log_path.with_stem(self.log_path.stem + ".stdout")
            )

            _redirect_stream(
                "stderr", self.log_path.with_stem(self.log_path.stem + ".stderr")
            )

    def _report_info(self, info: ModuleInfo):
        if self.info_queue is not None:
            self.info_queue.put_nowait((self.module_path.name, info))

    def _run_module(
        self,
        module_dir: Path,
        args: dict,
        venvs_path: Path,
    ):
        title_file = module_dir / "TITLE.txt"
        author_file = module_dir / "AUTHOR.txt"

        module_name = module_dir.name
        title = (
            title_file.read_text(encoding="utf-8").strip()
            if title_file.exists()
            else "Bilinmiyor"
        )
        author = (
            author_file.read_text(encoding="utf-8").strip()
            if author_file.exists()
            else "Bilinmiyor"
        )

        core_impl = CoreImpl(
            module_name=module_name,
            author=author,
            title=title,
            root_path=module_dir,
            **args,
        )

        requirements_file = module_dir / "requirements.txt"
        venv_manager = VenvManager(module_name, venvs_path)

        self._report_info(ModuleInfo.INSTALLING_REQS)
        venv_manager.ensure_requirements(requirements_file)
        venv_manager.activate()

        self._report_info(ModuleInfo.LOADING)
        sys.path.append(str(module_dir.absolute()))
        dummy_core.actual_impl = core_impl
        sys.modules["core"] = dummy_core
        os.chdir(module_dir)

        spec = importlib.util.spec_from_file_location(
            module_dir.name, module_dir / "main.py"
        )
        if spec is None:
            logger.warning(
                f"Module '{module_dir.name}' could not be imported. (No spec)"
            )
            return

        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise Exception(
                f"Module '{module_dir.name}' could not be imported. (No spec loader)"
            )

        try:
            spec.loader.exec_module(module)
        except:
            logger.exception(f"Module '{module_dir.name}' could not be imported.")
            raise

        if (not hasattr(module, "main")) or (not callable(module.main)):
            raise Exception(f"Module '{module_dir.name}' has no 'main' function.")

        self._report_info(ModuleInfo.RUNNING)
        try:
            asyncio.run(module.main(core_impl))  # type: ignore
            self._report_info(ModuleInfo.STOPPED)
        except:
            logger.exception(f"Module '{module_dir.name}' has thrown an exception.")
            self._report_info(ModuleInfo.ERRORED)
            raise
