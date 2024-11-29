from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import rich
from rich.progress import track
from robo_loader import ROOT_PATH
import hashlib


def calculate_md5(path: Path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with path.open("rb") as f:
        # Read file in chunks to avoid memory issues with large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def main():
    destination = ROOT_PATH / "gdrive"
    destination.mkdir(exist_ok=True)

    # for file in track(list(destination.iterdir()), description="Deleting old files"):
    #     file.unlink()

    folder_id = (
        "13Gx4livXMRLs7BBqT3H6BTeJE6YLE7zCddBSnnevaGzgBxvaTQw0jueorsMsd9-iW2n5gwg6"
    )

    # Authenticate and create the PyDrive client
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("creds")
    # gauth.LocalWebserverAuth()  # Creates local webserver and automatically handles authentication
    # gauth.SaveCredentialsFile("creds")
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile(
        {"q": f"'{folder_id}' in parents and trashed=false"}
    ).GetList()

    new_files: list[str] = []
    for file in track(file_list, "[green]Downloading files...", len(file_list)):
        file_name = file["title"]
        local_path = destination / file_name
        if local_path.exists():
            remote_md5 = file["md5Checksum"]
            local_md5 = calculate_md5(local_path)
            if remote_md5 == local_md5:
                continue
            else:
                local_path.unlink()

        file.GetContentFile(str(local_path))
        new_files.append(file_name)

    if new_files:
        rich.print(f"[green]Downloaded {new_files!r} new files")
    else:
        rich.print(f"[yellow]No new files to download")


if __name__ == "__main__":
    main()
