from pathlib import Path
import sys


def setup_sys_path():
    sys.path.append(str(Path(__file__).parent.parent.absolute()))
