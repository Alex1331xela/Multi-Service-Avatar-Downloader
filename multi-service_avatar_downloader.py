import sys

sys.dont_write_bytecode = True

from gta_online_avatar_downloader import download_gta_avatars
from mii_downloader import download_mii_avatars
from roblox_avatar_downloader import download_roblox_avatars_and_outfits
from common_downloader_functions import progress_bar
from config import GTA_CHARACTER_NAMES, MIIS_NINTENDO_ACCOUNT, MIIS_NINTENDO_NETWORK_ID, MIIS_MII_STUDIO, ROBLOX_USER_IDS

if __name__ == "__main__":
    with progress_bar() as progress:
        if GTA_CHARACTER_NAMES is not None:
            download_gta_avatars(progress)
        if MIIS_NINTENDO_ACCOUNT + MIIS_MII_STUDIO + MIIS_NINTENDO_NETWORK_ID is not None:
            download_mii_avatars(progress)
        if ROBLOX_USER_IDS is not None:
            download_roblox_avatars_and_outfits(progress)
