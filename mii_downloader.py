import sys

sys.dont_write_bytecode = True

from pathlib import Path

from rich import print
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, MofNCompleteColumn, BarColumn, TaskProgressColumn

from common_downloader_functions import download_url_to_bytes, render_gif_from_frames, find_next_available_file_path, save_contents_to_file
from config import (
    DEBUG_MODE,
    MIIS_NINTENDO_ACCOUNT,
    MIIS_MII_STUDIO,
    MIIS_NINTENDO_NETWORK_ID,
    MII_DOWNLOAD_FOLDER,
    MII_SAVE_HD_IMAGES,
    MII_SAVE_ROTATING_GIFS,
    MII_SAVE_ROTATING_FRAMES,
    MII_POSES,
    MII_EXPRESSIONS,
    MII_SHADINGS,
    LINK_TEMPLATE_NINTENDO_ACCOUNT,
    LINK_TEMPLATE_MII_STUDIO,
    LINK_TEMPLATE_MII_RENDERER_REAL,
)


def download_mii_avatars(progress: Progress) -> None:
    """
    Downloads Mii images based on the specified parameters.
    """
    total_downloads = calculate_total_downloads()
    task = progress.add_task("[magenta]Downloading Mii avatars...[/]", total=total_downloads)

    for pose in MII_POSES:
        for expression in MII_EXPRESSIONS:
            for mii in (mii for mii in MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID if "mii_id" in mii or "mii_code" in mii):
                process_image(progress, task, mii, pose, expression)
            for mii in (mii for mii in MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID if MII_SAVE_HD_IMAGES and "mii_renderer_real" in mii):
                for shading in MII_SHADINGS:
                    process_image(progress, task, mii, pose, expression, shading=shading)


def calculate_total_downloads() -> int:
    """
    Calculates the total number of downloads to be performed.

    :return: The total number of downloads.
    """
    total_downloads_nintendo_servers = (
        len(MII_POSES) * len(MII_EXPRESSIONS) * len([mii for mii in MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID if "mii_id" in mii or "mii_code" in mii])
    )
    total_downloads_mii_renderer_real = (
        (len(MII_POSES) * len(MII_EXPRESSIONS) * len(MII_SHADINGS) * len([mii for mii in MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID if "mii_renderer_real" in mii]))
        if MII_SAVE_HD_IMAGES
        else 0
    )
    total = total_downloads_nintendo_servers + total_downloads_mii_renderer_real
    if MII_SAVE_ROTATING_FRAMES:
        total *= 2
    if MII_SAVE_ROTATING_GIFS:
        total *= 2
    return total


def process_image(progress: Progress, task: TaskID, mii: dict[str, str], pose: str, expression: str, shading: str = "", frames: int = 1) -> None:
    """
    Handles downloading and saving a single Mii image.

    :param mii: A dictionary containing Mii information.
    :param pose: The pose of the Mii.
    :param expression: The expression of the Mii.
    :param shading: The shading type of the Mii.
    :param frames: The frame count of the Mii.
    """
    url = generate_url(mii, pose, expression, frames, shading)
    if DEBUG_MODE:
        print(f"[blue]Loading[/]: {url}")

    image_content = download_url_to_bytes(url)
    if image_content is None:
        print(f"[red]Error[/]: Failed to download image for [blue]{pose} {expression}[/] for [blue]{mii["name"]}[/] from {url}")
        return

    if MII_SAVE_ROTATING_FRAMES or frames == 1:
        file_name = generate_filename(mii, pose, expression, shading, "png")
        output_dir = Path(MII_DOWNLOAD_FOLDER) / mii["name"]
        output_dir = output_dir / (str(frames) + " frames") if frames != 1 else output_dir
        file_path = find_next_available_file_path(output_dir, file_name, image_content)
        if file_path:
            save_contents_to_file(file_path, image_content)
        progress.update(task, advance=1)

    if MII_SAVE_ROTATING_GIFS and frames != 1:
        file_name = generate_filename(mii, pose, expression, shading, "gif")
        output_dir = Path(MII_DOWNLOAD_FOLDER) / mii["name"]
        gif_bytes = render_gif_from_frames(image_content, frames)
        file_path = find_next_available_file_path(output_dir, file_name, gif_bytes)
        if file_path:
            save_contents_to_file(file_path, gif_bytes)
        progress.update(task, advance=1)

    if (MII_SAVE_ROTATING_GIFS or MII_SAVE_ROTATING_FRAMES) and frames == 1:
        process_image(progress, task, mii, pose, expression, shading, frames=16)


def generate_url(mii: dict[str, str], pose: str, expression: str, frames: int, shading: str) -> str:
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
        to_return = LINK_TEMPLATE_MII_RENDERER_REAL.format(data_or_nnid=data_or_nnid, mii_code_or_nnid=mii_code_or_nnid, expression=expression, pose=pose, frame_count=frames_str, shading=shading)
        max_width = (16384 - 1) // frames  # Ensure width * frames < 16384
        width = min(1200, max_width)  # use the calculated max_width if less than 1200
        return to_return.replace("width=1200", f"width={width}")
    elif "mii_id" in mii:
        return LINK_TEMPLATE_NINTENDO_ACCOUNT.format(mii_id=mii["mii_id"], expression=expression, pose=pose, frame_count=frames_str)
    elif "mii_code" in mii:
        return LINK_TEMPLATE_MII_STUDIO.format(mii_code=mii["mii_code"], expression=expression, pose=pose, frame_count=frames_str)
    return ""


def generate_filename(mii: dict[str, str], pose: str, expression: str, shading: str, extension: str) -> str:
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
    return f"Mii_{mii['name']}_{pose.replace('_', '-')}_{expression.replace('_', '-')}{shading}.{extension}"


if __name__ == "__main__":
    with Progress(
        SpinnerColumn(finished_text="✔"),
        TextColumn("[progress.description]{task.description}"),
        MofNCompleteColumn(),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:.2f} %"),
    ) as progress:
        download_mii_avatars(progress)
