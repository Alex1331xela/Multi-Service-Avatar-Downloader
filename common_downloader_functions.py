import os
import time
import hashlib
from pathlib import Path

from collections.abc import Sequence
import io
from PIL import Image
import requests
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, MofNCompleteColumn, BarColumn, TaskProgressColumn

try:
    from config import DEBUG_MODE
except ImportError:
    from config_default import DEBUG_MODE


def progress_bar() -> Progress:
    """
    Returns a `Progress` class with customized arguments for use in a progress bar.

    :return: A `Progress` class with customized arguments.
    """
    return Progress(
        SpinnerColumn(finished_text="✔"),
        TextColumn("[progress.description]{task.description}"),
        MofNCompleteColumn(),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:.2f} %"),
    )


def download_url_to_raw(url: str, body: dict | None = None) -> requests.Response | None:
    """
    Downloads from the given `URL` and returns the response object. Handles HTTP errors for access denial and rate limiting.

    :param url: The URL to download.
    :param body: An optional dictionary to send as a JSON body with the request.
    :return: The content in bytes as a requests.Response object, or `None` if access is denied (HTTP 403), if rate limited and retry fails (HTTP 429), or for other unhandled HTTP errors.
    """
    max_retries = 5
    retries = 0
    while retries <= max_retries:
        response = requests.get(url, json=body, timeout=10)
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as http_error:
            if response.status_code == 403:
                if DEBUG_MODE:
                    print(f"[red]Error[/]: Access denied for {url}.")
                return None
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        wait_seconds = int(retry_after)
                    except ValueError:
                        wait_seconds = 10
                else:
                    wait_seconds = 10
                if DEBUG_MODE:
                    print(f"[yellow]Warning[/]: 429 Too Many Requests for {url}. Pausing for {wait_seconds} seconds before retry... (Attempt {retries+1}/{max_retries})")
                time.sleep(wait_seconds)
                retries += 1
                continue
            else:
                raise http_error
    if DEBUG_MODE:
        print(f"[red]Error[/]: Exceeded maximum retries for {url}.")
    return None


def download_url_to_bytes(url: str, body: dict | None = None) -> bytes | None:
    """
    Downloads from the given `URL` and returns its content as bytes. Handles HTTP errors for access denial and rate limiting.

    :param url: The URL to download.
    :param body: An optional dictionary to send as a JSON body with the request.
    :return: The content in bytes. Returns `None` if access is denied (HTTP 403).
    """
    response = download_url_to_raw(url, body=body)
    return response.content if response else None


def download_url_to_json(url: str, body: dict | None = None) -> dict | None:
    """
    Downloads from the given `URL` and returns its content as JSON. Handles HTTP errors for access denial and rate limiting.

    :param url: The URL to download.
    :param body: An optional dictionary to send as a JSON body with the request.
    :return: The content in JSON format. Returns `None` if access is denied (HTTP 403).
    """
    response = download_url_to_raw(url, body=body)
    return response.json() if response else None


def render_gif_from_frames(image_to_split: str | Path | bytes, frame_count: int) -> bytes:
    """
    Renders a GIF from a single image that contains multiple side-by-side images.

    :param image_to_split: The side-by-side image to split, as a path or in bytes.
    :param frame_count: The number of frames in the image.
    """
    frames = split_image_into_frames(image_to_split, frame_count)
    gif_bytes = images_to_gif(frames)
    return gif_bytes


def split_image_into_frames(image_to_split: str | Path | bytes, frame_count: int) -> list[bytes]:
    """
    Splits a single image that contains multiple side-by-side images into individual frames.

    :param image_to_split: The side-by-side image to split, as a path or in bytes.
    :param frame_count: The number of frames in the image.
    """
    if isinstance(image_to_split, (str, Path)):  # Load string or Path object into bytes
        image_to_split = Path(image_to_split)
        image_to_split = image_to_split.read_bytes()

    with Image.open(io.BytesIO(image_to_split)) as img:
        width, height = img.size
        image_mode = ""
        if width > height:
            image_mode = "horizontal"
            frame_cutoff = width // frame_count
        else:
            image_mode = "vertical"
            frame_cutoff = height // frame_count

        frames = []
        for index in range(frame_count):
            left = index * frame_cutoff
            right = left + frame_cutoff
            if image_mode == "horizontal":
                frame = img.crop((left, 0, right, height))
            else:
                frame = img.crop((0, left, width, right))
            byte_io = io.BytesIO()
            frame.save(byte_io, format="PNG")
            frames.append(byte_io.getvalue())
        return frames


def images_to_gif(images_bytes_list: Sequence[str | Path | bytes]) -> bytes:
    """
    Converts a list of images to a GIF.

    :param images_bytes_list: A list of images, as paths or in bytes.
    """
    frames: list[Image.Image] = []
    for image in images_bytes_list:
        if isinstance(image, (str, Path)):  # Load string or Path object into bytes
            image = Path(image)
            image = image.read_bytes()
        frames.append(Image.open(io.BytesIO(image)))
    byte_io = io.BytesIO()
    frames[0].save(byte_io, format="GIF", save_all=True, append_images=frames[1:], duration=100, loop=0, disposal=2)
    return byte_io.getvalue()


def file_hash(file: str | Path | bytes) -> str:
    """
    Calculates the `MD5` hash of a file or raw bytes.

    :param file: The path to the file or bytes content.
    :return: The `MD5` hash as a hexadecimal string.
    """
    if isinstance(file, (bytes, bytearray)):
        return hashlib.md5(file).hexdigest()

    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hashlib.md5().update(chunk)
    return hashlib.md5().hexdigest()


def is_identical_file(file_1: str | Path | bytes, file_2: str | Path | bytes, size_only: bool = False) -> bool:
    """
    Checks if two files are identical.

    :param file_1: The first file path or content in bytes.
    :param file_2: The second file path or content in bytes.
    :param size_only: If `True`, only compare file sizes. If `False`, compare file hashes.
    :return: `True` if the files are identical based on the specified comparison method, `False` otherwise
    """
    if (isinstance(file_1, (str, Path)) and not os.path.exists(file_1)) or (isinstance(file_2, (str, Path)) and not os.path.exists(file_2)):
        return False

    if isinstance(file_1, (str, Path)):
        file_1_size = os.path.getsize(file_1)
        file_1_hash = file_hash(file_1)
    else:
        file_1_size = len(file_1)
        file_1_hash = hashlib.md5(file_1).hexdigest()

    if isinstance(file_2, (str, Path)):
        file_2_size = os.path.getsize(file_2)
        file_2_hash = file_hash(file_2)
    else:
        file_2_size = len(file_2)
        file_2_hash = hashlib.md5(file_2).hexdigest()

    if size_only:
        return file_1_size == file_2_size
    else:
        return file_1_hash == file_2_hash


def identical_or_same_size_file(file_1: str | Path | bytes, file_2: str | Path | bytes) -> bool:
    """
    Checks if one file is either identical to another or has the same size.

    :param file_1: The first file path or content in bytes.
    :param file_2: The second file path or content in bytes.
    :return: `True` if the file is identical or has the same size, `False` otherwise.
    """
    if is_identical_file(file_1, file_2, size_only=True):
        if is_identical_file(file_1, file_2):
            if DEBUG_MODE:
                print(f"Skipped ([green]identical[/]): {file_1}")
            return True
        else:
            if DEBUG_MODE:
                print(f"Skipped ([yellow]different[/]): {file_1}")
            return True
    return False


def find_next_available_file_path(folder_path: str | Path, file_name: str, file_content: bytes, suffix_on_original_file_and_take_its_spot: bool = False) -> Path | None:
    """
    Finds an available file path, avoiding overwriting identical files.

    :param folder_path: The folder where the file will be saved.
    :param file_name: The desired file name with extension.
    :param file_content: The content of the file in bytes.
    :param suffix_on_original_file_and_take_its_spot: If `True`, renames the existing file and takes its spot. If `False`, finds a new available name.
    :return: The available file path as a Path object, or `None` if an identical file already exists.
    """

    if isinstance(folder_path, str):  # Convert string path to Path object
        folder_path = Path(folder_path)
    file_path = folder_path / file_name

    os.makedirs(folder_path, exist_ok=True)
    if not file_path.exists():
        return file_path
    if identical_or_same_size_file(file_path, file_content):
        return None

    file_name_base, file_name_extension = os.path.splitext(file_name)
    suffix = 2
    while True:
        new_file_name = f"{file_name_base}_{suffix}{file_name_extension}"
        new_file_path = folder_path / new_file_name
        if not new_file_path.exists():
            if not suffix_on_original_file_and_take_its_spot:
                return new_file_path
            else:
                os.rename(file_path, new_file_path)
                return file_path
        if identical_or_same_size_file(new_file_path, file_content):
            return None
        suffix += 1


def save_contents_to_file(file_path: str | Path, file_content: bytes, overwrite: bool = False) -> None:
    """
    Saves the downloaded file content to the specified file path.

    :param file_path: The path where the file will be saved.
    :param file_content: The content of the file in bytes.
    :param overwrite: If `True`, overwrite the file if it already exists. If `False`, do not overwrite existing files.
    """
    if isinstance(file_path, str):  # Convert string path to Path object
        file_path = Path(file_path)

    if file_path.exists() and not overwrite:
        print(f"[red]Error[/]: File already exists and overwrite is not allowed: {file_path}")
        return

    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file_content)
    print(f"[green]Downloaded[/]: {file_path}")


def console_pause() -> None:
    """
    Pauses the console until the user presses any key.
    """
    if os.name == "nt":  # Windows
        import msvcrt

        print("Press any key to exit...")
        msvcrt.getch()
    else:  # Unix-based systems (Linux, macOS)
        import termios
        import sys

        print("Press any key to exit...")
        sys.stdout.flush()

        # Configure terminal to capture a single keypress without displaying it
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        new_settings = termios.tcgetattr(fd)
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)

        try:
            # Wait for a single keypress to exit
            os.read(fd, 1)
        finally:
            # Restore original terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
