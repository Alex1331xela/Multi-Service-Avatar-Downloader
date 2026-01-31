from rich.progress import Progress, SpinnerColumn, TextColumn, MofNCompleteColumn, BarColumn, TaskProgressColumn

from mii_downloader import download_mii_avatars
from roblox_avatar_downloader import download_roblox_avatars_and_outfits
from config import MIIS_NINTENDO_ACCOUNT, MIIS_NINTENDO_NETWORK_ID, MIIS_MII_STUDIO, ROBLOX_USER_IDS

if __name__ == "__main__":
    with Progress(
        SpinnerColumn(finished_text="✔"),
        TextColumn("[progress.description]{task.description}"),
        MofNCompleteColumn(),
        BarColumn(),
        TaskProgressColumn(text_format="[progress.percentage]{task.percentage:.2f} %"),
    ) as progress:
        if MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID is not None:
            download_mii_avatars(progress)
        if ROBLOX_USER_IDS is not None:
            download_roblox_avatars_and_outfits(progress)
