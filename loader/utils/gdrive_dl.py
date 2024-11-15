from pathlib import Path
import shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from rich.progress import Progress, track


def main():
    destination = Path(__file__).parent.parent / "gdrive"
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

    with Progress() as progress:
        task = progress.add_task("[green]Downloading files...", total=len(file_list))

        for file in file_list:
            file_name = file["title"]
            if (destination / file_name).exists():
                progress.advance(task)
                continue

            file.GetContentFile(f"{destination}/{file_name}")
            progress.advance(task)


if __name__ == "__main__":
    main()
