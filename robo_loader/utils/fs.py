import os
from pathlib import Path
import shutil
from typing import Callable


def rmrf(path: Path):
    try:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)
        return
    except PermissionError:
        pass

    def safe_rm(fn: Callable):
        try:
            fn()
        except PermissionError as e:
            os.chmod(e.filename, 0o777)
            fn()

    if not path.is_dir():
        safe_rm(path.unlink)
        return

    to_delete = []
    stack = [path]
    while stack:
        current = stack.pop()
        to_delete.append(current)
        for p in current.iterdir():
            if p.is_dir():
                stack.append(p)
            else:
                safe_rm(p.unlink)

    for p in reversed(to_delete):
        safe_rm(p.rmdir)
