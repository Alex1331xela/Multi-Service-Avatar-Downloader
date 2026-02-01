import sys

sys.dont_write_bytecode = True

from pathlib import Path
from rich import print
from rich.progress import Progress, TaskID
import time


from common_downloader_functions import progress_bar, download_url_to_bytes, download_url_to_json, find_next_available_file_path, save_contents_to_file

try:
    from config import DEBUG_MODE, ROBLOX_USER_IDS, ROBLOX_DOWNLOAD_FOLDER, ROBLOX_SAVE_OUTFIT_IMAGES
except ImportError:
    from config_default import DEBUG_MODE, ROBLOX_USER_IDS, ROBLOX_DOWNLOAD_FOLDER, ROBLOX_SAVE_OUTFIT_IMAGES

ROBLOX_POSES = [{"pose": "avatar", "size": "720x720"}, {"pose": "avatar-headshot", "size": "720x720"}, {"pose": "avatar-bust", "size": "420x420"}]

ROBLOX_LINK_TEMPLATE_AVATAR = "https://thumbnails.roblox.com/v1/users/{pose}?userIds={user_id}&size={size}&format=png"
ROBLOX_LINK_TEMPLATE_CURRENT_OUTFIT = "https://avatar.roblox.com/v1/users/{user_id}/currently-wearing"
ROBLOX_LINK_TEMPLATE_OUTFIT = "https://thumbnails.roblox.com/v1/assets?assetIds={outfit_id}&size=700x700&format=png"


def download_roblox_avatars_and_outfits(progress: Progress) -> None:
    """
    Downloads Roblox avatars and outfits for all users and poses defined in the configuration.
    """
    if ROBLOX_SAVE_OUTFIT_IMAGES:
        task_outfit_loading = progress.add_task("[magenta]Loading Roblox outfit assets...[/]", total=len(ROBLOX_USER_IDS))
        all_asset_ids = _load_outfit_asset_ids_to_list(progress, task_outfit_loading)
    else:
        all_asset_ids = None

    total_downloads = _calculate_total_downloads(all_asset_ids)
    task_downloading_avatars = progress.add_task("[magenta]Downloading Roblox avatars...[/]", total=total_downloads[1])
    if ROBLOX_SAVE_OUTFIT_IMAGES:
        task_downloading_outfits = progress.add_task("[magenta]Downloading Roblox outfits...[/]", total=total_downloads[2])

    for user in ROBLOX_USER_IDS:
        user = _get_missing_user_names_and_ids(user)
        for pose in ROBLOX_POSES:
            _download_roblox_avatars(progress, task_downloading_avatars, user, pose)
    if ROBLOX_SAVE_OUTFIT_IMAGES and all_asset_ids:
        for outfit_id in all_asset_ids:
            _download_roblox_outfits(progress, task_downloading_outfits, outfit_id)


def _load_outfit_asset_ids_to_list(progress: Progress, task: TaskID) -> list[str]:
    """
    Loads the outfit asset IDs for all users.

    :return: A list of dictionaries mapping user IDs to their outfit asset IDs.
    """
    all_asset_ids = []
    for user in ROBLOX_USER_IDS:
        current_outfit_url = ROBLOX_LINK_TEMPLATE_CURRENT_OUTFIT.format(user_id=user["user_id"])
        asset_ids = _get_outfit_asset_ids_from_api(current_outfit_url)
        if not asset_ids:
            print(f"[red]Error[/]: No outfit asset IDs found for [blue]{user['username']}[/] ([blue]{user['user_id']}[/]) at {current_outfit_url}")
            continue
        all_asset_ids.append({user["user_id"]: asset_ids})
        progress.update(task, advance=1)

    # flatten `all_asset_ids` and remove duplicates
    unique_asset_ids = set[str]()
    for user_assets_dict in all_asset_ids:
        for asset_id_list in user_assets_dict.values():
            unique_asset_ids.update(asset_id_list)
    unique_asset_ids = list(unique_asset_ids)
    return unique_asset_ids


def _get_outfit_asset_ids_from_api(current_outfit_url: str) -> list[str] | None:
    """
    Fetches the outfit asset IDs from the Roblox API.

    :param api_url: The API URL to fetch the outfit asset IDs from.
    :return: A list of outfit asset IDs if available, otherwise `None`.
    """
    try:
        data = download_url_to_json(current_outfit_url)
        if isinstance(data, dict) and "assetIds" in data and isinstance(data["assetIds"], list):
            return data["assetIds"]
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching outfit asset IDs from {current_outfit_url}: {error}")
        return None


def _calculate_total_downloads(unique_asset_ids: list[str] | None) -> tuple[int, int, int]:
    """
    Calculates the total number of downloads to be performed.

    :return: A `tuple` containing the total number of downloads, the total number of avatar images, and the total number of outfit images.
    """
    total_downloads_roblox_avatars = len(ROBLOX_USER_IDS) * len(ROBLOX_POSES)
    total_downloads_roblox_outfits = len(unique_asset_ids) if unique_asset_ids else 0
    total = total_downloads_roblox_avatars + total_downloads_roblox_outfits
    return total, total_downloads_roblox_avatars, total_downloads_roblox_outfits


def _fetch_username_from_id(user_id: str) -> str | None:
    """
    Helper to fetch a username given a user_id; returns None on failure.

    :param user_id: The Roblox user ID to fetch the username for.
    :return: The username if found, otherwise `None`.
    """
    if not user_id:
        return None
    api_url = "https://users.roblox.com/v1/users"
    body = {"userIds": [user_id], "excludeBannedUsers": True}
    try:
        data = download_url_to_json(api_url, body=body)
        if data and "data" in data and isinstance(data["data"], list) and data["data"]:
            entry = data["data"][0]
            return entry.get("name")  # can change to "displayName" if wanted
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching username for user ID [blue]{user_id}[/]: {error}")
    return None


def _fetch_userid_from_username(username: str) -> str | None:
    """
    Helper to fetch a user_id given a username; returns None on failure.

    :param username: The Roblox username to fetch the user ID for.
    :return: The user ID if found, otherwise `None`.
    """
    if not username:
        return None
    api_url = "https://users.roblox.com/v1/usernames/users"
    body = {"usernames": [username], "excludeBannedUsers": True}
    try:
        data = download_url_to_json(api_url, body=body)
        if data and "data" in data and isinstance(data["data"], list) and data["data"]:
            entry = data["data"][0]
            user_id = entry.get("id") or entry.get("Id") or entry.get("userId")
            if user_id:
                return str(user_id)
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching user ID for username [blue]{username}[/]: {error}")
    return None


def _get_missing_user_names_and_ids(user: dict[str, str]) -> dict[str, str]:
    """
    Fetches missing usernames or user IDs for a Roblox user.

    :param user: A dictionary containing user information, including `username` and/or `user_id`.
    """
    # Ensure username exists (try to fetch from user_id)
    if "username" not in user or not user["username"]:
        username = _fetch_username_from_id(user.get("user_id", ""))
        if username:
            user["username"] = username

    # Ensure user_id exists (try to fetch from username)
    if "user_id" not in user or not user["user_id"]:
        user_id = _fetch_userid_from_username(user.get("username", ""))
        if user_id:
            user["user_id"] = user_id

    return user


def _download_roblox_avatars(progress: Progress, task: TaskID, user: dict[str, str], pose: dict[str, str]) -> None:
    """
    Downloads Roblox avatar images based on the specified parameters.

    :param user: A dictionary containing user information, including `user_id`.
    :param pose: A dictionary containing pose information, including `pose` and `size`.
    """
    api_url = ROBLOX_LINK_TEMPLATE_AVATAR.format(user_id=user["user_id"], pose=pose["pose"], size=pose["size"])
    image_url = _get_image_url_from_roblox_api(api_url)
    if not image_url:
        print(f"[red]Error[/]: Failed to get image URL from API for [blue]{pose["pose"]}[/] image for user [blue]{user['username']}[/] of ID [blue]{user['user_id']}[/] from {image_url}")
        progress.update(task, advance=1)
        return
    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {image_url}")

    image_content = download_url_to_bytes(image_url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download [blue]{pose["pose"]}[/] image for user [blue]{user['username']}[/] (ID [blue]{user['user_id']})[/] from {image_url}")
        progress.update(task, advance=1)
        return

    file_name = f"roblox_{user['user_id']}_{pose['pose']}.png"
    file_path = find_next_available_file_path(ROBLOX_DOWNLOAD_FOLDER, file_name, image_content)
    if file_path:
        save_contents_to_file(file_path, image_content)
    progress.update(task, advance=1)


def _get_image_url_from_roblox_api(api_url: str) -> str | None:
    """
    Fetches the avatar image URL from the Roblox API.

    :param api_url: The API URL to fetch the avatar image from.
    :return: The avatar image URL if available, otherwise `None`.
    """
    try:
        data_json = download_url_to_json(api_url)
        if data_json and "data" in data_json and data_json["data"]:
            entry = data_json["data"][0]
            if entry.get("state") == "Completed" and "imageUrl" in entry:
                return entry["imageUrl"]
            elif entry.get("state") == "Pending":
                if DEBUG_MODE:
                    print(f"[yellow]Warning[/]: Image generation pending for {api_url}")
                time.sleep(5)
                return _get_image_url_from_roblox_api(api_url)
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching {api_url}: {error}")


def _download_roblox_outfits(progress: Progress, task: TaskID, outfit_id: str) -> None:
    """
    Downloads Roblox outfit images based on the specified parameters.

    :param outfit_id: A string containing the outfit ID to download.
    """
    api_url = ROBLOX_LINK_TEMPLATE_OUTFIT.format(outfit_id=outfit_id)
    image_url = _get_image_url_from_roblox_api(api_url)
    if not image_url:
        print(f"[red]Error[/]: Failed to get image URL from API for ID [blue]{outfit_id}[/] from {image_url}")
        progress.update(task, advance=1)
        return
    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {image_url}")

    outfit_type = image_url.split("/")[-3]
    image_content = download_url_to_bytes(image_url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download image for outfit type [blue]{outfit_type}[/] of ID [blue]{outfit_id}[/] from {image_url}")
        progress.update(task, advance=1)
        return

    file_name = f"roblox_outfit_{outfit_type}_{outfit_id}.png"
    folder_path = Path(ROBLOX_DOWNLOAD_FOLDER, "outfits")
    file_path = find_next_available_file_path(folder_path, file_name, image_content)
    if file_path:
        save_contents_to_file(file_path, image_content)
    progress.update(task, advance=1)


if __name__ == "__main__":
    with progress_bar() as progress:
        download_roblox_avatars_and_outfits(progress)
