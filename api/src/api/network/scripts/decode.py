import sys

id = sys.argv[1]
crs = id[1:7]
platform_given = int(id[7])
platform_is_letter = int(id[8])
platform = id[9:11]
platform_suffix = id[11:13]


def decode_letter(number: int) -> str:
    return chr(number + 64)


crs_letter_1 = decode_letter(int(crs[0:2]))
crs_letter_2 = decode_letter(int(crs[2:4]))
crs_letter_3 = decode_letter(int(crs[4:6]))

crs_decoded = f"{crs_letter_1}{crs_letter_2}{crs_letter_3}"

if platform_given == 0:
    platform_string = ""
else:
    if platform_is_letter == 0:
        platform_number_decoded = str(int(platform))
    else:
        platform_number_decoded = decode_letter(int(platform))

    if not platform_suffix == "00":
        platform_suffix_decoded = decode_letter(int(platform_suffix))
    else:
        platform_suffix_decoded = ""

    platform_decoded = f"{platform_number_decoded}{platform_suffix_decoded}"
    platform_string = f": platform {platform_decoded}"

print(f"{crs_decoded}{platform_string}")
