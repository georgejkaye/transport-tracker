from typing import Optional


def get_node_id_from_crs_and_platform(crs: str, platform: Optional[str]) -> int:
    """
    Node ids are encoded as 1xxxxxxabccdd where

    xxx: crs of the station encoded as zero-padded two digit numbers
    (a = 01, b = 02 etc)
    a: 0 if there is no platform, 1 if there is a platform
    b: 0 if the platform is a number, 1 if the platform is a letter
    cc: the platform number padded to two digits if a number, the numeric
    encoding of the platform letter if a number (a = 01, b = 02 etc)
    dd: the letter suffix of the platform encoded as a number if one is present,
    00 if there is no suffix
    """
    if platform is None:
        platform_string = "000000"
    else:
        if platform.isnumeric():
            platform_string = f"10{int(platform):02d}00"
        elif platform[0:-1].isnumeric():
            platform_letter = ord(platform[-1]) - 64
            platform_string = f"10{platform[0:-1]}{platform_letter:02d}"
        else:
            platform_string = f"11{ord(platform) - 64}00"
    first_num = ord(crs[0]) - 64
    second_num = ord(crs[1]) - 64
    third_num = ord(crs[2]) - 64
    node_id = int(
        f"1{first_num:02d}{second_num:02d}{third_num:02d}{platform_string}"
    )
    return node_id


def get_crs_and_platform_from_node_id(node_id: int) -> str:
    node_id_str = str(node_id)
    station_crs_str = node_id_str[1:7]
    station_platform_ind = node_id_str[7]
    station_platform_str = node_id_str[8:]
    station_crs_first_char = chr(int(station_crs_str[0:2]) + 64)
    station_crs_second_char = chr(int(station_crs_str[2:4]) + 64)
    station_crs_third_char = chr(int(station_crs_str[4:]) + 64)
    station_crs = f"{station_crs_first_char}{station_crs_second_char}{station_crs_third_char}"
    has_platform = station_platform_ind == "1"
    if not has_platform:
        platform = ""
    else:
        platform = " pl"
        is_platform_number = station_platform_str[0] == "0"
        if is_platform_number:
            platform = f"{platform} {str(int(station_platform_str[1:3]))}"
        else:
            platform = f"{platform} {chr(int(station_platform_str[1:3]) + 64)}"
        platform_suffix_str = station_platform_str[3:]
        if platform_suffix_str != "00":
            platform = f"{platform}{chr(int(platform_suffix_str) + 64)}"
    return f"{station_crs}{platform}"
