import rich
import rich.rule
from gdrive_dl import main as gdrive_dl
from unzip import main as unzip
from test_all import main as test_all

if __name__ == "__main__":
    rich.print(rich.rule.Rule("GDRIVE DOWNLOAD"))
    gdrive_dl()
    rich.print(rich.rule.Rule("UNZIP"))
    unzip()
    rich.print(rich.rule.Rule("TEST ALL"))
    test_all()
