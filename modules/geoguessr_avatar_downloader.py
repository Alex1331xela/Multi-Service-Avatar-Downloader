import sys

sys.dont_write_bytecode = True

import os
from rich import print
from rich.progress import Progress, TaskID

# ensure project root is on sys.path so sibling 'modules' imports resolve when running this file directly
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.common_downloader_functions import (
    create_config_file_if_only_default,
    download_url_to_json,
    progress_bar,
    download_url_to_bytes,
    file_hash,
    find_next_available_file_path,
    save_contents_to_file,
)

try:
    from config import DEBUG_MODE, GEOGUESSR_AVATAR_IDS, GEOGUESSR_DOWNLOAD_FOLDER
except ImportError:
    from config_default import DEBUG_MODE, GEOGUESSR_AVATAR_IDS, GEOGUESSR_DOWNLOAD_FOLDER

GEOGUESSR_AVATAR_POSES = ["fullBodyPath", "mugshotPath", "pinImageId"]

GEOGUESSR_USER_DATA_LINK_TEMPLATE = "https://www.geoguessr.com/api/v4/player-identities/{player_id}"
GEOGUESSR_IMAGE_LINK_TEMPLATE = "https://www.geoguessr.com/images/resize:auto:2048:2048/gravity:ce/plain/{image_id}"

saved_hashes = set()  # to avoid saving duplicate images for different poses of the same avatar


def download_geoguessr_avatars(progress: Progress) -> None:
    total_downloads = len(GEOGUESSR_AVATAR_IDS) * len(GEOGUESSR_AVATAR_POSES)
    task = progress.add_task("[magenta]Downloading GeoGuessr avatars...[/]", total=total_downloads)

    for avatar in GEOGUESSR_AVATAR_IDS:
        for pose in GEOGUESSR_AVATAR_POSES:
            _download_character_avatar(progress, task, avatar, pose)


def _download_character_avatar(progress: Progress, task: TaskID, avatar: dict[str, str], pose: str) -> None:
    user_url = GEOGUESSR_USER_DATA_LINK_TEMPLATE.format(player_id=avatar["user_id"])
    image_url, nick = _get_image_url_from_geoguessr_profile_api(user_url, pose)
    if image_url == "":
        print(f"[red]Error[/]: Failed to retrieve image URL for [blue]{avatar}[/] from {user_url}")
        progress.update(task, advance=1)
        return
    else:
        image_url = GEOGUESSR_IMAGE_LINK_TEMPLATE.format(image_id=image_url)

    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {image_url}")

    image_content = download_url_to_bytes(image_url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download image for [blue]{avatar}[/] from {image_url}")
        progress.update(task, advance=1)
        return

    if file_hash(image_content) == "d41d8cd98f00b204e9800998ecf8427e":
        print(f"[red]Error[/]: Empty image returned when fetching image for [blue]{avatar}[/] from {image_url}")
        progress.update(task, advance=1)
        return

    if file_hash(image_content) in saved_hashes:
        if DEBUG_MODE:
            print(
                f"[yellow]Warning[/]: Duplicate image detected for [blue]{avatar}[/]'s [blue]{pose}[/] from {image_url}. This image has already been downloaded for a different pose, so it will be skipped to avoid duplicates."
            )
        progress.update(task, advance=1)
        return

    saved_hashes.add(file_hash(image_content))

    file_name = f"geoguessr_{nick}_{pose}.png"
    file_path = find_next_available_file_path(GEOGUESSR_DOWNLOAD_FOLDER, file_name, image_content)
    if file_path:
        save_contents_to_file(file_path, image_content)
    progress.update(task, advance=1)


def _get_image_url_from_geoguessr_profile_api(user_url: str, pose: str) -> tuple[str, str]:
    """
    Fetches the avatar image URL from the GeoGuessr API.

    :param user_url: The user profile URL to fetch the avatar image from.
    :param pose: The pose for which to fetch the image URL.
    :return: The avatar image URL and nickname if available, otherwise `None`.
    """
    try:
        data_json = download_url_to_json(user_url)
        if data_json and "player" in data_json and data_json["player"]:
            player = data_json["player"]
            if pose in player:
                return player[pose], player["nick"]
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching {user_url}: {error}")
    return "", ""


if __name__ == "__main__":
    create_config_file_if_only_default()
    with progress_bar() as progress:
        download_geoguessr_avatars(progress)
