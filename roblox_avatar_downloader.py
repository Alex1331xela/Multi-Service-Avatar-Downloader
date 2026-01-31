import sys

sys.dont_write_bytecode = True

import time
from pathlib import Path

import requests
from rich import print
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, MofNCompleteColumn, BarColumn, TaskProgressColumn


from common_downloader_functions import download_url_to_bytes, download_url_to_json, find_next_available_file_path, save_contents_to_file
from config import ROBLOX_USER_IDS, ROBLOX_POSES, ROBLOX_DOWNLOAD_FOLDER, ROBLOX_SAVE_OUTFIT_IMAGES, ROBLOX_AVATAR_LINK_TEMPLATE, ROBLOX_CURRENT_OUTFIT_TEMPLATE, ROBLOX_OUTFIT_LINK_TEMPLATE


def download_roblox_avatars_and_outfits(progress: Progress) -> None:
    """
    Downloads Roblox avatars and outfits for all users and poses defined in the configuration.
    """
    if ROBLOX_SAVE_OUTFIT_IMAGES:
        task_outfit_loading = progress.add_task("[magenta]Loading Roblox outfit assets...[/]", total=len(ROBLOX_USER_IDS))
        all_asset_ids = load_outfit_asset_ids(progress, task_outfit_loading)
    else:
        all_asset_ids = None

    total_downloads = calculate_total_downloads(all_asset_ids)
    task_downloading_avatars = progress.add_task("[magenta]Downloading Roblox avatars...[/]", total=total_downloads[1])
    if ROBLOX_SAVE_OUTFIT_IMAGES:
        task_downloading_outfits = progress.add_task("[magenta]Downloading Roblox outfits...[/]", total=total_downloads[2])

    for user in ROBLOX_USER_IDS:
        for pose in ROBLOX_POSES:
            download_roblox_avatars(progress, task_downloading_avatars, user, pose)
    if ROBLOX_SAVE_OUTFIT_IMAGES and all_asset_ids:
        download_roblox_outfits(progress, task_downloading_outfits, all_asset_ids)


def load_outfit_asset_ids(progress: Progress, task: TaskID) -> list[str]:
    """
    Loads the outfit asset IDs for all users.

    :return: A list of dictionaries mapping user IDs to their outfit asset IDs.
    """
    all_asset_ids = []
    for user in ROBLOX_USER_IDS:
        current_outfit_url = ROBLOX_CURRENT_OUTFIT_TEMPLATE.format(user_id=user["user_id"])
        asset_ids = get_outfit_asset_ids(current_outfit_url)
        if not asset_ids:
            print(f"[red]Error[/]: No outfit asset IDs found for [purple]{user['username']}[/] ([purple]{user['user_id']}[/]) at {current_outfit_url}")
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


def get_outfit_asset_ids(current_outfit_url: str) -> list[str] | None:
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


def calculate_total_downloads(unique_asset_ids: list[str] | None) -> tuple[int, int, int]:
    """
    Calculates the total number of downloads to be performed.

    :return: A `tuple` containing the total number of downloads, the total number of avatar images, and the total number of outfit images.
    """
    total_downloads_roblox_avatars = len(ROBLOX_USER_IDS) * len(ROBLOX_POSES)
    total_downloads_roblox_outfits = len(unique_asset_ids) if unique_asset_ids else 0
    total = total_downloads_roblox_avatars + total_downloads_roblox_outfits
    return total, total_downloads_roblox_avatars, total_downloads_roblox_outfits


def download_roblox_avatars(progress: Progress, task: TaskID, user: dict[str, str], pose: dict[str, str]) -> None:
    """
    Downloads Roblox avatar images based on the specified parameters.

    :param user: A dictionary containing user information, including `user_id`.
    :param pose: A dictionary containing pose information, including `pose` and `size`.
    """
    api_url = ROBLOX_AVATAR_LINK_TEMPLATE.format(user_id=user["user_id"], pose=pose["pose"], size=pose["size"])
    image_url = get_image_url_from_roblox_api(api_url)
    filename = f"roblox_{user['user_id']}_{pose['pose']}.png"
    if image_url:
        image_content = download_url_to_bytes(image_url)
        if image_content is None:
            print(f"[red]Error[/]: Failed to download [blue]{pose["pose"]}[/] image for user [blue]{user['username']}[/] of ID [blue]{user['user_id']}[/]) from {image_url}")
            progress.update(task, advance=1)
            return
        result = find_next_available_file_path(ROBLOX_DOWNLOAD_FOLDER, filename, image_content, suffix_on_original_file_and_take_its_spot=True)
        if result:
            save_contents_to_file(result, image_content)
        progress.update(task, advance=1)
    else:
        print(f"[red]Error[/]: No URL found for [blue]{pose["pose"]}[/] image for user [blue]{user['username']}[/] of ID [blue]{user['user_id']}[/] from {image_url}")


def get_image_url_from_roblox_api(api_url: str) -> str | None:
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
                print(f"[yellow]Warning[/]: Image generation pending for {api_url}.")
                time.sleep(5)
                return get_image_url_from_roblox_api(api_url)
    except Exception as error:
        print(f"[red]Error[/]: Problem fetching {api_url}: {error}")


def download_roblox_outfits(progress: Progress, task: TaskID, all_asset_ids: list[str]) -> None:
    """
    Downloads Roblox outfit images based on the specified parameters.

    :param user: A dictionary containing user information, including `user_id`.
    """
    for outfit_id in all_asset_ids:
        api_url = ROBLOX_OUTFIT_LINK_TEMPLATE.format(outfit_id=outfit_id)
        image_url = get_image_url_from_roblox_api(api_url)
        folder_path = Path(ROBLOX_DOWNLOAD_FOLDER, "outfits")
        outfit_type = image_url.split("/")[-3] if image_url else "unknown"
        file_name = f"roblox_outfit_{outfit_type}_{outfit_id}.png"
        folder_path.mkdir(parents=True, exist_ok=True)
        if image_url:
            image_content = download_url_to_bytes(image_url)
            if image_content is None:
                print(f"[red]Error[/]: Failed to download image for outfit type [blue]{outfit_type}[/] of ID [blue]{outfit_id}[/] from {image_url}")
                progress.update(task, advance=1)
                return
            result = find_next_available_file_path(folder_path, file_name, image_content, suffix_on_original_file_and_take_its_spot=True)
            if result:
                save_contents_to_file(result, image_content)
            progress.update(task, advance=1)
        else:
            print(f"[red]Error[/]: No URL found for outfit type [blue]{outfit_type}[/] of ID [blue]{outfit_id}[/] from {image_url}")


if __name__ == "__main__":
    with Progress(
        SpinnerColumn(finished_text="✔"),
        TextColumn("[progress.description]{task.description}"),
        MofNCompleteColumn(),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:.2f} %"),
    ) as progress:
        download_roblox_avatars_and_outfits(progress)
