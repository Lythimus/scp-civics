#!/usr/bin/env python3
"""St. Charles Parish coastal permitting: the Coastal Zone Advisory Committee's permit lists, a site's
standing on the state's coastal maps, mapped coastal use permits near a place, and the Chapter 26 clocks.

  coastal.py czac [--since 2026-01-01] [--term Shell] [--permit P20260816] [--json]
  coastal.py site "15045 River Rd, Hahnville" | --point 29.999,-90.409 | --geojson footprint.geojson
  coastal.py near "Norco" | --point 29.999,-90.409 [--radius 1000] [--since 2015]
  coastal.py permit P20250727
  coastal.py clock --notice 2026-11-12 [--decision 2026-12-10] [--activity 2026-11-01]

Sources, all public and keyless:
  * Legistar (webapi.legistar.com, stcharlesgov), body 189, "SCP Coastal Zone Advisory Committee".
    Its agendas begin 2025-07-10; earlier committee agendas are not on Legistar.
  * The Office of Coastal Management's map service on sonris-gis.dnr.la.gov: coastal use permits
    (points, polygons, lines), the State Coastal Zone Boundary, the Five Foot Contour and Fastlands.
    The service refuses Python's default User-Agent, so every request names this tool.
  * The parish GIS (maps.scpgis.com): address locator, communities, council districts, the parish's
    copy of the National Wetlands Inventory, and the DFIRM flood zones.
  * USGS 3DEP elevation (epqs.nationalmap.gov) at a point, as context only.

Agenda rows and permit records can name private applicants. Print them for the user's research;
never copy them into this plugin.

Public data is cached in --cache (default ~/.cache/scp-civics/coastal), never in the plugin.
Exit codes: 0 answered, 1 no match, 2 a source could not be reached. Stdlib only.
"""
import argparse, datetime as dt, importlib.util, json, math, os, re, sys, time
import urllib.parse, urllib.request
from pathlib import Path

sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
SKILLS = Path(__file__).resolve().parents[2]
UA = {"User-Agent": "scp-civics/0.1 (public records research)"}
API = "https://webapi.legistar.com/v1/stcharlesgov"
CZAC_BODY = 189
OCM = "https://sonris-gis.dnr.la.gov/arcgis/rest/services/DNRSvc/OCM/MapServer"
OCM_POINTS, OCM_LINES, OCM_POLYGONS, OCM_ZONE, OCM_FIVE_FOOT, OCM_FASTLANDS = 0, 6, 16, 26, 30, 32
GIS = "https://maps.scpgis.com/geoserver/rest/services"
GEOCODER = f"{GIS}/Address_Point_Locator/GeocodeServer/findAddressCandidates"
COMMUNITY_LAYER = f"{GIS}/Public/GIS_Data/MapServer/2"
COUNCIL_LAYER = f"{GIS}/Public/GIS_Data/MapServer/4"
WETLANDS_LAYER = f"{GIS}/Public/Wetlands/MapServer/0"
DFIRM_LAYER = f"{GIS}/Public/Planning/MapServer/2"
EPQS = "https://epqs.nationalmap.gov/v1/json"
SONRIS_DOCS = "https://sonlite.dnr.state.la.us/ords/r/sonris/ucmsearch/finddocuments?qtype=eq&idx=xrefnum&val={}"
DEFAULT_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "scp-civics" / "coastal"
MIN_SCORE = 90
PERMIT_RE = re.compile(r"\bP(19|20)\d{6}\b")
SCP_RE = re.compile(r"\bSCP-\d{4}-\d{2,3}\b")
# Determination words seen on the committee's agendas, 2025-11 to 2026-11. Anything else is kept in the
# row's text; the meaning of RFD is not stated on the agendas, so it is reported as written.
CODES = ("CUP NEEDED", "CUP", "NDSI", "EXEMPT", "DENIAL", "WITHDRAWN", "IN REVIEW", "RFD",
         "ADDITIONAL INFO REQUESTED", "ADDITIONAL INFORMATION REQUESTED", "RETURNED FOR ADDITIONAL INFO")
CODE_RE = re.compile(r"(?<![A-Z])(" + "|".join(re.escape(c) for c in sorted(CODES, key=len, reverse=True))
                     + r")(?![A-Z])", re.I)
CODE_MEANING = {"NDSI": "no direct and significant impact", "CUP": "coastal use permit required or issued",
                "EXEMPT": "exempt from a coastal use permit"}
# Chapter 26 and R.S. 49:214 periods, as (label, trigger, days, source). Calendar days.
CLOCKS = (
    ("Public comment period ends (local concern)", "notice", 25, "Sec. 26-6; R.S. 49:214.30"),
    ("Request for a public hearing due", "notice", 25, "Sec. 26-6 (from the official journal publication)"),
    ("Parish comments to the state due (state concern)", "notice", 25, "Sec. 26-6"),
    ("Parish decision due, if no hearing is held", "notice", 30, "Sec. 26-6; R.S. 49:214.30(C)(3)"),
    ("Administrative appeal due", "decision", 15, "Sec. 26-9(a), from the date the decision was issued"),
    ("Request for a public appeal (10 or more residents) due", "decision", 10,
     "Sec. 26-9(d)(1), within 10 days of the decision or of the notice for administrative appeal"),
    ("Petition for reconsideration due", "decision", 10,
     "Sec. 26-9(w)(1) counts from public notice of the final permit; R.S. 49:214.35(B) now counts from "
     "posting on the department's website"),
    ("After-the-fact permit request due", "activity", 15, "Sec. 26-7(c), from the activity"),
)


class SourceError(Exception):
    pass


# ---------------------------------------------------------------- fetching and cache

def fetch(url, data=None, tries=3, timeout=90):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as exc:  # Legistar, SONRIS GIS and the parish GIS all drop requests at times
            if attempt == tries - 1:
                raise SourceError(f"{url.split('?')[0]}: {exc}") from exc
            time.sleep(2 * (attempt + 1))


def fetch_json(url, data=None):
    try:
        body = json.loads(fetch(url, data))
    except json.JSONDecodeError as exc:
        raise SourceError(f"{url.split('?')[0]}: not JSON") from exc
    if isinstance(body, dict) and body.get("error"):
        raise SourceError(f"{url.split('?')[0]}: {body['error']}")
    return body


class Cache:
    """JSON files under one folder, reused for max_age days. The plugin folder is refused."""

    def __init__(self, folder, max_age=1, refresh=False):
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


def legistar(path, **params):
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$'(),")
    return fetch_json(f"{API}{path}" + (f"?{query}" if query else ""))


def query(layer, **params):
    """One ArcGIS query, POSTed because footprint geometries outgrow a URL."""
    base = {"f": "json", "outSR": 4326, "returnGeometry": "false", "outFields": "*"}
    return fetch_json(f"{layer}/query", urllib.parse.urlencode({**base, **params}).encode()).get("features", [])


def ocm(layer):
    return f"{OCM}/{layer}"


def geometry_params(shape):
    """Query parameters for a point (lon, lat) or a list of rings."""
    if isinstance(shape, tuple):
        geom, kind = {"x": shape[0], "y": shape[1]}, "esriGeometryPoint"
    else:
        geom, kind = {"rings": shape}, "esriGeometryPolygon"
    return {"geometry": json.dumps({**geom, "spatialReference": {"wkid": 4326}}), "geometryType": kind,
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"}


def geocode(address):
    url = GEOCODER + "?" + urllib.parse.urlencode({"SingleLine": address, "outSR": 4326, "maxLocations": 5, "f": "json"})
    return fetch_json(url).get("candidates", [])


def from_epoch_ms(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date() if ms else None


# ---------------------------------------------------------------- geometry

def contains(rings, lon, lat):
    """Even-odd point in polygon over every ring, so holes count as outside."""
    inside = False
    for ring in rings:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def metres_to(parts, lon, lat, closed):
    """Distance from a point to a polygon (0 inside) or a polyline, flat projection at parish scale."""
    if closed and contains(parts, lon, lat):
        return 0.0
    kx, ky = 111320 * math.cos(math.radians(lat)), 110570
    best = float("inf")
    for part in parts:
        pairs = zip(part, part[1:] + part[:1]) if closed else zip(part, part[1:])
        for (x1, y1), (x2, y2) in pairs:
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
        if len(part) == 1:
            best = min(best, math.hypot((part[0][0] - lon) * kx, (part[0][1] - lat) * ky))
    return best


def centroid(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def sample_points(rings, grid=12):
    """Every vertex plus a grid of interior points: enough to show a footprint is not wholly on one class."""
    pts = [tuple(p) for r in rings for p in r[:-1] or r]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for i in range(grid):
        for j in range(grid):
            x, y = x0 + (i + 0.5) * (x1 - x0) / grid, y0 + (j + 0.5) * (y1 - y0) / grid
            if contains(rings, x, y):
                pts.append((x, y))
    return pts


def read_geojson(path):
    """Rings (lon, lat) of every polygon in a GeoJSON file, merged into one footprint."""
    data = json.loads(Path(path).expanduser().read_text())
    geoms = []

    def walk(obj):
        kind = obj.get("type")
        if kind == "FeatureCollection":
            for f in obj["features"]:
                walk(f)
        elif kind == "Feature":
            walk(obj["geometry"])
        elif kind == "GeometryCollection":
            for g in obj["geometries"]:
                walk(g)
        elif kind == "Polygon":
            geoms.extend(obj["coordinates"])
        elif kind == "MultiPolygon":
            for poly in obj["coordinates"]:
                geoms.extend(poly)
    walk(data)
    rings = [[[float(x), float(y)] for x, y, *_ in ring] for ring in geoms]
    if not rings:
        raise ValueError("no Polygon or MultiPolygon in the file")
    lon, lat = centroid(rings)
    if not (-92 < lon < -89 and 29 < lat < 31):
        raise ValueError(f"centre {lat:.4f}, {lon:.4f} is not near St. Charles Parish; GeoJSON must be lon, lat in WGS84")
    return rings


# ---------------------------------------------------------------- committee agendas

def flatten(items):
    """An event's agenda items as numbered lines, in agenda order."""
    lines = []
    for item in sorted(items, key=lambda i: (i.get("EventItemAgendaSequence") or 0)):
        for line in re.split(r"[\r\n]+", item.get("EventItemTitle") or ""):
            if line.strip():
                lines.append(line.strip())
    return lines


def strip_number(line):
    """Drop an agenda outline prefix such as '3.2.1.4.', 'IV.B.2.', '(a)', '1)' or 'A)'."""
    return re.sub(r"^(?:(?:[IVX]+|\d+|[A-Z])(?:\.(?:[IVX]+|\d+|[A-Za-z]))*\.?\s+|\(?[a-zA-Z0-9]{1,3}\)\s*)+", "", line).strip()


def parse_agenda(lines):
    """Permit rows from one meeting's agenda lines.

    Section comes from the nearest heading: 'open for public comment' rows are still in review and their
    code is the staff's proposed call; 'Last Month's ... Applications' rows carry the determination.
    """
    rows, section, concern = [], None, None
    for raw in lines:
        low = raw.lower()
        if "open for public comment" in low:
            section, concern = "open", None
            continue
        if "last month" in low and "application" in low:
            section, concern = "determined", None
        if "update on recent" in low or re.search(r"\badjourn", low):
            section = None
        m = re.search(r"\b(state|local) concerns?\b", low)
        if m and not PERMIT_RE.search(raw):
            concern = m.group(1).upper()
        permit, scp = PERMIT_RE.search(raw), SCP_RE.search(raw)
        if not (permit or scp):
            if rows and section and rows[-1]["section"] == section and not re.search(
                    r"concerns?|applications|briefing|update on", low):
                rows[-1]["text"] = (rows[-1]["text"] + " " + raw).strip()  # a description on its own line
            continue
        if section is None:
            continue
        text = strip_number(raw)
        tag = re.search(r"\((LOCAL|STATE)\)", raw, re.I)
        codes = []
        for c in CODE_RE.findall(text):
            c = c.upper()
            if c not in codes:
                codes.append(c)
        rows.append({"section": section, "concern": (tag.group(1).upper() if tag else concern),
                     "permit": permit.group(0) if permit else None, "scp": scp.group(0) if scp else None,
                     "codes": codes, "text": text})
    return rows


def load_czac(cache):
    def make():
        events = legistar("/events", **{"$filter": f"EventBodyId eq {CZAC_BODY}", "$orderby": "EventDate"})
        out = []
        for e in events:
            items = legistar(f"/events/{e['EventId']}/eventitems") if e.get("EventAgendaStatusName") != "Cancelled" else []
            out.append({"id": e["EventId"], "date": e["EventDate"][:10], "time": e.get("EventTime"),
                        "status": e.get("EventAgendaStatusName"), "comment": e.get("EventComment"),
                        "agenda": e.get("EventAgendaFile"), "minutes": e.get("EventMinutesFile"),
                        "lines": flatten(items)})
        return out
    return cache.get("czac_events", make)


def czac_rows(events):
    for e in events:
        for r in parse_agenda(e["lines"]):
            yield {**r, "date": e["date"], "event": e["id"]}


def cmd_czac(a):
    events = load_czac(Cache(a.cache, a.max_age, a.refresh))
    rows = [r for r in czac_rows(events) if r["date"] >= (a.since or "")]
    if a.permit:
        rows = [r for r in rows if a.permit.upper() in (r["permit"] or "", r["scp"] or "")]
    if a.term:
        rows = [r for r in rows if a.term.lower() in r["text"].lower()]
    if a.json:
        print(json.dumps(rows, indent=1))
        return 0 if rows else 1
    print(f"Coastal Zone Advisory Committee (Legistar body {CZAC_BODY}), {len(events)} meetings listed, "
          f"{events[0]['date'] if events else '-'} to {events[-1]['date'] if events else '-'}; read {dt.date.today()}.")
    for e in events:
        if e["status"] == "Cancelled" or not e["lines"]:
            why = e["comment"] or ("cancelled" if e["status"] == "Cancelled" else "no agenda items posted")
            if e["date"] >= (a.since or ""):
                print(f"  {e['date']}: {why}")
    if not rows:
        print("No permit rows match.")
        return 1
    last = None
    for r in rows:
        if r["date"] != last:
            print(f"\n{r['date']}  (event {r['event']}, https://stcharlesgov.legistar.com/MeetingDetail.aspx?ID={r['event']})")
            last = r["date"]
        ids = " / ".join(x for x in (r["permit"], r["scp"]) if x)
        where = "open for comment" if r["section"] == "open" else "determination"
        print(f"  {ids:24} {(r['concern'] or '?'):5}  {where:16}  {', '.join(r['codes']) or '-':18}  {r['text'][:150]}")
    print("\nCodes are copied from the agenda. NDSI = no direct and significant impact. 'Open for comment' rows"
          " show the staff's proposed call, not a decision. The determinations list follows the comment and"
          " appeal windows, so it is history, not notice: watch the Herald Guide for 'Notice of Pending Application'.")
    return 0


# ---------------------------------------------------------------- site

def resolve_place(a):
    """(label, shape) where shape is (lon, lat) or a list of rings."""
    if getattr(a, "geojson", None):
        return f"footprint from {Path(a.geojson).name}", read_geojson(a.geojson)
    if a.point:
        lat, lon = (float(x) for x in a.point.split(","))
        return f"point {lat:.6f}, {lon:.6f}", (lon, lat)
    cands = geocode(a.address)
    top = cands[0] if cands else None
    if not top or top["score"] < MIN_SCORE:
        print("No confident address match in the parish locator.")
        for c in cands:
            print(f"  {c['score']:5.1f}  {c['address']}")
        print("Rerun with the exact address shown, or with --point LAT,LON.")
        return None, None
    lon, lat = top["location"]["x"], top["location"]["y"]
    return f"{top['address']} (score {top['score']:.0f}) at {lat:.6f}, {lon:.6f}", (lon, lat)


def classify(samples, five_foot, fastlands):
    """Each sample point's class on the state map: 'fastland', the five-foot class, or None."""
    out = []
    for lon, lat in samples:
        cls = None
        if any(contains(f["rings"], lon, lat) for f in fastlands):
            cls = "fastland"
        else:
            for f in five_foot:
                if contains(f["rings"], lon, lat):
                    cls = f["a"].get("ELEVATION") or "five-foot layer"
                    break
        out.append(cls)
    return out


def exemption_screen(classes, is_point):
    """The words for R.S. 49:214.34(A)'s 'wholly' test, never stronger than the maps allow."""
    high = sum(1 for c in classes if c)
    if high == len(classes):
        lines = ["Every sampled point lies in a fastland or on land mapped 5 ft or more above sea level, so an "
                 "exemption under R.S. 49:214.34(A) may apply. OCM decides, and the secretary can still find a "
                 "direct and significant impact on coastal waters."]
        if is_point:
            lines.append("A single point cannot show that the whole activity is on such land. Rerun with the "
                         "footprint (--geojson), including access, staging and borrow areas.")
        return lines
    if high == 0:
        return ["No sampled point lies in a mapped fastland or on land mapped 5 ft or more, so the exemption for "
                "high land and fastlands does not appear to apply. A coastal use permit or a determination is needed."]
    return [f"{high} of {len(classes)} sampled points lie in a fastland or on land mapped 5 ft or more. The "
            "exemption needs the activity to be wholly on such land, so on the state's maps it does not appear "
            "to apply. OCM decides."]


def with_rings(features):
    return [{"a": f["attributes"], "rings": (f.get("geometry") or {}).get("rings", [])} for f in features]


def cmd_site(a):
    label, shape = resolve_place(a)
    if shape is None:
        return 1
    is_point = isinstance(shape, tuple)
    rings = None if is_point else shape
    lon, lat = shape if is_point else centroid(rings)
    geo = geometry_params(shape)
    print(f"Site: {label}\nRead {dt.date.today()} from the OCM map service and the parish GIS.\n")

    zone = query(ocm(OCM_ZONE), **geo, outFields="REVISION,UPDATE_")
    if zone:
        z = zone[0]["attributes"]
        print(f"State coastal zone: inside (State Coastal Zone Boundary, revision {z.get('REVISION')}, "
              f"updated {from_epoch_ms(z.get('UPDATE_'))}). The whole parish lies inside it (R.S. 49:214.24).")
    else:
        print("State coastal zone: outside the mapped boundary. Check the point; every part of the parish is inside.")

    five = with_rings(query(ocm(OCM_FIVE_FOOT), **geo, outFields="ELEVATION", returnGeometry="true"))
    fast = with_rings(query(ocm(OCM_FASTLANDS), **geo, returnGeometry="true",
                            outFields="NAME,PARISH,DATE_,STATUS,SOURCE,UPDATE_DATE"))
    samples = [shape] if is_point else sample_points(rings)
    classes = classify(samples, five, fast)
    if fast:
        for f in fast:
            x = f["a"]
            print(f"Fastland: {x.get('NAME')} ({x.get('PARISH')}), dated {from_epoch_ms(x.get('DATE_')) or 'none'}, "
                  f"STATUS {x.get('STATUS')}, SOURCE {x.get('SOURCE')}, last edited {from_epoch_ms(x.get('UPDATE_DATE')) or 'unknown'}")
        print("  The layer publishes no code list, so STATUS and SOURCE are printed as stored.")
    else:
        print("Fastland: none mapped here (OCM Fastlands layer).")
    kinds = sorted({c for c in classes if c and c != "fastland"})
    print(f"Five Foot Contour: {', '.join(kinds) if kinds else 'not in a mapped 5-to-7 ft or above-7 ft area'}"
          " (OCM layer; absence means below 5 ft or unmapped).")
    if not is_point:
        counts = {}
        for c in classes:
            counts[c or "neither"] = counts.get(c or "neither", 0) + 1
        print(f"  Footprint samples ({len(samples)} points: vertices plus an interior grid): "
              + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print()
    for line in exemption_screen(classes, is_point):
        print(line)
    print("Exempt and 'no direct and significant impact' findings by the parish go to OCM for concurrence (Sec. 26-6).\n")

    wet = query(WETLANDS_LAYER, **geo, outFields="attribute,wetland_ty")
    seen = sorted({(w["attributes"].get("wetland_ty"), w["attributes"].get("attribute")) for w in wet})
    print("Wetlands (parish copy of the National Wetlands Inventory): "
          + ("; ".join(f"{t} ({c})" for t, c in seen) if seen else "none mapped here"))
    print("  NWI is a screening map, not a jurisdictional delineation; the Corps decides Section 404 wetlands.")
    flood = query(DFIRM_LAYER, **geo, outFields="fld_zone,static_bfe,v_datum,sfha_tf")
    zones = sorted({(f["attributes"].get("fld_zone"), f["attributes"].get("static_bfe"), f["attributes"].get("v_datum"))
                    for f in flood})
    print("Flood zone (parish DFIRM layer): " + ("; ".join(
        f"{z}" + (f", BFE {b:g} ft {d}" if b is not None and b > -9000 else "") for z, b, d in zones) or "none"))
    pt = geometry_params((lon, lat))
    com = query(COMMUNITY_LAYER, **pt, outFields="name")
    dist = query(COUNCIL_LAYER, **pt, outFields="district")
    print(f"Community: {com[0]['attributes']['name'] if com else 'outside the parish community polygons'}; "
          f"council district: {dist[0]['attributes']['district'] if dist else 'none'}"
          + ("" if is_point else " (at the footprint's centre)"))
    if is_point:
        try:
            e = fetch_json(EPQS + "?" + urllib.parse.urlencode({"x": lon, "y": lat, "wkid": 4326, "units": "Feet"}))
            val = float(e.get("value"))
            if val > -1000:
                print(f"Ground elevation (USGS 3DEP): {val:.1f} ft NAVD88. Context only: the exemption test uses the "
                      "secretary's map and mean sea level, not a single LiDAR cell.")
        except (SourceError, TypeError, ValueError):
            print("Ground elevation (USGS 3DEP): not available.")
    print("Environmental Management Unit: not in any queryable layer for St. Charles. Read the EMU maps in "
          "the Local Coastal Program, chapter 6 (corpus/), and say the placement is read from a figure.")
    return 0


# ---------------------------------------------------------------- permits near a place and one permit

def permit_year(number):
    m = re.match(r"P(\d{4})", number or "")
    return int(m.group(1)) if m else None


def gather_permits(features, kind, lon, lat):
    """One row per permit number with its nearest distance, from points, polygons or lines."""
    out = {}
    for f in features:
        x, g = f["attributes"], f.get("geometry") or {}
        number = (x.get("CUPNO") or x.get("DOCNO") or "").strip()
        if not number:
            continue
        if "x" in g:
            d = metres_to([[[g["x"], g["y"]]]], lon, lat, closed=False)
        elif "rings" in g:
            d = metres_to(g["rings"], lon, lat, closed=True)
        else:
            d = metres_to(g.get("paths", []), lon, lat, closed=False)
        row = out.setdefault(number, {"permit": number, "kinds": set(), "metres": d, "acres": None,
                                      "company": None, "status": None, "issued": None})
        row["kinds"].add(kind)
        row["metres"] = min(row["metres"], d)
        row["acres"] = x.get("ACRES") or row["acres"]
        row["company"] = x.get("COMPANY") or row["company"]
        row["status"] = x.get("PERMIT_STATUS") or row["status"]
        row["issued"] = from_epoch_ms(x.get("DOCISSUDT")) or row["issued"]
    return out


def merge(*groups):
    merged = {}
    for g in groups:
        for k, r in g.items():
            if k in merged:
                merged[k]["kinds"] |= r["kinds"]
                merged[k]["metres"] = min(merged[k]["metres"], r["metres"])
                for f in ("acres", "company", "status", "issued"):
                    merged[k][f] = merged[k][f] or r[f]
            else:
                merged[k] = r
    return merged


def paged(layer, **params):
    out, offset = [], 0
    while True:
        batch = query(layer, **params, resultOffset=offset, resultRecordCount=1000)
        out += batch
        if len(batch) < 1000:
            return out
        offset += 1000


def cmd_near(a):
    label, shape = resolve_place(a)
    if shape is None:
        return 1
    lon, lat = shape if isinstance(shape, tuple) else centroid(shape)
    geo = {**geometry_params((lon, lat)), "distance": a.radius, "units": "esriSRUnit_Meter", "returnGeometry": "true"}
    rows = merge(
        gather_permits(paged(ocm(OCM_POINTS), **geo, outFields="CUPNO"), "point", lon, lat),
        gather_permits(paged(ocm(OCM_POLYGONS), **geo, outFields="CUPNO,ACRES"), "polygon", lon, lat),
        gather_permits(paged(ocm(OCM_LINES), **geo, outFields="DOCNO,COMPANY,PERMIT_STATUS,DOCISSUDT"), "line", lon, lat))
    rows = [r for r in rows.values() if (permit_year(r["permit"]) or 0) >= a.since]
    rows.sort(key=lambda r: r["permit"], reverse=True)
    print(f"Coastal use permits mapped by OCM within {a.radius:g} m of {label}"
          f"{f', {a.since} on' if a.since else ''}: {len(rows)}. Read {dt.date.today()}.")
    for r in rows:
        extra = "; ".join(x for x in (f"{r['acres']:g} ac" if r["acres"] else "", r["company"] or "",
                                       r["status"] or "", f"issued {r['issued']}" if r["issued"] else "") if x)
        print(f"  {r['permit']}  {r['metres']:6.0f} m  {'/'.join(sorted(r['kinds'])):14}  {extra}")
    print("\nThe map holds state and parish permits alike under P-numbers. The line layer's company, status and"
          " issue date stop in 2023. A permit's description is in its SONRIS documents: "
          + SONRIS_DOCS.format("<P-number>"))
    return 0 if rows else 1


def cmd_permit(a):
    number = a.number.upper()
    if not PERMIT_RE.fullmatch(number):
        print("A coastal use permit number looks like P20260816.")
        return 1
    where = f"CUPNO='{number}'"
    found = []
    for layer, kind, fields in ((OCM_POLYGONS, "polygon", "CUPNO,ACRES"), (OCM_POINTS, "point", "CUPNO")):
        for f in query(ocm(layer), where=where, outFields=fields, returnGeometry="true"):
            found.append((kind, f))
    for f in query(ocm(OCM_LINES), where=f"DOCNO='{number}'", outFields="COMPANY,PRODUCT,PERMIT_STATUS,DOCISSUDT",
                   returnGeometry="true"):
        found.append(("line", f))
    print(f"{number}, read {dt.date.today()}")
    print(f"SONRIS documents: {SONRIS_DOCS.format(number)}")
    if found:
        pts = []
        for kind, f in found:
            g = f.get("geometry") or {}
            parts = g.get("rings") or g.get("paths") or ([[[g["x"], g["y"]]]] if "x" in g else [])
            pts += [p for part in parts for p in part]
        lon, lat = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        kinds = sorted({k for k, _ in found})
        acres = sum(f["attributes"].get("ACRES") or 0 for k, f in found if k == "polygon")
        print(f"OCM map: {len(found)} feature(s) ({', '.join(kinds)}), centre {lat:.6f}, {lon:.6f}"
              + (f", {acres:g} acres mapped" if acres else ""))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) - min(xs) > 0.05 or max(ys) - min(ys) > 0.05:  # a pipeline or multi-parish permit
            print(f"  Spans {min(ys):.4f} to {max(ys):.4f} N, {min(xs):.4f} to {max(xs):.4f} W; the centre may be outside the parish.")
        lines = {(f["attributes"].get("COMPANY"), f["attributes"].get("PRODUCT"), f["attributes"].get("PERMIT_STATUS"),
                  from_epoch_ms(f["attributes"].get("DOCISSUDT"))) for k, f in found if k == "line"}
        for company, product, status, issued in sorted(lines, key=str):
            print(f"  line: {company}, {product}, {status}, issued {issued}")
        pt = geometry_params((lon, lat))
        com = query(COMMUNITY_LAYER, **pt, outFields="name")
        print(f"  Community at the centre: {com[0]['attributes']['name'] if com else 'outside the parish community polygons'}")
    else:
        print("OCM map: not mapped (yet). New applications can take weeks to appear.")
    try:
        rows = [r for r in czac_rows(load_czac(Cache(a.cache, a.max_age, a.refresh))) if r["permit"] == number]
    except SourceError as exc:
        print(f"Committee agendas: unavailable ({exc})")
        rows = None
    if rows:
        print("Coastal Zone Advisory Committee agendas:")
        for r in rows:
            where = "open for comment" if r["section"] == "open" else "determination"
            print(f"  {r['date']}  {r['concern'] or '?':5}  {where:16}  {', '.join(r['codes']) or '-':18}  {r['text'][:150]}")
    elif rows is not None:
        print("Coastal Zone Advisory Committee agendas: not listed (agendas on Legistar begin 2025-07-10).")
    print("If the SONRIS link times out, use bayou:sonris-doc-search if installed, or open it in a browser.")
    return 0


# ---------------------------------------------------------------- clock

def government_module():
    path = SKILLS / "scp-government" / "scripts" / "government.py"
    spec = importlib.util.spec_from_file_location("scp_government", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clock_rows(triggers, holidays):
    """(label, due date, source, note) for every period whose trigger date was given."""
    out = []
    for label, trigger, days, source in CLOCKS:
        start = triggers.get(trigger)
        if not start:
            continue
        due = start + dt.timedelta(days=days)
        note = ""
        if due.weekday() >= 5 or due in holidays:
            nxt = due
            while nxt.weekday() >= 5 or nxt in holidays:
                nxt += dt.timedelta(days=1)
            why = holidays.get(due) or due.strftime("%A")
            note = f"falls on {why}; next working day {nxt:%a %Y-%m-%d}"
        out.append((label, due, source, note))
    return out


def cmd_clock(a):
    triggers = {k: dt.date.fromisoformat(v) for k, v in (("notice", a.notice), ("decision", a.decision),
                                                         ("activity", a.activity)) if v}
    if not triggers:
        print("Give at least one of --notice, --decision or --activity (YYYY-MM-DD).")
        return 1
    holidays = {}
    try:
        gov = government_module()
        for year in {d.year for d in triggers.values()} | {d.year + 1 for d in triggers.values()}:
            holidays.update(gov.legal_holidays(year)[0])
    except Exception:  # scp-government missing from a partial install: weekends are still flagged
        pass
    for k, v in triggers.items():
        print(f"{k:9} {v:%a %Y-%m-%d}")
    print()
    for label, due, source, note in clock_rows(triggers, holidays):
        print(f"{due:%a %Y-%m-%d}  {label}\n              {source}" + (f"\n              {note}" if note else ""))
    print("\nConvention of this skill, not a legal ruling: calendar days, the trigger day not counted. Chapter 26"
          " does not say whether a period ending on a weekend or holiday moves. File early, and ask the parish"
          " Coastal Zone Management office in writing how it counts. Court review periods (Sec. 26-9(r)(2) and"
          " (w)(3)) are in references/program.md, quoted, not computed.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=str(DEFAULT_CACHE))
    ap.add_argument("--max-age", type=float, default=1, help="days before cached agendas are fetched again")
    ap.add_argument("--refresh", action="store_true")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("czac"); p.add_argument("--since"); p.add_argument("--term"); p.add_argument("--permit")
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_czac)
    p = sp.add_parser("site"); p.add_argument("address", nargs="?"); p.add_argument("--point")
    p.add_argument("--geojson"); p.set_defaults(fn=cmd_site)
    p = sp.add_parser("near"); p.add_argument("address", nargs="?"); p.add_argument("--point")
    p.add_argument("--radius", type=float, default=1000); p.add_argument("--since", type=int, default=0)
    p.set_defaults(fn=cmd_near)
    p = sp.add_parser("permit"); p.add_argument("number"); p.set_defaults(fn=cmd_permit)
    p = sp.add_parser("clock"); p.add_argument("--notice"); p.add_argument("--decision"); p.add_argument("--activity")
    p.set_defaults(fn=cmd_clock)
    a = ap.parse_args(argv)
    if a.cmd in ("site", "near") and not (a.address or a.point or getattr(a, "geojson", None)):
        ap.error(f"{a.cmd} needs an address, --point LAT,LON" + (" or --geojson FILE" if a.cmd == "site" else ""))
    try:
        return a.fn(a)
    except SourceError as exc:
        print(f"Source unavailable: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main())
