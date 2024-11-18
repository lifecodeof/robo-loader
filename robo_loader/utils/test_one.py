import sys
from multiprocessing import Event

from loguru import logger

from robo_loader import ROOT_PATH
from robo_loader.impl import module_loader


def main():
    module_name = sys.argv[1]
    module_path = ROOT_PATH / "modules" / module_name

    logger.info(f"Loading module {module_path.stem}")

    cancel_event = Event()

    def cancel(*args, **kwargs):
        cancel_event.set()

    try:
        module_loader.load([module_path], cancel, cancel, cancel_event)
        logger.info(f"Module {module_path.stem} passed successfully")
    except KeyboardInterrupt:
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {module_path.stem}"
        )
        exit(1)
