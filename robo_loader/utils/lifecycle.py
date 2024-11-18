import rich
import rich.rule
from robo_loader.utils.gdrive_dl import main as gdrive_dl
from robo_loader.utils.unzip import main as unzip
from robo_loader.utils.test_all import main as test_all


def main():
    rich.print(rich.rule.Rule("GDRIVE DOWNLOAD"))
    gdrive_dl()
    rich.print(rich.rule.Rule("UNZIP"))
    unzip()
    rich.print(rich.rule.Rule("TEST ALL"))
    test_all()
