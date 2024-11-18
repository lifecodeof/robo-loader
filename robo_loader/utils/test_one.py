import sys
from multiprocessing import Event

from loguru import logger

from robo_loader import ROOT_PATH
from robo_loader.impl import module_loader


def main(module_name: str | None = None):
    if module_name is None:
        module_name = sys.argv[1]

    module_path = ROOT_PATH / "modules" / module_name

    logger.info(f"Loading module {module_path.stem}")

    cancel_event = Event()

    state_changed = False

    def on_state_change(*args, **kwargs):
        nonlocal state_changed
        state_changed = True
        cancel_event.set()

    def on_message(_id, message: str):
        logger.warning(f"MESSAGE USED: {message}")

    try:
        module_loader.load(
            module_paths=[module_path],
            on_state_change=on_state_change,
            on_message=on_message,
            cancellation_event=cancel_event,
        )

        if state_changed:
            logger.info(f"Module {module_path.stem} passed successfully")
        else:
            logger.error(f"Module {module_path.stem} failed (state did not change)")
            exit(1)

    except KeyboardInterrupt:
        raise
    except BaseException:
        logger.exception(
            f"An error occurred while loading the module: {module_path.stem}"
        )
        exit(1)


if __name__ == "__main__":
    main()
