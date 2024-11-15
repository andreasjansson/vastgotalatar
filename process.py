# TODO:
# Group items by socken


import random
import math
import datetime
import json
import pandas as pd
import geopandas as gpd
import pickle
import os
import geopy
from geopy.point import Point
from geopy.location import Location
from geopy.distance import geodesic
from geopy.exc import GeocoderQueryError


CACHE = {}

gmaps = geopy.GoogleV3(os.environ["GMAPS_API_KEY"])


def cell_to_str(fmt):
    def wrapped(x):
        if pd.notnull(x) and isinstance(x, (pd.Timestamp, datetime.datetime)):
            return x.strftime(fmt)
        if pd.notnull(x) and isinstance(x, datetime.time):
            return x.hour * 3600 + x.minute * 60 + x.second
        return x

    return wrapped


def location_to_coord(loc: Location) -> tuple[float, float]:
    return (loc.latitude, loc.longitude)


def get_filter(row):
    return {
        "song_type": get_song_type_filter(row),
        "instrument": get_instrument_filter(row),
        "collector": get_collector_filter(row),
    }


def get_collector_filter(row):
    collector = row["Inspelat/ inlämnat av"]
    if not collector:
        return ""

    collector = collector.strip()

    if collector == "Josefsson, Arnold, Djupedal, Vara":
        return "Josefsson, Arnold, Vara"
    if collector == "Nordström, Annika (Olsson, Elsa, ev.)":
        return "Nordström, Annika"
    if collector == "Lätt, Billy, Korsberga, Hjo":
        return "Lätt, Billy, Hjo"
    if "Adin, Björn" in collector:
        return "Adin, Björn"
    return collector


def get_song_type_filter(row):
    song_type = row["Låttyp eller visgenre"]
    if not song_type or not song_type.strip():
        return {
            "main": "",
            "secondary": [],
        }
    song_type = song_type.lower()

    parts = [normalize_string(p).capitalize() for p in song_type.split(",")]
    return {
        "main": parts[0],
        "secondary": parts[1:],
    }


def normalize_instrument(s):
    if s == "m.m" or s == "-":
        return ""

    s = s.replace("fioler", "fiol").replace("fiol 1", "fiol").replace("fiol 2", "fiol")
    s = s.replace(
        "liktonigt knappdragspel med svarta och vita tangenter vilket innebär att det egentligen inte är ett durspel",
        "dragspel",
    )
    s = s.replace(" m.m", "")

    if "cittra" in s or "zittra" in s:
        return "cittra"

    s = (
        s.replace("1-", "en")
        .replace("1", "en")
        .replace("2-", "två")
        .replace("2", "två")
        .replace("3-", "tre")
        .replace("3", "tre")
        .replace("4-", "fyr")
        .replace("4", "fyr")
        .replace("5-", "fem")
        .replace("5", "fem")
    )

    return s


def normalize_string(s):
    return s.lower().split("(")[0].strip(" ?.,")


def get_instrument_filter(row):
    instrument = row["Sång  instrument"]
    if not instrument or not instrument.strip():
        return []

    parts = [
        normalize_instrument(normalize_string(p)).capitalize()
        for p in instrument.split(",")
    ]
    parts = [p for p in parts if p]

    return parts


def create_hitta_data():
    df = pd.read_excel("hitta-folkmusiken.xls", parse_dates=False)
    for year_column in [
        "Inspelat år",
        "Inspelat år.1",
        "Född år",
        "Inspelat/nedtecknat år",
        "Tid på inspelningen",
    ]:
        df[year_column] = df[year_column].apply(cell_to_str("%Y"))
    hitta = df.to_dict("records")

    for row in hitta:
        for k, v in row.items():
            if isinstance(v, float) and math.isnan(v):
                row[k] = None

        locations = get_locations(row["Proveniens"], row["Landskap"])
        coords = [location_to_coord(loc) for loc in locations]
        row["coords"] = coords

        row["filter"] = get_filter(row)

    grouped = {}
    for row in hitta:
        prov = row["Proveniens"]
        if not prov:
            continue
        ls = row.get("Landskap", "")
        key = f"{prov} | {ls}"
        if key not in grouped:
            # randomly move coords a little bit
            coords = [
                (c[0] + random.uniform(-0.01, 0.01), c[1] + random.uniform(-0.01, 0.01))
                for c in row["coords"]
            ]
            grouped[key] = {"coords": coords, "rows": []}

        grouped[key]["rows"].append(row)

    with open("vastgotalatar/public/hitta.json", "w") as f:
        json.dump(grouped, f, ensure_ascii=False)


def cleanup_proveniens(p):
    for s in [
        "textbok",
        "lösblad",
        "CD, Joakim Wannberg",
        "CD Margareta Johansson",
        "CD avspelade kassetter kassetter",
        "CD avspelade kassetter",
        "CD",
        "m.m.",
        "VHS",
    ]:
        p = p.replace(", " + s, "")
    return p


def cleanup_landskap(ls):
    return (
        ls.strip()
        .replace("dalsland", "Dalsland")
        .replace("Dalsland/Västergötland", "Västra Götaland")
        .replace("Västgergötland", "Västergötland")
    )


def split(s):
    return [p.strip() for p in s.split(",")]


def cleanup_parens_parts(parts):
    if "(" not in ", ".join(parts):
        return parts

    clean_parts = []
    cur_part = []
    for part in parts:
        cur_part.append(part)
        if ")" in part:
            clean_parts.append(", ".join(cur_part).split("(")[0].strip(" ,"))
            cur_part = []

    if cur_part:
        clean_parts.append(", ".join(cur_part))

    return clean_parts


def get_locations(proveniens, landskap) -> list[Location]:
    if not isinstance(proveniens, str) or not proveniens.strip():
        return []

    prov_parts = cleanup_parens_parts(split(cleanup_proveniens(proveniens)))
    if not isinstance(landskap, str) or not landskap.strip():
        landskap = ""

    if not prov_parts:
        return []

    ls_parts = split(cleanup_landskap(landskap))

    if len(prov_parts) == 1:
        loc = geocode(prov_parts[0], ls_parts[0])
        if loc:
            return [loc]
        else:
            return []

    if len(prov_parts) == len(ls_parts):
        ret = []
        for prov, ls in zip(prov_parts, ls_parts):
            loc = geocode(prov, ls)
            if loc:
                ret.append(loc)
        return ret

    if len(ls_parts) > 1:
        return get_locations(proveniens, None)

    ls = ls_parts[0]

    if len(prov_parts) >= 4:
        ret = []
        for prov in prov_parts:
            loc = geocode(prov, ls)
            if loc:
                ret.append(loc)
        return ret

    part_locs = []
    for prov in prov_parts:
        loc = geocode(prov, ls)
        if loc:
            part_locs.append(loc)

    multi_loc = geocode(", ".join(prov_parts), ls)
    if not multi_loc:
        return first_if_close(part_locs)

    if all([is_close(loc.point, multi_loc.point) for loc in part_locs]):
        return [multi_loc]

    return first_if_close(part_locs)


def first_if_close(part_locs):
    if not part_locs:
        return []

    for i, l1 in enumerate(part_locs):
        for l2 in part_locs[i:]:
            if not is_close(l1.point, l2.point):
                return part_locs

    return [part_locs[0]]


def is_close(p1, p2):
    return geodesic(p1, p2).km < 12


def is_in_bounds(p, bounds):
    min_lat = bounds[0].latitude
    max_lat = bounds[1].latitude
    if min_lat > max_lat:
        min_lat, max_lat = max_lat, min_lat
    min_long = bounds[0].longitude
    max_long = bounds[1].longitude
    if min_long > max_long:
        min_long, max_long = max_long, min_long

    return min_lat <= p.latitude <= max_lat and min_long < p.longitude < max_long


def geocode_lantmateriet(prov, ls):
    # curl 'https://minkarta.lantmateriet.se/api/searchservice/searchinput?&searchtext=K%C3%A4llby' | jq .
    # {
    #   "antalsokresultat": 147,
    #   "sokresultat": [
    #     {
    #       "typ": "ORTNAMN",
    #       "position": {
    #         "east": 401378,
    #         "north": 6487224
    #       },
    #       "id": "4328929",
    #       "headertext": "Källby",
    #       "subtext": "Götene | Tätort"
    #     },
    #     {
    #       "typ": "ORTNAMN",
    #       "position": {
    #         "east": 402866,
    #         "north": 6486659
    #       },
    #       "id": "4272100",
    #       "headertext": "Källby",
    #       "subtext": "Götene | Bebyggelse"
    #     },
    #
    # filter to exclude typ=ADRESS
    #
    # from pyproj import Transformer
    # transformer = Transformer.from_crs("EPSG:3006", "EPSG:4326")
    # lat, lng = transformer.transform(401378, 6487224)

    # only query by prov, and use ls shapes to determine if a place is
    # within landskap
    #
    # import geopandas as gpd
    # from shapely.geometry import Point
    #
    # # Read GeoJSON
    # gdf = gpd.read_file('polygon.geojson')
    #
    # point = Point(longitude, latitude)
    # is_inside = gdf.geometry.contains(point).any()
    #
    # if there are more than one comma-separated prov, first search
    # all of them. if there's no result, search each one individually
    # and compare each search result if they're within 12km of each
    # other to find clusters. only look for immediate next neighbors,
    # e.g. Källebäcken, Gustav Adolf, Habo, Herrestad, Uddevalla
    #
    # if one of the comma-separated provs is a landskap as in
    # "Fagerhult, Habo, Västergötland, Uddevalla, Bohuslän", recursively call
    # geocode_lantmateriet("Fagerhult, Habo", "Västergötland"),
    # geocode_lantmateriet("Uddevalla", "Bohuslän")
    #
    # lantmateriet doesnt fix spelling mistakes, so rename
    # bovallsstrand to bovallstrand, etc. log all single places with no results


    pass

def geocode(prov, ls):
    query = f"{prov}, {ls}".strip(" ,")

    if query in CACHE:
        locs = CACHE[query]

    else:
        print(query)
        try:
            locs = gmaps.geocode(query, exactly_one=False, bounds=BOUNDS)
        except GeocoderQueryError:
            print("query error", query)
            locs = []
        cache(query, locs)

    if not locs:
        return None

    for loc in locs:
        if is_in_bounds(loc, BOUNDS):
            return loc

    if ls:
        return geocode(prov, "")

    if prov == "Askersund":
        print("not in bounds", prov, ls, locs)

    return None


def cache(query, loc):
    CACHE[query] = loc
    with open("loc.cache", "wb") as f:
        pickle.dump(CACHE, f)


def load_cache():
    with open("loc.cache", "rb") as f:
        return pickle.load(f)


def compute_landskap_bounds():
    landskap = gpd.read_file("svenska-landskap.geo.json")
    bounds_dict = {
        row["landskap"]: bounds_to_points(row.geometry.bounds)
        for _, row in landskap.iterrows()
    }
    return bounds_dict


def bounds_to_points(b):
    return (Point(b[3], b[0]), Point(b[1], b[2]))


def combined_bounds(*bs, padding=0.0):
    min_y = float("inf")
    min_x = float("inf")
    max_y = float("-inf")
    max_x = float("-inf")

    for b in bs:
        if b[0][0] > max_y:
            max_y = b[0][0]
        if b[1][0] < min_y:
            min_y = b[1][0]
        if b[0][1] < min_x:
            min_x = b[0][1]
        if b[1][1] > max_x:
            max_x = b[1][1]

    return (
        Point(max_y + padding, min_x - padding),
        Point(min_y - padding, max_x + padding),
    )


CACHE = load_cache()
LANDSKAP_BOUNDS = compute_landskap_bounds()
BOUNDS = combined_bounds(
    LANDSKAP_BOUNDS["Västergötland"],
    LANDSKAP_BOUNDS["Bohuslän"],
    LANDSKAP_BOUNDS["Dalsland"],
    padding=0.3,
)
