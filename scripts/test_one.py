import sys
from pathlib import Path
from loguru import logger
from multiprocessing import Event


if __name__ == "__main__":
    from setup_path import setup_sys_path

    setup_sys_path()

    from loader import load

    module_name = sys.argv[1]
    module_path = Path(__file__).parent.parent / "modules" / module_name


    logger.info(f"Loading module {module_path.stem}")

    cancel_event = Event()

    def cancel(*args, **kwargs):
        cancel_event.set()

    try:
        load.load([module_path], cancel, cancel, cancel_event)
        logger.info(f"Module {module_path.stem} passed successfully")
    except KeyboardInterrupt:
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {module_path.stem}"
        )
        exit(1)
