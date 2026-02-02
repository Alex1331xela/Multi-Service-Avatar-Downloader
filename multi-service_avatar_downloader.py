import sys

sys.dont_write_bytecode = True

from modules.gta_online_avatar_downloader import download_gta_avatars
from modules.mii_downloader import download_mii_avatars
from modules.roblox_avatar_downloader import download_roblox_avatars_and_outfits
from modules.common_downloader_functions import create_config_file_if_only_default, progress_bar

try:
    from config import GTA_CHARACTER_NAMES, MIIS, ROBLOX_USER_IDS
except ImportError:
    from config_default import GTA_CHARACTER_NAMES, MIIS, ROBLOX_USER_IDS

if __name__ == "__main__":
    create_config_file_if_only_default()
    with progress_bar() as progress:
        if GTA_CHARACTER_NAMES is not None:
            download_gta_avatars(progress)
        if MIIS is not None:
            download_mii_avatars(progress)
        if ROBLOX_USER_IDS is not None:
            download_roblox_avatars_and_outfits(progress)
