from PyInstaller import __main__ as pyi

if __name__ == "__main__":
    pyi.run(
        [
            "main.py",
            "--onefile",
            "--hidden-import=serial",
            "--hidden-import=loader",
            "--hidden-import=loader.load",
        ]
    )
