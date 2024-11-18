from loguru import logger
from rich import get_console
from robo_loader.impl.module_loader import get_module_path, get_module_paths
from robo_loader.utils import test_one
from rich.prompt import Confirm, Prompt
from rapidfuzz import process


def main():
    console = get_console()
    module_names = [path.name for path in get_module_paths()]

    while True:
        name = Prompt.ask("Enter the module name")
        module_name, _, _ = process.extractOne(name, module_names)

        if Confirm.ask("Clean screen?"):
            console.clear()

        try:
            logger.info(f"Installing and testing module {module_name}")
            test_one.main(module_name)
        except KeyboardInterrupt:
            if Confirm.ask("Do you want to continue testing?"):
                continue
            else:
                break
        except BaseException:
            logger.exception("An error occurred while testing")
