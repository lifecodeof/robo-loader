from datetime import datetime
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

    gdrive_file_iter = drive.ListFile(
        {"q": f"'{folder_id}' in parents and trashed=false"}
    ).GetList()
    gdrive_file_list = list(gdrive_file_iter)

    user_files = {}
    for file in track(gdrive_file_list, "[green]Comparing files..."):
        username = file["lastModifyingUserName"]
        if username not in user_files:
            user_files[username] = file
        else:
            existing_file_mod_date = datetime.fromisoformat(
                user_files[username]["modifiedDate"]
            )
            current_file_mod_date = datetime.fromisoformat(file["modifiedDate"])
            if current_file_mod_date > existing_file_mod_date:
                user_files[username] = file

    files = list(user_files.values())
    downloaded_files: list[str] = list()

    for file in track(gdrive_file_list, "[green]Downloading files..."):
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
        downloaded_files.append(file_name)

    if downloaded_files:
        rich.print(f"[green]Downloaded: {downloaded_files!r}")
    else:
        rich.print(f"[yellow]No new files to download")

    # gdrive_filenames = [file["title"] for file in files]
    # for file in track(
    #     list(destination.iterdir()),
    #     "[green]Deleting old files...",
    # ):
    #     if file.name not in gdrive_filenames:
    #         file.unlink()
    #         rich.print(f"[red]Deleted {file.name!r}")


if __name__ == "__main__":
    main()
