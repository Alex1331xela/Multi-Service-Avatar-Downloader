DEBUG_MODE = False  # Set to True to enable debug mode (prints additional information)

# ===================================================================================================================================================
# =                                             Nintendo Mii Downloader Configuration                                                               =
# ===================================================================================================================================================

MIIS_NINTENDO_ACCOUNT = [
    {
        "name": "Alex",
        "mii_id": "9dfb1b542d57e1e0/6636421f8702af402ac6680542d80cb21ebbc949",
        "mii_code": "3a39407a808f929da5aea9b1b7b8c3d7dcdde4ebf2f9f8fffe01090a12193576798089a4aec4c7dbdde0e7f4f7fdfb",
        "mii_renderer_real": "true",
    },
    {"name": "Olivia", "mii_id": "2d86eca37760e8c3/9c59af4d12ab32c4240b233736b26bc419cb27aa"},
]  # list of Miis from a Nintendo Account with their Mii ID
MIIS_MII_STUDIO = [
    {"name": "AlexProfilePic", "mii_code": "000f1629310a101b2f343f4349535e656e6d747b8289888f8e91999aa2a9a5cad5dce5f802182337414c53606b717f", "mii_renderer_real": "true"}
]  # list of Miis from Mii Studio with their Mii Code
MIIS_NINTENDO_NETWORK_ID = [{"name": "Alex3DS", "nnid": "Alex1331xela", "mii_renderer_real": "true"}]  # list of Miis from Nintendo Network ID with their NNID (username)


MII_DOWNLOAD_FOLDER = r"mii"
MII_SAVE_ROTATING_GIFS = True  # whether to save rotating GIFs of the Miis in each pose/expression combination
MII_SAVE_ROTATING_FRAMES = False  # whether to save the individual side-by-side rotated frames of the Miis in each pose/expression combination


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


LINK_PREFIX_NINTENDO_ACCOUNT = "https://cdn-mii.accounts.nintendo.com/2.0.0/mii_images/{mii_id}.png?width=512"
LINK_PREFIX_MII_STUDIO = "https://studio.mii.nintendo.com/miis/image.png?data={mii_code}&width=512"
LINK_PREFIX_MII_RENDERER_REAL = "https://mii-unsecure.ariankordi.net/miis/image.png?{data_or_nnid}={mii_code_or_nnid}&shaderType={shading}&resourceType=very_high&width=1200"
LINK_SUFFIX_MIIS = "&type={pose}&expression={expression}&bgColor=00000000{frame_count}"
LINK_TEMPLATE_NINTENDO_ACCOUNT = LINK_PREFIX_NINTENDO_ACCOUNT + LINK_SUFFIX_MIIS
LINK_TEMPLATE_MII_STUDIO = LINK_PREFIX_MII_STUDIO + LINK_SUFFIX_MIIS
LINK_TEMPLATE_MII_RENDERER_REAL = LINK_PREFIX_MII_RENDERER_REAL + LINK_SUFFIX_MIIS

# ===================================================================================================================================================
# =                                                   Roblox Avatar Downloader Configuration                                                        =
# ===================================================================================================================================================

ROBLOX_USER_IDS = [
    {"name": "Alex", "username": "Alex1331xela", "user_id": "5111841651"},
    {"name": "Jacob", "username": "TheGreenJacob", "user_id": "1332680547"},
    {"name": "Maddy", "username": "MaddyLoveHeart", "user_id": "5111824731"},
    {"name": "Sammy", "username": "smawoo", "user_id": "872274986"},
    {"name": "Maddy_old", "username": "MaddyLoveHeart_old", "user_id": "7277515456"},
]


ROBLOX_DOWNLOAD_FOLDER = r"roblox"
ROBLOX_SAVE_OUTFIT_IMAGES = True


ROBLOX_POSES = [{"pose": "avatar", "size": "720x720"}, {"pose": "avatar-headshot", "size": "720x720"}, {"pose": "avatar-bust", "size": "420x420"}]


ROBLOX_AVATAR_LINK_TEMPLATE = "https://thumbnails.roblox.com/v1/users/{pose}?userIds={user_id}&size={size}&format=png"
ROBLOX_CURRENT_OUTFIT_TEMPLATE = "https://avatar.roblox.com/v1/users/{user_id}/currently-wearing"
ROBLOX_OUTFIT_LINK_TEMPLATE = "https://thumbnails.roblox.com/v1/assets?assetIds={outfit_id}&size=700x700&format=png"
