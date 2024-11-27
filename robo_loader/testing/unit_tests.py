from pathlib import Path
from re import I

from loguru import logger
from robo_loader.impl.venv_manager import RequirementsError, VenvManager
from robo_loader.testing.utils import Tests


tests = Tests()


@tests()
def test_has_photo(module_dir: Path):
    """Fotoğraf dosyası olmalı"""
    photo_path = module_dir / "PHOTO.png"
    assert photo_path.exists(), "PHOTO.png fotoğrafı bulunamadı."


@tests()
def test_has_author(module_dir: Path):
    """AUTHOR.txt dosyası olmalı"""
    author_path = module_dir / "AUTHOR.txt"
    assert author_path.exists(), "AUTHOR.txt dosyası bulunamadı."
    if author_path.read_text().strip() == "":
        assert False, "AUTHOR.txt dosyası boş."


@tests()
def test_has_title(module_dir: Path):
    """TITLE.txt dosyası olmalı"""
    title_path = module_dir / "TITLE.txt"
    assert title_path.exists(), "TITLE.txt dosyası bulunamadı."
    if title_path.read_text().strip() == "":
        assert False, "TITLE.txt dosyası boş."


@tests(is_required=True)
def test_has_main_py(module_dir: Path):
    """main.py dosyası olmalı"""
    main_py_path = module_dir / "main.py"
    assert main_py_path.exists(), "main.py dosyası bulunamadı."


@tests(is_required=True)
def test_main_py_has_main_fn(module_dir: Path):
    """main.py dosyasında main fonksiyonu olmalı"""
    import ast

    main_py_path = module_dir / "main.py"
    main_py_contents = main_py_path.read_text(encoding="utf-8")
    main_py_tree = ast.parse(main_py_contents)
    for node in ast.walk(main_py_tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "main":
            assert isinstance(
                node, ast.AsyncFunctionDef
            ), "main fonksiyonu async olmalı."

            args_len = len(node.args.args)
            assert args_len == 1, "main fonksiyonunun sadece 1 parametresi olmalı"

            arg = node.args.args[0]
            assert arg.arg == "core", "main fonksiyonunun parametresi 'core' olmalı"

            break
    else:
        assert False, "main.py dosyasında main fonksiyonu bulunamadı."


@tests(is_required=True)
def test_requirements_installable(module_dir: Path):
    """requirements.txt dosyasındaki paketler yüklenebilmeli"""
    logger.disable("robo_loader.impl.venv_manager")
    venv_manager = VenvManager(module_dir.name, module_dir)
    try:
        venv_manager.ensure_requirements(module_dir / "requirements.txt")
    except RequirementsError:
        assert False, "requirements.txt hatalı."
