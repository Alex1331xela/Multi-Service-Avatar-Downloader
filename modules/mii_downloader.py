import sys

sys.dont_write_bytecode = True

from pathlib import Path
from rich import print
from rich.progress import Progress, TaskID

from modules.common_downloader_functions import create_config_file_if_only_default, progress_bar, download_url_to_bytes, render_gif_from_frames, find_next_available_file_path, save_contents_to_file

try:
    from config import DEBUG_MODE, MIIS, MII_DOWNLOAD_FOLDER, MII_SAVE_HD_IMAGES, MII_SAVE_ROTATING_GIFS, MII_SAVE_ROTATING_FRAMES
except ImportError:
    from config_default import DEBUG_MODE, MIIS, MII_DOWNLOAD_FOLDER, MII_SAVE_HD_IMAGES, MII_SAVE_ROTATING_GIFS, MII_SAVE_ROTATING_FRAMES

MII_POSES = ["face", "face_only", "all_body"]  # list of all rendered poses to download
MII_EXPRESSIONS = [
    "normal",
    "smile",
    "anger",
    "sorrow",
    "surprise",
    "blink",
    "normal_open_mouth",
    "smile_open_mouth",
    "anger_open_mouth",
    "sorrow_open_mouth",
    "surprise_open_mouth",
    "blink_open_mouth",
    "wink_left",
    "wink_right",
    "wink_left_open_mouth",
    "wink_right_open_mouth",
    "like_wink_left",
    "like_wink_right",
    "frustrated",
]  # list of all rendered expressions to download
MII_SHADINGS = ["miitomo", "switch", "wiiu"]  # list of shading types for NNID Miis

MII_LINK_PREFIX_NINTENDO_ACCOUNT = "https://cdn-mii.accounts.nintendo.com/2.0.0/mii_images/{mii_id}.png?width=512"
MII_LINK_PREFIX_MII_STUDIO = "https://studio.mii.nintendo.com/miis/image.png?data={mii_code}&width=512"
MII_LINK_PREFIX_MII_RENDERER_REAL = "https://mii-unsecure.ariankordi.net/miis/image.png?{data_or_nnid}={mii_code_or_nnid}&shaderType={shading}&resourceType=very_high&width=1200"
MII_LINK_SUFFIX_MIIS = "&type={pose}&expression={expression}&bgColor=00000000{frame_count}"
MII_LINK_TEMPLATE_NINTENDO_ACCOUNT = MII_LINK_PREFIX_NINTENDO_ACCOUNT + MII_LINK_SUFFIX_MIIS
MII_LINK_TEMPLATE_MII_STUDIO = MII_LINK_PREFIX_MII_STUDIO + MII_LINK_SUFFIX_MIIS
MII_LINK_TEMPLATE_MII_RENDERER_REAL = MII_LINK_PREFIX_MII_RENDERER_REAL + MII_LINK_SUFFIX_MIIS


def download_mii_avatars(progress: Progress) -> None:
    """
    Downloads Mii images based on the specified parameters.
    """
    total_downloads = _calculate_total_downloads()
    task = progress.add_task("[magenta]Downloading Mii avatars...[/]", total=total_downloads)

    for mii in MIIS:
        if not (("mii_id" in mii or "mii_code" in mii) or (MII_SAVE_HD_IMAGES and ("mii_code" in mii or "nnid" in mii))):
            continue  # skip Miis that are improperly formatted / missing the necessary info to download
        for pose in MII_POSES:
            for expression in MII_EXPRESSIONS:
                _seperate_downloading_sd_vs_hd(progress, task, mii, pose, expression)


def _calculate_total_downloads() -> int:
    """
    Calculates the total number of downloads to be performed.

    :return: The total number of downloads.
    """
    total_downloads_nintendo_servers = len(MII_POSES) * len(MII_EXPRESSIONS) * len([mii for mii in MIIS if ("mii_id" in mii or "mii_code" in mii)])
    total_downloads_mii_renderer_real = (len(MII_POSES) * len(MII_EXPRESSIONS) * len(MII_SHADINGS) * len([mii for mii in MIIS if ("mii_code" in mii or "nnid" in mii)])) if MII_SAVE_HD_IMAGES else 0
    total = total_downloads_nintendo_servers + total_downloads_mii_renderer_real
    if MII_SAVE_ROTATING_FRAMES:
        total *= 2
    if MII_SAVE_ROTATING_GIFS:
        total *= 2
    return total


def _seperate_downloading_sd_vs_hd(progress: Progress, task: TaskID, mii: dict[str, str], pose: str, expression: str) -> None:
    """
    Seperates the downloading of a single mii for a given pose/expression between downloading the default image from Nintendo servers and,
    if configured, 3rd party HD shaded variants.

    :param mii: A dictionary containing Mii information.
    :param pose: The pose of the Mii.
    :param expression: The expression of the Mii.
    """
    if "mii_id" in mii or "mii_code" in mii:
        _process_individual_image(progress, task, mii, pose, expression)  # download the SD image if mii has an id or code

    if MII_SAVE_HD_IMAGES and ("mii_code" in mii or "nnid" in mii):
        for shading in MII_SHADINGS:
            _process_individual_image(progress, task, mii, pose, expression, shading=shading)  # download the HD image if mii has a code or nnid


def _process_individual_image(progress: Progress, task: TaskID, mii: dict[str, str], pose: str, expression: str, shading: str = "", frames: int = 1) -> None:
    """
    Handles downloading and saving a single Mii image.

    :param mii: A dictionary containing Mii information.
    :param pose: The pose of the Mii.
    :param expression: The expression of the Mii.
    :param shading: The shading type of the Mii.
    :param frames: The frame count of the Mii.
    """
    url = _generate_url(mii, pose, expression, frames, shading)
    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {url}")

    image_content = download_url_to_bytes(url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download image for [blue]{pose} {expression}[/] for [blue]{mii["mii_name"]}[/] from {url}")
        progress.update(task, advance=1)
        return

    if MII_SAVE_ROTATING_FRAMES or frames == 1:
        file_name = _generate_filename(mii, pose, expression, shading, "png")
        output_dir = Path(MII_DOWNLOAD_FOLDER) / mii["mii_name"]
        output_dir = output_dir / (str(frames) + " frames") if frames != 1 else output_dir
        file_path = find_next_available_file_path(output_dir, file_name, image_content)
        if file_path:
            save_contents_to_file(file_path, image_content)
        progress.update(task, advance=1)

    if MII_SAVE_ROTATING_GIFS and frames != 1:
        file_name = _generate_filename(mii, pose, expression, shading, "gif")
        output_dir = Path(MII_DOWNLOAD_FOLDER) / mii["mii_name"]
        gif_bytes = render_gif_from_frames(image_content, frames)
        file_path = find_next_available_file_path(output_dir, file_name, gif_bytes)
        if file_path:
            save_contents_to_file(file_path, gif_bytes)
        progress.update(task, advance=1)

    if (MII_SAVE_ROTATING_GIFS or MII_SAVE_ROTATING_FRAMES) and frames == 1:
        _process_individual_image(progress, task, mii, pose, expression, shading, frames=16)


def _generate_url(mii: dict[str, str], pose: str, expression: str, frames: int, shading: str) -> str:
    """
    Generates the download URL for a Mii image.

    :param mii: A dictionary containing Mii information.
    :param pose: The pose of the Mii.
    :param expression: The expression of the Mii.
    :param frames: The frame count of the Mii.
    :param shading: The shading type of the Mii.
    :return: The generated download URL.
    """
    frames_str = f"&instanceCount={str(frames)}" if frames != 1 else ""
    if shading != "":
        if "mii_code" in mii:
            data_or_nnid = "data"
            mii_code_or_nnid = mii["mii_code"]
        elif "nnid" in mii:
            data_or_nnid = "nnid"
            mii_code_or_nnid = mii["nnid"]
        to_return = MII_LINK_TEMPLATE_MII_RENDERER_REAL.format(data_or_nnid=data_or_nnid, mii_code_or_nnid=mii_code_or_nnid, expression=expression, pose=pose, frame_count=frames_str, shading=shading)
        max_width = (16384 - 1) // frames  # Ensure width * frames < 16384
        width = min(1200, max_width)  # use the calculated max_width if less than 1200
        return to_return.replace("width=1200", f"width={width}")
    elif "mii_id" in mii:
        return MII_LINK_TEMPLATE_NINTENDO_ACCOUNT.format(mii_id=mii["mii_id"], expression=expression, pose=pose, frame_count=frames_str)
    elif "mii_code" in mii:
        return MII_LINK_TEMPLATE_MII_STUDIO.format(mii_code=mii["mii_code"], expression=expression, pose=pose, frame_count=frames_str)
    return ""


def _generate_filename(mii: dict[str, str], pose: str, expression: str, shading: str, extension: str) -> str:
    """
    Generates the filename for a Mii image.

    :param mii: A dictionary containing Mii information.
    :param pose: The pose of the Mii.
    :param expression: The expression of the Mii.
    :param frames: The frame count of the Mii.
    :param shading: The shading type of the Mii.
    :param extension: The file extension.
    :return: The generated filename.
    """
    if shading != "":
        shading = f"_{shading}"
    else:
        shading = ""
    return f"Mii_{mii['mii_name']}_{pose.replace('_', '-')}_{expression.replace('_', '-')}{shading}.{extension}"


if __name__ == "__main__":
    create_config_file_if_only_default()
    with progress_bar() as progress:
        download_mii_avatars(progress)
