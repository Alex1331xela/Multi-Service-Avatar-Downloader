import sys

sys.dont_write_bytecode = True

import random
from rich import print
from rich.progress import Progress, TaskID

from common_downloader_functions import create_config_file_if_only_default, progress_bar, download_url_to_bytes, file_hash, find_next_available_file_path, save_contents_to_file

try:
    from config import DEBUG_MODE, GTA_CHARACTER_NAMES, GTA_DOWNLOAD_FOLDER
except ImportError:
    from config_default import DEBUG_MODE, GTA_CHARACTER_NAMES, GTA_DOWNLOAD_FOLDER

GTA_LINK_TEMPLATE = "https://prod.cloud.rockstargames.com/members/np/{random_four_digits}/{character_name}/publish/gta5/mpchars/0_ps4.png"


def download_gta_avatars(progress: Progress) -> None:
    total_downloads = len(GTA_CHARACTER_NAMES)
    task = progress.add_task("[magenta]Downloading GTA Online avatars...[/]", total=total_downloads)

    for character_name in GTA_CHARACTER_NAMES:
        _download_character_avatar(progress, task, character_name)


def _download_character_avatar(progress: Progress, task: TaskID, character_name: str) -> None:
    random_seed = f"{random.randint(0, 9999):04d}"
    url = GTA_LINK_TEMPLATE.format(random_four_digits=random_seed, character_name=character_name)
    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {url}")

    image_content = download_url_to_bytes(url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download image for [blue]{character_name}[/] from {url}")
        progress.update(task, advance=1)
        return

    if file_hash(image_content) == "d41d8cd98f00b204e9800998ecf8427e":
        print(f"[red]Error[/]: Empty image returned when fetching image for [blue]{character_name}[/] from {url}")
        progress.update(task, advance=1)
        return

    file_name = f"gta_online_{character_name}.png"
    file_path = find_next_available_file_path(GTA_DOWNLOAD_FOLDER, file_name, image_content)
    if file_path:
        save_contents_to_file(file_path, image_content)
    progress.update(task, advance=1)


if __name__ == "__main__":
    create_config_file_if_only_default()
    with progress_bar() as progress:
        download_gta_avatars(progress)
