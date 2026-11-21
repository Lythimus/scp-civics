#!/usr/bin/env python3
"""Who lives next to what in St. Charles Parish: the parish's 14 communities compared.

  communities.py places [--km 2]                    every community side by side, plus a tiling check
  communities.py profile NORCO [--km 2]             one community: people, districts, land use, neighbours
  communities.py point "15045 River Rd, Hahnville"  community, tract and block group at an address
  communities.py point --point 29.9634,-90.4070
  communities.py distribution [--since 1999]        enacted rezonings placed on the map, by community
                                                    and council district

Sources, all public; a Census key is used if CENSUS_API_KEY is set (or in bayou's bayou-credentials.md): the parish GIS (community, council district, Future Land Use and
zoning layers), Census TIGERweb 2020 blocks, the 2020 census (P2) by block, ACS 5-year estimates for
each community's Census Designated Place (CDP), the LDEQ facility list through scp-facilities, NCES
school locations and CMS nursing home and hospital listings.

Two population figures, never mixed:
  * 2020 census counts, exact, summed over the blocks whose interior point is inside the parish's
    own community polygon.
  * ACS estimates with margins of error, published by the Census Bureau for the CDP of the same
    name. A CDP's boundary is the Census Bureau's, not the parish's.

Nothing here describes a single household: an address query reports block group and larger areas.
Parish GIS staff logins, the zoning layer's file links and parcel owners are never printed.

Public data is cached in --cache (default ~/.cache/scp-civics/communities), never in the plugin.
Exit codes: 0 answered, 1 no match, 2 a source could not be reached. Stdlib only.
"""
import argparse, collections, importlib.util, json, math, os, re, sys, time
import urllib.parse, urllib.request
from pathlib import Path

sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
SKILLS = Path(__file__).resolve().parents[2]
UA = {"User-Agent": "scp-civics/0.1 (public records research)"}
GIS = "https://maps.scpgis.com/geoserver/rest/services"
GEOCODER = f"{GIS}/Address_Point_Locator/GeocodeServer/findAddressCandidates"
COMMUNITY_LAYER = f"{GIS}/Public/GIS_Data/MapServer/2"
COUNCIL_LAYER = f"{GIS}/Public/GIS_Data/MapServer/4"
ZONING_LAYER = f"{GIS}/Planning_Map_MIL1/MapServer/1"
FLUM_LAYER = f"{GIS}/Planning_Map_MIL1/MapServer/2"
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer"
BLOCKS_2020, BLOCK_GROUPS_2020 = f"{TIGER}/12", f"{TIGER}/11"
CENSUS_TABLE = "https://data.census.gov/api/access/data/table"
NCES = "https://services1.arcgis.com/Ua5sjt3LWTPigjyD/arcgis/rest/services"
CMS = "https://data.cms.gov/provider-data/api/1/datastore/query"
CMS_NURSING, CMS_HOSPITAL = "4pq5-n9py", "xubh-q36u"
DEFAULT_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "scp-civics" / "communities"
STATE, COUNTY = "22", "089"
ACS_YEAR = 2024  # the 2020-2024 5-year release; 2021-2025 is due in December 2026
MIN_SCORE = 90

# Parish community polygon name -> 2020 CDP GEOID. Every parish community has a CDP of the same
# name (TIGERweb Census 2020 layer, checked 2026-11-19).
CDP = {"AMA": "2201780", "BAYOU GAUCHE": "2205315", "BOUTTE": "2209130", "DES ALLEMANDS": "2220680",
       "DESTREHAN": "2220820", "HAHNVILLE": "2232510", "KILLONA": "2239720", "LULING": "2246615",
       "MONTZ": "2251795", "NEW SARPY": "2255140", "NORCO": "2255525", "PARADIS": "2258920",
       "ST. ROSE": "2267740", "TAFT": "2274550"}
EAST_BANK = {"MONTZ", "NORCO", "NEW SARPY", "DESTREHAN", "ST. ROSE"}
LEVEE = {"east": "Pontchartrain Levee District (R.S. 38:291(L))",
         "west": "Lafourche Basin Levee District (R.S. 38:291(F))"}
# Future Land Use categories that plan for industry next to people.
INDUSTRIAL_FLUM = ("Heavy Industrial", "Industrial", "Industrial Buffer")
# ACS measures: label, table, numerator cells, denominator cells. Cells are the table's line numbers.
MEASURES = (
    ("Black, not Hispanic", "B03002", ["004"], ["001"]),
    ("Hispanic or Latino", "B03002", ["012"], ["001"]),
    ("White, not Hispanic", "B03002", ["003"], ["001"]),
    ("Below the poverty line", "C17002", ["002", "003"], ["001"]),
    ("Below twice the poverty line", "C17002", ["002", "003", "004", "005", "006", "007"], ["001"]),
    ("Under 5", "B01001", ["003", "027"], ["001"]),
    ("65 and over", "B01001", [f"{n:03d}" for n in (*range(20, 26), *range(44, 50))], ["001"]),
    ("Households with no vehicle", "B25044", ["003", "010"], ["001"]),
    ("Limited-English households", "C16002", ["004", "007", "010", "013"], ["001"]),
    ("Renter households", "B25003", ["003"], ["001"]),
)
INCOME = ("Median household income", "B19013", "001")


class SourceError(Exception):
    pass


# ---------------------------------------------------------------- fetching and cache

def fetch(url, data=None, tries=3, timeout=90, headers=UA):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:  # TIGERweb, data.census.gov and the parish GIS all drop requests at times
            if attempt == tries - 1:
                raise SourceError(f"{url.split('?')[0]}: {exc}") from exc
            time.sleep(2 * (attempt + 1))


def fetch_json(url, data=None, headers=UA):
    try:
        body = json.loads(fetch(url, data, headers=headers))
    except json.JSONDecodeError as exc:
        raise SourceError(f"{url.split('?')[0]}: not JSON") from exc
    if isinstance(body, dict) and body.get("error"):
        raise SourceError(f"{url.split('?')[0]}: {body['error']}")
    return body


class Cache:
    """JSON files under one folder, reused for max_age days. The plugin folder is refused."""

    def __init__(self, folder, max_age=7, refresh=False):
        self.folder, self.max_age, self.refresh = Path(folder).expanduser(), max_age, refresh
        resolved = self.folder.resolve()
        if SKILLS.parent.resolve() in (resolved, *resolved.parents):
            sys.exit("--cache must be outside the plugin folder.")

    def get(self, key, make):
        path = self.folder / f"{key}.json"
        if not self.refresh and path.exists() and time.time() - path.stat().st_mtime < self.max_age * 86400:
            return json.loads(path.read_text())
        value = make()
        self.folder.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return value

    def age(self, key):
        path = self.folder / f"{key}.json"
        return time.strftime("%Y-%m-%d", time.localtime(path.stat().st_mtime)) if path.exists() else "now"


def arcgis(layer, fields, where="1=1", geometry=True, page=2000):
    """Every feature of an ArcGIS layer as {"a": attributes, "rings": [[[lon, lat], ...], ...]}."""
    out, offset = [], 0
    while True:
        params = {"where": where, "outFields": ",".join(fields), "returnGeometry": str(geometry).lower(),
                  "outSR": 4326, "f": "json", "resultOffset": offset, "resultRecordCount": page}
        body = fetch_json(f"{layer}/query", urllib.parse.urlencode(params).encode())
        feats = body.get("features", [])
        for f in feats:
            out.append({"a": f["attributes"], "rings": (f.get("geometry") or {}).get("rings", [])})
        if not feats or not body.get("exceededTransferLimit"):
            return out
        offset += len(feats)


# Summary levels: data.census.gov's "g" code, and api.census.gov's for/in clauses.
LEVELS = {
    "place": ("0400000US{state}$1600000", [("for", "place:*"), ("in", "state:{state}")]),
    "tract": ("050XX00US{state}{county}$1400000", [("for", "tract:*"), ("in", "state:{state}"), ("in", "county:{county}")]),
    "block group": ("050XX00US{state}{county}$1500000",
                    [("for", "block group:*"), ("in", "state:{state}"), ("in", "county:{county}")]),
    "block": ("050XX00US{state}{county}$1000000",
              [("for", "block:*"), ("in", "state:{state}"), ("in", "county:{county}"), ("in", "tract:*")]),
}
CENSUS_API = "https://api.census.gov/data"
CREDENTIALS = Path.home() / ".claude" / "bayou-credentials.md"
_census = {"warned": False}


def census_key(path=CREDENTIALS):
    """CENSUS_API_KEY from the environment, else a "CENSUS_API_KEY: value" line in the bayou credentials
    file if that plugin is set up. None means the keyless endpoint is used."""
    if os.environ.get("CENSUS_API_KEY", "").strip():
        return os.environ["CENSUS_API_KEY"].strip()
    try:
        for line in Path(path).read_text().splitlines():
            m = re.match(r"\s*[-*]?\s*CENSUS_API_KEY\s*:\s*`?([0-9A-Za-z]{20,})`?\s*$", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return None


def census_table(dataset, table, level):
    """Rows of one census table as dicts with GEO_ID, NAME and the table's cells.

    dataset is "acs" (the ACS 5-year release, ACS_YEAR) or "pl" (2020 redistricting data). With a key,
    this asks api.census.gov, which answers 302 to missing_key.html without one (checked 2026-11-19).
    Without a key, or if the keyed request fails, it asks data.census.gov's table endpoint: what the
    data.census.gov site calls, not a documented API, and it could change. Both return the same rows.
    """
    key = census_key()
    if key:
        path = f"{ACS_YEAR}/acs/acs5" if dataset == "acs" else "2020/dec/pl"
        geo = [(k, v.format(state=STATE, county=COUNTY)) for k, v in LEVELS[level][1]]
        url = f"{CENSUS_API}/{path}?" + urllib.parse.urlencode([("get", f"NAME,group({table})"), *geo, ("key", key)])
        try:
            data = fetch_json(url)
            if isinstance(data, list) and len(data) > 1:
                return [dict(zip(data[0], r)) for r in data[1:]]
            raise SourceError(f"{CENSUS_API}/{path}: no rows for {table} {level}")
        except SourceError as exc:  # an invalid or not yet active key lands here as a redirect to an HTML page
            if not _census["warned"]:
                print(f"api.census.gov failed with the key ({exc}); using data.census.gov without it.", file=sys.stderr)
                _census["warned"] = True
    ident = f"ACSDT5Y{ACS_YEAR}.{table}" if dataset == "acs" else f"DECENNIALPL2020.{table}"
    g = LEVELS[level][0].format(state=STATE, county=COUNTY)
    body = fetch_json(f"{CENSUS_TABLE}?" + urllib.parse.urlencode({"id": ident, "g": g}))
    data = (body.get("response") or {}).get("data")
    if not data:
        raise SourceError(f"{CENSUS_TABLE}: no rows for {table} {level}")
    return [dict(zip(data[0], r)) for r in data[1:]]


def num(value):
    """A census cell as a number. Negative sentinels (-666666666 and the like) mean not computed."""
    try:
        n = float(str(value).replace(",", "").rstrip("+-"))
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


# ---------------------------------------------------------------- geometry

def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)


def contains(rings, lon, lat, box=None):
    """Even-odd point in polygon over every ring, so holes count as outside."""
    if box and not (box[0] <= lon <= box[2] and box[1] <= lat <= box[3]):
        return False
    inside = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def km_between(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def km_to_polygon(rings, lon, lat):
    """0 inside the polygon, else the distance to its nearest edge (flat projection, fine at parish scale)."""
    if contains(rings, lon, lat):
        return 0.0
    kx, ky = 111.32 * math.cos(math.radians(lat)), 110.57
    best = float("inf")
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            ax, ay = (x1 - lon) * kx, (y1 - lat) * ky
            bx, by = (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def centroid(rings):
    """Area-weighted centroid of the outer rings, for placing a zoning polygon in a community."""
    sx = sy = sa = 0.0
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            cross = x1 * y2 - x2 * y1
            sa += cross
            sx += (x1 + x2) * cross
            sy += (y1 + y2) * cross
    if abs(sa) < 1e-15:
        x0, y0, x1, y1 = bbox(rings)
        return (x0 + x1) / 2, (y0 + y1) / 2
    return sx / (3 * sa), sy / (3 * sa)


def touches(a, b, step=5):
    """Whether polygons a and b overlap, judged by sampled vertices of each falling in the other.

    Sampling can miss a sliver overlap; that is acceptable for a list of nearby land-use categories.
    """
    box_a, box_b = bbox(a), bbox(b)
    if box_a[0] > box_b[2] or box_b[0] > box_a[2] or box_a[1] > box_b[3] or box_b[1] > box_a[3]:
        return False
    return (any(contains(b, x, y, box_b) for ring in a for x, y in ring[::step])
            or any(contains(a, x, y, box_a) for ring in b for x, y in ring[::step]))


class Areas:
    """Named polygons with bounding boxes, answering which one holds a point."""

    def __init__(self, features, key):
        self.items = [(str(f["a"].get(key) or "").strip(), f["rings"], bbox(f["rings"])) for f in features]

    def at(self, lon, lat):
        return [name for name, rings, box in self.items if contains(rings, lon, lat, box)]

    def rings(self, name):
        return [r for n, rings, _ in self.items if n == name for r in rings]

    def names(self):
        return sorted({n for n, _, _ in self.items})


# ---------------------------------------------------------------- loading sources

def load_geo(cache):
    communities = cache.get("communities", lambda: arcgis(COMMUNITY_LAYER, ["name"]))
    council = cache.get("council", lambda: arcgis(COUNCIL_LAYER, ["district"]))
    flum = cache.get("flum", lambda: arcgis(FLUM_LAYER, ["dev_type"]))
    return Areas(communities, "name"), Areas(council, "district"), Areas(flum, "dev_type")


def load_blocks(cache):
    """2020 blocks: {geoid: {pop, lat, lon, race counts}} from TIGERweb points and the P2 table."""
    def make():
        where = f"STATE='{STATE}' AND COUNTY='{COUNTY}'"
        pts = arcgis(BLOCKS_2020, ["GEOID", "POP100", "INTPTLAT", "INTPTLON"], where, geometry=False, page=5000)
        p2 = {r["GEO_ID"][-15:]: r for r in census_table("pl", "P2", "block")}
        out = {}
        for p in pts:
            g = p["a"]["GEOID"]
            r = p2.get(g, {})
            out[g] = {"pop": int(p["a"]["POP100"] or 0), "lat": float(p["a"]["INTPTLAT"]),
                      "lon": float(p["a"]["INTPTLON"]),
                      "hisp": int(num(r.get("P2_002N")) or 0), "white": int(num(r.get("P2_005N")) or 0),
                      "black": int(num(r.get("P2_006N")) or 0), "asian": int(num(r.get("P2_008N")) or 0),
                      "p2_total": int(num(r.get("P2_001N")) or 0)}
        return out
    return cache.get("blocks2020", make)


def assign_blocks(blocks, communities, council, flum):
    """Tag each block with the community, council district and FLUM category holding its interior point."""
    for b in blocks.values():
        c = communities.at(b["lon"], b["lat"])
        d = council.at(b["lon"], b["lat"])
        f = flum.at(b["lon"], b["lat"])
        b["community"], b["district"], b["flum"] = (c[0] if c else ""), (d[0] if d else ""), (f[0] if f else "")
    for geoid, b in blocks.items():
        b["geoid"] = geoid
    return blocks


def acs_places(cache, tables):
    """{CDP GEOID: {cell: value}} for the parish's CDPs, one statewide request per table."""
    wanted = set(CDP.values())
    out = collections.defaultdict(dict)
    for t in tables:
        rows = cache.get(f"acs{ACS_YEAR}_{t}_places",
                         lambda t=t: [r for r in census_table("acs", t, "place")
                                      if r["GEO_ID"][-7:] in wanted])
        for r in rows:
            out[r["GEO_ID"][-7:]].update(r)
            out[r["GEO_ID"][-7:]]["NAME"] = r.get("NAME")
    return out


def acs_small_areas(cache, tables, level):
    """{GEOID: {cell: value}} for every tract or block group in the parish."""
    out = collections.defaultdict(dict)
    for t in tables:
        rows = cache.get(f"acs{ACS_YEAR}_{t}_{level.replace(' ', '')}",
                         lambda t=t: census_table("acs", t, level))
        for r in rows:
            out[r["GEO_ID"].split("US", 1)[-1]].update(r)
    return out


def facilities_module():
    path = SKILLS / "scp-facilities" / "scripts" / "facilities.py"
    spec = importlib.util.spec_from_file_location("scp_facilities", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_facilities(cache):
    """LDEQ AIs with a plotted point: scp-facilities' roster sites, plus its broader `near` types.

    Roster sites (`roster: True`) follow facilities.py `in_roster`: the chemical, refining and pipeline
    types plus its named power plants and terminals. The broader `near` types also hold septic, dump
    and other records filed under private people's names, so those are counted, never named.
    """
    def make():
        fac = facilities_module()
        try:
            ais = fac.ldeq_ais()
        except RuntimeError as exc:
            raise SourceError(str(exc)) from exc
        return [{"id": ai["id"], "name": ai["name"], "type": ai["typeName"],
                 "address": (ai.get("physicalAddress") or "").replace("\n", ", "),
                 "lat": ai["latitude"], "lon": ai["longitude"], "roster": fac.in_roster(ai)}
                for ai in ais if ai.get("latitude") is not None and ai.get("longitude") is not None
                and (fac.in_roster(ai) or (ai["typeName"] in fac.NEAR_TYPES and fac.looks_like_company(ai)))]
    return cache.get("facilities_v2", make)


def load_institutions(cache):
    """Schools (NCES), nursing homes and hospitals (CMS) with a point each."""
    def make():
        out = []
        for service, where, kind in (
                ("Public_School_Locations_Current", f"CNTY='{STATE}{COUNTY}'", "public school"),
                # NCES codes CNTY with three digits on the private-school layer
                ("Private_School_Locations_Current", f"STATE='LA' AND CNTY='{COUNTY}'", "private school")):
            for f in arcgis(f"{NCES}/{service}/FeatureServer/0", ["NAME", "STREET", "CITY", "LAT", "LON", "SCHOOLYEAR"],
                            where, geometry=False):
                a = f["a"]
                out.append({"kind": kind, "name": a["NAME"], "address": f"{a['STREET']}, {a['CITY']}",
                            "lat": a["LAT"], "lon": a["LON"], "source": f"NCES {a['SCHOOLYEAR']}"})
        for dataset, kind in ((CMS_NURSING, "nursing home"), (CMS_HOSPITAL, "hospital")):
            county = "St. Charles" if dataset == CMS_NURSING else "ST. CHARLES"  # CMS cases them differently
            params = {"conditions[0][property]": "state", "conditions[0][value]": "LA",
                      "conditions[1][property]": "countyparish", "conditions[1][value]": county, "limit": 100}
            # CMS answers 403 to a descriptive User-Agent and 200 to urllib's default (checked 2026-11-19)
            rows = fetch_json(f"{CMS}/{dataset}/0?" + urllib.parse.urlencode(params), headers={}).get("results", [])
            for r in rows:
                name = r.get("provider_name") or r.get("facility_name")
                address = f"{(r.get('provider_address') or r.get('address') or '').title()}, {(r.get('citytown') or '').title()}"
                lat, lon = num(r.get("latitude")), (float(r["longitude"]) if r.get("longitude") else None)
                if lat is None:  # the hospital listing has no coordinates; place it with the parish geocoder
                    hit = geocode(address)
                    lat, lon = (hit[0]["location"]["y"], hit[0]["location"]["x"]) if hit and hit[0]["score"] >= MIN_SCORE else (None, None)
                out.append({"kind": kind, "name": name, "address": address, "lat": lat, "lon": lon, "source": "CMS"})
        return out
    return cache.get("institutions", make)


def geocode(address):
    url = GEOCODER + "?" + urllib.parse.urlencode({"SingleLine": address, "outSR": 4326, "maxLocations": 5, "f": "json"})
    return fetch_json(url).get("candidates", [])


# ---------------------------------------------------------------- arithmetic

def acs_sum(row, table, cells):
    """(estimate, MOE) of a sum of ACS cells; MOE by the root sum of squares, as the ACS handbook does."""
    ests = [num(row.get(f"{table}_{c}E")) for c in cells]
    moes = [num(row.get(f"{table}_{c}M")) or 0 for c in cells]
    if any(e is None for e in ests):
        return None, None
    return sum(ests), math.sqrt(sum(m * m for m in moes))


def acs_share(row, table, num_cells, den_cells):
    """(percent, MOE in points, reliable) for a proportion, with the ACS proportion formula."""
    n, nm = acs_sum(row, table, num_cells)
    d, dm = acs_sum(row, table, den_cells)
    if n is None or not d:
        return None, None, False
    p = n / d
    radicand = nm * nm - p * p * dm * dm
    if radicand < 0:  # the handbook falls back to the ratio formula here
        radicand = nm * nm + p * p * dm * dm
    moe = math.sqrt(radicand) / d
    reliable = p > 0 and (moe / 1.645) / p <= 0.30
    return 100 * p, 100 * moe, reliable


def fmt_share(value):
    p, moe, reliable = value
    if p is None:
        return "n/a"
    return f"{p:.0f}% ±{moe:.0f}" + ("" if reliable else " (unreliable)")


def fmt_income(row):
    """Median household income with its margin. A top-coded median prints as "$250,000+" with no margin."""
    raw = str(row.get("B19013_001E") or "")
    est, moe = num(raw), num(row.get("B19013_001M"))
    if est is None:
        return "n/a"
    text = f"${est:,.0f}" + ("+" if raw.endswith("+") else "-" if raw.endswith("-") else "")
    return text + (f" ±{moe:,.0f}" if moe is not None else "")


def block_totals(blocks):
    t = collections.Counter()
    for b in blocks:
        for k in ("pop", "hisp", "white", "black", "asian"):
            t[k] += b[k]
    return t


def pct(part, whole):
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def near_population(blocks, points, km):
    """Population of the populated blocks whose interior point is within km of any of the points."""
    hit = 0
    for b in blocks:
        if b["pop"] and any(km_between(b["lat"], b["lon"], p["lat"], p["lon"]) <= km for p in points):
            hit += b["pop"]
    return hit


def select_sites(facilities, all_types):
    return facilities if all_types else [f for f in facilities if f["roster"]]


def site_words(all_types):
    roster = "scp-facilities roster sites (LDEQ chemical, refining and pipeline AIs and the named power plants and terminals)"
    if all_types:
        return roster + " plus its broader `near` types (utilities, oil and gas field sites, freight, food)"
    return roster


def bank(name):
    return "east" if name in EAST_BANK else "west"


# ---------------------------------------------------------------- commands

def setup(a):
    cache = Cache(a.cache, a.max_age, a.refresh)
    communities, council, flum = load_geo(cache)
    blocks = assign_blocks(load_blocks(cache), communities, council, flum)
    return cache, communities, council, flum, blocks


def tiling(blocks, communities):
    total = sum(b["pop"] for b in blocks.values())
    placed = sum(b["pop"] for b in blocks.values() if b["community"])
    loose = sorted((b for b in blocks.values() if b["pop"] and not b["community"]), key=lambda b: -b["pop"])
    no_district = sum(b["pop"] for b in blocks.values() if b["pop"] and not b["district"])
    lines = [f"Tiling check: {placed:,} of {total:,} people (2020) are in blocks inside one of the "
             f"{len(communities.names())} community polygons; {total - placed:,} are not."]
    if loose:
        lines.append(f"  {len(loose)} populated blocks fall outside every community polygon; the largest hold "
                     + ", ".join(str(b["pop"]) for b in loose[:5]) + " people.")
    lines.append(f"  {no_district:,} people are in blocks outside every council district polygon.")
    return lines


def cmd_places(a):
    cache, communities, council, flum, blocks = setup(a)
    facilities = select_sites(load_facilities(cache), a.all_types)
    tables = sorted({m[1] for m in MEASURES} | {INCOME[1]})
    acs = acs_places(cache, tables)
    by = collections.defaultdict(list)
    for b in blocks.values():
        by[b["community"]].append(b)
    print(f"St. Charles Parish communities. 2020 counts are exact for the parish's polygons; ACS {ACS_YEAR - 4}-{ACS_YEAR} "
          "estimates are for the CDP of the same name. Data cached " + cache.age("blocks2020") + ".\n")
    head = (f"{'Community':14} {'Bank':4} {'Districts':9} {'Pop 2020':>8} {'Black':>6} {'Hisp':>5} "
            f"{'Ind.FLUM':>8} {f'<{a.km:g}km fac':>10} {'Pov (ACS)':>16} {'Med. income (ACS)':>20}")
    print(head)
    for name in communities.names():
        bl = by.get(name, [])
        t = block_totals(bl)
        districts = collections.Counter()
        for b in bl:
            if b["district"]:
                districts[b["district"]] += b["pop"]
        dist = ",".join(d for d, n in sorted(districts.items(), key=lambda x: -x[1]) if n)
        ind = sum(b["pop"] for b in bl if b["flum"] in INDUSTRIAL_FLUM)
        near = near_population(bl, facilities, a.km)
        row = acs.get(CDP.get(name, ""), {})
        pov = fmt_share(acs_share(row, "C17002", ["002", "003"], ["001"])) if row else "no CDP"
        income = fmt_income(row)
        print(f"{name.title():14} {bank(name):4} {dist or '-':9} {t['pop']:>8,} {pct(t['black'], t['pop']):>6} "
              f"{pct(t['hisp'], t['pop']):>5} {pct(ind, t['pop']):>8} {pct(near, t['pop']):>10} {pov:>16} {income:>20}")
    print("\nColumns: Districts = council districts holding the community's 2020 population, largest first. "
          "Black and Hisp = 2020 census, Black alone not Hispanic, and Hispanic of any race. "
          f"Ind.FLUM = share of 2020 population in blocks the Future Land Use Map (2023) places in "
          f"{', '.join(INDUSTRIAL_FLUM)}. <{a.km:g}km fac = share within {a.km:g} km of one of the "
          f"{site_words(a.all_types)}, by the agency's plotted point. "
          "Pov = ACS share below the poverty line, ±90% margin.")
    print("\n" + "\n".join(tiling(blocks, communities)))
    return 0


def cmd_profile(a):
    cache, communities, council, flum, blocks = setup(a)
    want = a.name.upper().replace("SAINT ", "ST. ").replace("ST ROSE", "ST. ROSE")
    names = [n for n in communities.names() if n == want] or [n for n in communities.names() if want in n]
    if len(names) != 1:
        print(f"No single community matches {a.name!r}. Communities: {', '.join(n.title() for n in communities.names())}")
        return 1
    name = names[0]
    rings = communities.rings(name)
    bl = [b for b in blocks.values() if b["community"] == name]
    t = block_totals(bl)
    print(f"{name.title()}, St. Charles Parish ({bank(name)} bank). Data cached {cache.age('blocks2020')}.\n")
    print(f"Levee district: {LEVEE[bank(name)]}. Confirm against the district's own map for a specific site.")

    districts = collections.Counter()
    for b in bl:
        districts[b["district"] or "outside every district polygon"] += b["pop"]
    print("Council districts (2020 population of the community in each): "
          + "; ".join(f"District {d}: {n:,}" for d, n in districts.most_common() if n))
    print("  For the members, run scp-government `district`.\n")

    print(f"People, 2020 census, {len(bl)} blocks inside the parish polygon (exact counts):")
    print(f"  Total {t['pop']:,}; Black alone, not Hispanic {t['black']:,} ({pct(t['black'], t['pop'])}); "
          f"White alone, not Hispanic {t['white']:,} ({pct(t['white'], t['pop'])}); Hispanic {t['hisp']:,} "
          f"({pct(t['hisp'], t['pop'])}); Asian alone, not Hispanic {t['asian']:,} ({pct(t['asian'], t['pop'])}).")
    tracts = collections.Counter()
    for b in bl:
        tracts[b.get("geoid", "")[:11]] += b["pop"]
    print("  2020 census tracts holding this population: " + "; ".join(
        f"{g[5:9]}.{g[9:]} ({pct(n, t['pop'])})" for g, n in tracts.most_common() if n and g)
          + ". Tract-level sources (CDC's Environmental Justice Index, for one) use these.")
    geoid = CDP.get(name)
    if geoid:
        tables = sorted({m[1] for m in MEASURES} | {INCOME[1], "B01003"})
        row = acs_places(cache, tables).get(geoid, {})
        pop, pop_m = acs_sum(row, "B01003", ["001"])
        print(f"\nACS {ACS_YEAR - 4}-{ACS_YEAR} estimates for {row.get('NAME', name.title() + ' CDP')} "
              f"(the Census Bureau's boundary, not the parish's), ±90% margins:")
        if pop is not None:
            print(f"  Population {pop:,.0f} ±{pop_m:,.0f}")
        for label, table, nums, dens in MEASURES:
            print(f"  {label}: {fmt_share(acs_share(row, table, nums, dens))}")
        print(f"  {INCOME[0]}: {fmt_income(row)}")
        print("  'Unreliable' means a coefficient of variation over 30%. Small CDPs often are; say so when citing them.")

    print("\nFuture Land Use Map (2023), 2020 population by the category at each block's interior point:")
    by_flum = collections.Counter()
    for b in bl:
        by_flum[b["flum"] or "no FLUM polygon"] += b["pop"]
    for cat, n in by_flum.most_common():
        if n:
            flag = "  <- industrial" if cat in INDUSTRIAL_FLUM else ""
            print(f"  {cat:28} {n:>7,} ({pct(n, t['pop'])}){flag}")
    present = sorted({n for n, r, _ in flum.items if touches(rings, r)})
    if present:
        print("  Categories with land in or touching the community: " + ", ".join(present))

    facilities = select_sites(load_facilities(cache), a.all_types)
    rows = [(km_to_polygon(rings, f["lon"], f["lat"]), f) for f in facilities]
    rows = sorted(((d, near_population(bl, [f], a.km), f) for d, f in rows if d <= a.km), key=lambda x: (-x[1], x[0]))
    named = [r for r in rows if r[2]["roster"]]
    print(f"\nSites inside or within {a.km:g} km of the community boundary: {len(rows)} {site_words(a.all_types)}. "
          f"Most {name.title()} residents within {a.km:g} km first:")
    for d, nearby, f in named[: a.top]:
        where = "inside" if d == 0 else f"{d:.1f} km outside"
        print(f"  {f['id']:>7} {f['name'][:58]:58} {where:>15} | {nearby:>6,} residents | {f['type']}")
    if len(named) > a.top:
        print(f"  ... {len(named) - a.top} more; raise --top.")
    others = collections.Counter(f["type"] for _, _, f in rows if not f["roster"])
    if others:
        print(f"  Plus {sum(others.values())} other registered sites, counted and not named because these types also "
              "hold records filed under private people's names: "
              + ", ".join(f"{n} {t}" for t, n in others.most_common()) + ". scp-facilities `near` lists them.")
    print(f"  {near_population(bl, facilities, a.km):,} of {t['pop']:,} {name.title()} residents (2020) live within "
          f"{a.km:g} km of at least one, measured from each block's interior point.")
    print("  A registration isn't an operating plant or a source of harm. scp-facilities `find <AI>` gives the record.")

    try:
        inst = load_institutions(cache)
    except SourceError as exc:
        inst, gaps = [], f"not checked: {exc}"
    else:
        gaps = ""
    near_inst = sorted(((km_to_polygon(rings, i["lon"], i["lat"]), i) for i in inst if i["lat"] is not None),
                       key=lambda x: x[0])
    print(f"\nSchools, nursing homes and hospitals inside or within {a.km:g} km:" + (f" {gaps}" if gaps else ""))
    for d, i in near_inst:
        if d <= a.km:
            roster = [f for f in facilities if f["roster"]]
            fac_d = min(((km_between(i["lat"], i["lon"], f["lat"], f["lon"]), f) for f in roster),
                        key=lambda x: x[0]) if roster else None
            nearest = f"; nearest roster site {fac_d[1]['name'][:40]} at {fac_d[0]:.1f} km" if fac_d else ""
            print(f"  {i['kind']:14} {i['name'][:45]:45} {('inside' if d == 0 else f'{d:.1f} km out'):>11} ({i['source']}){nearest}")
    print("  NCES listed one private school in the parish (2023-24), so private schools are likely incomplete. "
          "Child care centers and parks aren't covered.")

    print("\nDrainage: the Master Drainage Plan's basins don't follow community lines. Find this community's "
          "basins in scp-master-drainage-plan references/watersheds.md and confirm a site with its `mdp_index.py find`.")
    return 0


def cmd_point(a):
    if a.point:
        try:
            lat, lon = (float(x) for x in a.point.split(","))
        except ValueError:
            sys.exit("--point takes LAT,LON in decimal degrees, e.g. 29.9634,-90.4070")
        print(f"Point {lat:.6f}, {lon:.6f}")
    else:
        cands = geocode(a.address)
        if not cands or cands[0]["score"] < MIN_SCORE:
            print("No confident match from the parish geocoder. Try the street address without unit or ZIP, or --point.")
            for c in cands[:5]:
                print(f"  {c['score']:5.1f}  {c['address']}")
            return 1
        lon, lat = cands[0]["location"]["x"], cands[0]["location"]["y"]
        print(f"Matched {cands[0]['address']} (score {cands[0]['score']:.0f}) at {lat:.6f}, {lon:.6f}")
    cache = Cache(a.cache, a.max_age, a.refresh)
    communities, council, flum = load_geo(cache)
    c, d, f = communities.at(lon, lat), council.at(lon, lat), flum.at(lon, lat)
    if not d and not c:
        print("This point is outside the parish's community and council layers, so probably outside St. Charles Parish.")
        return 1
    print(f"Community: {c[0].title() if c else 'none on the parish layer'}"
          + (f" ({bank(c[0])} bank; generally {LEVEE[bank(c[0])]}, confirm on the district's map)" if c else ""))
    print(f"Council district: {d[0] if d else 'none'} (members: scp-government `district`)")
    print(f"Future Land Use Map (2023): {f[0] if f else 'no category at this point'}")
    params = {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "false", "f": "json"}
    bg = fetch_json(f"{BLOCK_GROUPS_2020}/query?" + urllib.parse.urlencode(params)).get("features", [])
    if not bg:
        print("No 2020 block group at this point.")
        return 0
    bg_id = bg[0]["attributes"]["GEOID"]
    tract = bg_id[:11]
    tables = sorted({m[1] for m in MEASURES} | {INCOME[1], "B01003"})
    print(f"\n2020 tract {tract[5:9]}.{tract[9:]} and block group {bg_id[-1]} (GEOID {bg_id}). "
          f"ACS {ACS_YEAR - 4}-{ACS_YEAR}, ±90% margins:")
    small = {"block group": acs_small_areas(cache, tables, "block group").get(bg_id, {}),
             "tract": acs_small_areas(cache, tables, "tract").get(tract, {})}
    print(f"  {'':32} {'Block group':>22} {'Tract':>22}")
    pops = [acs_sum(small[k], "B01003", ["001"]) for k in ("block group", "tract")]
    print(f"  {'Population':32} " + " ".join(f"{(f'{p:,.0f} ±{m:,.0f}' if p is not None else 'n/a'):>22}" for p, m in pops))
    for label, table, nums, dens in MEASURES:
        print(f"  {label:32} " + " ".join(f"{fmt_share(acs_share(small[k], table, nums, dens)):>22}"
                                          for k in ("block group", "tract")))
    print(f"  {INCOME[0]:32} " + " ".join(f"{fmt_income(small[k]):>22}" for k in ("block group", "tract")))
    print("\nBlock-level figures are left out on purpose: a block can be a handful of homes. "
          "For sites near this point, use scp-facilities `near`.")
    return 0


# ---------------------------------------------------------------- distribution

def norm_zone(code):
    c = (code or "").strip().upper().replace("-", "")
    return c


def is_industrial(code):
    """M-1, M-2 and M-3. MS and the other M-initial codes aren't counted as industrial."""
    return bool(re.fullmatch(r"M\d", norm_zone(code)))


def zone_family(frm, to):
    """The family a map amendment moves land into, judged by its target districts."""
    if any(is_industrial(c) for c in to):
        return "within industrial (M to M)" if frm and all(is_industrial(c) for c in frm) else "newly industrial (M)"
    c = norm_zone(to[0]) if to else ""
    if c.startswith("R") or c == "CR1":
        return "residential"
    if c.startswith(("C", "B")):
        return "commercial"
    return "other"


def split_ordinances(text):
    return [o.strip() for o in re.split(r"[;,]", text or "") if re.fullmatch(r"\d{2}-\d{1,2}-\d{1,3}", o.strip())]


def load_decisions():
    path = SKILLS / "scp-decisions" / "scripts" / "decisions.py"
    spec = importlib.util.spec_from_file_location("scp_decisions", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def place_ordinances(zoning, communities, council):
    """{ordinance number: [(community, district, current zoning)]} from the zoning layer.

    The layer shows today's zoning; a polygon carries only the ordinances its editors recorded, and
    a later rezoning or a merge can overwrite an earlier one.
    """
    placed = collections.defaultdict(list)
    for z in zoning:
        ords = split_ordinances(z["a"].get("oridnance"))
        if not ords or not z["rings"]:
            continue
        x, y = centroid(z["rings"])
        c, d = communities.at(x, y), council.at(x, y)
        for o in ords:
            placed[o].append((c[0] if c else "", d[0] if d else "", norm_zone(z["a"].get("zoning"))))
    return placed


def cmd_distribution(a):
    cache = Cache(a.cache, a.max_age, a.refresh)
    communities, council, _ = load_geo(cache)
    zoning = cache.get("zoning", lambda: arcgis(ZONING_LAYER, ["zoning", "oridnance"]))
    placed = place_ordinances(zoning, communities, council)
    dec = load_decisions()
    print("Loading the rezoning set through scp-decisions (the first run fetches each matter; later runs use its cache).",
          file=sys.stderr)
    records, failed = dec.load_all(dec.rezoning_matters(), Path(a.decisions_cache).expanduser())
    rows = [dec.summarize(r) for r in records]
    rows = [r for r in rows if r["intro"][:4] >= str(a.since)]
    enacted = [r for r in rows if r["enactment"]]
    tally = collections.defaultdict(collections.Counter)
    unplaced_by_decade = collections.Counter()
    placed_by_decade = collections.Counter()
    listing = []
    for r in enacted:
        decade = r["intro"][:3] + "0s"
        spots = placed.get(r["enactment"].strip())
        if not spots:
            unplaced_by_decade[decade] += 1
            continue
        placed_by_decade[decade] += 1
        to = [dec.norm_code(x) for x in r["to"]] or ["?"]
        family = zone_family(r["from"], to)
        community, district = collections.Counter(s[0] for s in spots).most_common(1)[0][0], \
            collections.Counter(s[1] for s in spots).most_common(1)[0][0]
        tally[family][(community or "outside polygons", district or "?")] += 1
        if family.endswith("(M)") or family.startswith("within industrial"):
            listing.append((r["decided"] or r["intro"], r["file"], r["enactment"], ",".join(r["from"]) or "?",
                            ",".join(to), community.title() or "?", district or "?"))
    print(f"Enacted rezoning ordinances since {a.since}, placed by the zoning layer's ordinance field "
          f"(parish GIS, cached {cache.age('zoning')}).")
    print(f"{len(rows)} rezoning matters on Legistar in the period; {len(enacted)} carry an enactment number.")
    print("Placed / not placed, by decade of introduction: " + "; ".join(
        f"{d} {placed_by_decade[d]}/{unplaced_by_decade[d]}" for d in sorted(set(placed_by_decade) | set(unplaced_by_decade))))
    print("Failed, withdrawn and postponed rezonings never reach the map, so they can't be placed this way; "
          "scp-decisions `rezonings --where <community>` finds those by title words.\n")
    for family in ("newly industrial (M)", "within industrial (M to M)", "commercial", "residential", "other"):
        cells = tally.get(family)
        if not cells:
            continue
        by_c, by_d = collections.Counter(), collections.Counter()
        for (c, d), n in cells.items():
            by_c[c] += n
            by_d[d] += n
        print(f"{family[0].upper() + family[1:]}: {sum(cells.values())}")
        print("  by community: " + ", ".join(f"{c.title()} {n}" for c, n in by_c.most_common()))
        print("  by council district (today's lines): " + ", ".join(f"{d} {n}" for d, n in sorted(by_d.items())))
    if listing:
        print("\nRezonings to an M district that the map places:")
        print(f"  {'Decided':10} {'File':10} {'Ord.':9} {'From':10} {'To':8} {'Community':14} Dist.")
        for row in sorted(listing):
            print(f"  {row[0][:10]:10} {row[1]:10} {row[2]:9} {row[3][:10]:10} {row[4][:8]:8} {row[5][:14]:14} {row[6]}")
    if failed:
        print(f"\n{len(failed)} matters couldn't be read from Legistar: {', '.join(failed[:5])}")
        return 2
    print("\nDistricts are today's council lines (Ord. 22-12-12, 26-2-3), not the lines when each vote was cast. "
          "A polygon's centroid places it, so a rezoning on a community edge can land in the neighbour.")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--max-age", type=float, default=7, help="days before cached public data is fetched again")
    ap.add_argument("--refresh", action="store_true")
    sp = ap.add_subparsers(dest="cmd", required=True)
    broad = "also count scp-facilities' broader `near` types (utilities, oil and gas field sites, freight, food)"
    p = sp.add_parser("places"); p.add_argument("--km", type=float, default=2)
    p.add_argument("--all-types", action="store_true", help=broad)
    p.set_defaults(fn=cmd_places)
    p = sp.add_parser("profile"); p.add_argument("name"); p.add_argument("--km", type=float, default=2)
    p.add_argument("--all-types", action="store_true", help=broad)
    p.add_argument("--top", type=int, default=25); p.set_defaults(fn=cmd_profile)
    p = sp.add_parser("point"); p.add_argument("address", nargs="?"); p.add_argument("--point")
    p.set_defaults(fn=cmd_point)
    p = sp.add_parser("distribution"); p.add_argument("--since", type=int, default=1999)
    p.add_argument("--decisions-cache", default=str(DEFAULT_CACHE.parent / "decisions"))
    p.set_defaults(fn=cmd_distribution)
    a = ap.parse_args(argv)
    if a.cmd == "point" and not (a.address or a.point):
        ap.error("point needs an address or --point LAT,LON")
    try:
        return a.fn(a)
    except SourceError as exc:
        print(f"Source unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main())
