from pathlib import Path


DEBUG_MODE: bool = False  # boolean, set to `True` to enable debug mode (prints additional information)

# ===================================================================================================================================================
# =                                                  Grand Theft Auto Online Avatar Downloader Configuration                                        =
# ===================================================================================================================================================

GTA_CHARACTER_NAMES: list[str] = ["Alex1331xela"]  # list of strings, each string a GTA Online character name

GTA_DOWNLOAD_FOLDER: str | Path = Path.home() / "Pictures" / "gta_online"  # string or path object, path to the folder to save downloaded GTA Online avatars to

# ===================================================================================================================================================
# =                                                  Nintendo Mii Avatar Downloader Configuration                                                   =
# ===================================================================================================================================================

MIIS: list[dict[str, str]] = [
    {
        "mii_name": "Alex",
        "mii_id": "9dfb1b542d57e1e0/6636421f8702af402ac6680542d80cb21ebbc949",
        "mii_code": "3a39407a808f929da5aea9b1b7b8c3d7dcdde4ebf2f9f8fffe01090a12193576798089a4aec4c7dbdde0e7f4f7fdfb",
    }
]  # list of dictionaries, each dictionary containing information on a Mii. Accepts a `mii_name` (for folder and file naming), as well as at least one of the following: a `mii_id` and/or a `mii_code` and/or a `nnid` username

MII_SAVE_HD_IMAGES: bool = False  # boolean, whether to save high quality renders of the Miis in each pose/expression/shading combination from the 3rd party site "Mii Renderer (Real)"
MII_SAVE_ROTATING_GIFS: bool = False  # boolean, whether to save rotating GIFs of the Miis in each pose/expression/shading combination
MII_SAVE_ROTATING_FRAMES: bool = False  # boolean, whether to save the individual side-by-side rotated frames of the Miis in each pose/expression/shading combination

MII_DOWNLOAD_FOLDER: str | Path = Path.home() / "Pictures" / "mii"  # string or path object, path to the folder to save downloaded Mii avatars to

# ===================================================================================================================================================
# =                                                  Roblox Avatar Downloader Configuration                                                         =
# ===================================================================================================================================================

ROBLOX_USER_IDS: list[dict[str, str]] = [
    {"username": "Alex1331xela", "user_id": "5111841651"}
]  # list of dictionaries, each dictionary containing information on a Roblox user. Accepts a `username` and/or a `user_id`. If both are provided, `user_id` will be used for downloading, and `username` for file naming.

ROBLOX_SAVE_OUTFIT_IMAGES: bool = False  # boolean, whether to save Roblox outfit images

ROBLOX_DOWNLOAD_FOLDER: str | Path = Path.home() / "Pictures" / "roblox"  # string or path object, path to the folder to save downloaded Roblox avatars and outfits to
