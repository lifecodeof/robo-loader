from pathlib import Path
from tempfile import TemporaryDirectory

from loader.utils.unzip import unzip_with_7z


def test_module(archive_path: Path):
    with TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)

        unzip_with_7z(archive_path, temp / "module")
        
