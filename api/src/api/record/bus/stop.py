import re
from itertools import product

stop_name_matches = {
    "av": ["avenue", "ave"],
    "ave": ["avenue", "av"],
    "avenue": ["av", "ave"],
    "br": ["bridge"],
    "bridge": ["br"],
    "bus station": ["bus stn"],
    "bus stn": ["bus station"],
    "centre": ["ctr"],
    "ch": ["church"],
    "church": ["ch"],
    "cl": ["close"],
    "close": ["cl"],
    "coll": ["college"],
    "college": ["coll"],
    "court": ["ct"],
    "cres": ["crescent"],
    "crescent": ["cres"],
    "ct": ["court"],
    "ctr": ["centre"],
    "dr": ["drive"],
    "drive": ["dr"],
    "garden": ["gdn"],
    "gardens": ["gdns"],
    "gdn": ["garden"],
    "gdns": ["gardens"],
    "green": ["grn"],
    "grn": ["green"],
    "hosp": ["hospital"],
    "hospital": ["hosp"],
    "ind": ["industrial estate", "ind est"],
    "ind est": ["industrial estate", "ind"],
    "industrial estate": ["ind est", "ind"],
    "int": ["interchange"],
    "interchange": ["int"],
    "jct": ["junction"],
    "junction": ["jct"],
    "lane": ["ln"],
    "ln": ["lane"],
    "market": ["mkt"],
    "mews": ["mws"],
    "mkt": ["market"],
    "mws": ["mews"],
    "parade": ["pde"],
    "park": ["pk"],
    "pde": ["parade"],
    "pk": ["park"],
    "pl": ["place"],
    "place": ["pl"],
    "rbt": ["roundabout"],
    "rd": ["road"],
    "road": ["rd"],
    "roundabout": ["rbt"],
    "sch": ["school"],
    "school": ["sch"],
    "sq": ["square"],
    "square": ["sq"],
    "st": ["street"],
    "station": ["stn"],
    "stn": ["station"],
    "street": ["st"],
    "ter": ["terrace"],
    "terrace": ["ter"],
    "uni": ["university"],
    "university": ["uni"],
    "way": ["wy"],
    "wy": ["way"],
}

_stop_name_pattern = re.compile(
    r"(?<!\w)(?:"
    + "|".join(
        re.escape(component).replace(r"\ ", r"\s+")
        for component in sorted(stop_name_matches, key=len, reverse=True)
    )
    + r")(?!\w)",
)


def get_stop_name_variations(stop_name: str) -> list[str]:
    matches = list(_stop_name_pattern.finditer(stop_name))
    if not matches:
        return [stop_name]

    replacements: list[list[str]] = []
    for match in matches:
        component = match.group()
        key = " ".join(component.split())
        replacements.append([component, *stop_name_matches[key]])
    variations: list[str] = []
    for choices in product(*replacements):
        pieces: list[str] = []
        start = 0
        for match, replacement in zip(matches, choices):
            pieces.extend((stop_name[start : match.start()], replacement))
            start = match.end()
        pieces.append(stop_name[start:])
        variation = "".join(pieces)
        if variation not in variations:
            variations.append(variation)
    return variations
