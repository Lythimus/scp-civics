#!/usr/bin/env python3
"""St. Charles Parish facility roster from LDEQ, EPA ECHO, EPA FRS and RMP records.

  roster [--md FILE]            industrial sites, LDEQ AI joined to EPA IDs (slow: ~2 minutes)
  find TERM [--neighbors]       every LDEQ AI matching a name, address or ID
  near LAT LON [--km N] [--all] LDEQ AIs by distance from a point

Records show that a site is registered, not that it is operating or that it
caused anything. Stdlib only.
"""

import argparse
import concurrent.futures
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

FIPS = "22089"
UA = "Mozilla/5.0 (scp-civics facility roster)"  # EDMS answers 403 to urllib's default agent
EDMS = "https://edms.deq.louisiana.gov/edmsv2/aiSearch/filter"
ECHO = "https://echodata.epa.gov/echo/echo_rest_services.get_facility_info"
FRS = "https://data.epa.gov/efservice/FRS_PROGRAM_FACILITY/REGISTRY_ID/{}/JSON"
RMP = "https://data-liberation-project.github.io/epa-rmp-viewer/data/facilities/by-state/LA.json"

# Refining, chemicals, industrial gases, power, bulk storage and pipelines. A code
# list anyone can check keeps the roster to companies: the full AI list also holds
# private people's names, on complaint and dump-site records.
INDUSTRIAL_SICS = {
    "1321", "2812", "2813", "2819", "2821", "2822", "2865", "2869", "2873", "2899",
    "2911", "2951", "2999", "4226", "4612", "4613", "4619", "4911", "4922", "5169",
}
LDEQ_TYPES = {
    "Chemicals And Allied Products",
    "Petroleum Refining And Related Industries",
    "Pipelines, Except Natural Gas",
}
NEAR_TYPES = LDEQ_TYPES | {
    "Electric, Gas, And Sanitary Services",
    "Motor Freight Transportation And Warehousing",
    "Food And Kindred Products",
    "Oil And Gas Extraction",
}
# The type code for power plants also covers septic and dump records, so these are named.
EXTRA_AIS = {"35260", "83898", "687", "197303", "248424", "2720", "4885", "227637", "1738"}
# ECHO's FIPS query returns these for rows whose mailing or plotted point is elsewhere.
PARISH_TOWNS = {
    "AMA", "BAYOU GAUCHE", "BOUTTE", "DES ALLEMANDS", "DESTREHAN", "GOOD HOPE", "HAHNVILLE",
    "KILLONA", "LAKE SALVADOR", "LULING", "MONTZ", "NEW SARPY", "NORCO", "PARADIS", "SAINT ROSE",
    "SAINT CHARLES PARISH", "ST ROSE", "ST. ROSE", "TAFT",
}
# Dropped from street names so spellings of one road compare equal.
ROAD_NOISE = {"E", "N", "S", "W", "EAST", "WEST", "LA", "LOUISIANA", "US", "U", "HWY", "HIGHWAY"}
# Too common in LDEQ and EPA names to show that a record is in a company's own name.
NAME_NOISE = {"THE", "INC", "LLC", "CORP", "SAINT", "CHARLES", "CHEMICAL", "PLANT"}


def fetch(url, data=None, tries=3):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == tries - 1:
                raise RuntimeError(f"{url}: {exc}") from exc
            time.sleep(2 * (attempt + 1))


def ldeq_ais():
    rows, start = [], 0
    while True:
        body = {
            "filter": {"keywordSearchType": "Name", "fuzzyMatch": True, "keyword": "*"},
            "refinerFilter": {
                "regions": [], "regionIds": [], "parishes": ["St. Charles"],
                "cities": [], "typeNames": [], "typeCodes": [],
            },
            "start": start, "rows": 200, "sort": "name", "asc": True, "highlight": False,
        }
        page = fetch(EDMS, json.dumps(body).encode())["data"]
        if not page:
            return rows
        rows += page
        start += len(page)


def echo_active():
    query = urllib.parse.urlencode({"output": "JSON", "p_fips": FIPS, "p_act": "Y"})
    return fetch(f"{ECHO}?{query}")["Results"].get("Facilities") or []


def rmp_rows():
    for county in fetch(RMP)["counties"]:
        if county["fips"] == FIPS:
            return county["facilities"]
    return []


def frs_ids(registry):
    return {r["pgm_sys_id"] for r in fetch(FRS.format(registry)) if r.get("pgm_sys_id")}


def id_forms(value):
    """Spellings of one permit ID. FRS writes air IDs as LA0000002208900027; LDEQ as 2208900027."""
    value = value.strip().upper()
    forms = {value}
    match = re.search(r"(22089\d{5})$", value)
    if match:
        forms.add(match.group(1))
    return forms


def join_key(street):
    """House number plus road name, for addresses agencies spell differently.

    "355 Highway 3142", "355 Louisiana Hwy 3142" and "355 HWY. 3142" are one place, and so
    are "12501B River Road" and "12501 River Rd". An RMP address can lead with a
    non-street part, as in "La. Highways 18 and 3142 • 355 Hwy 3142".
    """
    for part in re.split(r"[•\n]", (street or "").upper()):
        match = re.match(r"\s*(\d+)(?![\d.])(?:[A-Z](?=[\s-]))?(?:-[A-Z])?\s*(?=[A-Z0-9])(.*)", part)
        if not match:
            continue
        words = [w for w in re.findall(r"[A-Z0-9]+", match.group(2)) if w not in ROAD_NOISE]
        if words:
            return f"{match.group(1)} {words[0]}"
    return ""


def site_address(ai):
    """Street line, with 'portion of' dropped, so co-located AIs group together."""
    line = (ai.get("physicalAddress") or "").split("\n")[0]
    return re.sub(r",?\s*\(?(a )?portion of\)?.*$", "", line, flags=re.I).strip()


def looks_like_company(ai):
    return not re.match(r"(Incident\b|T\d{5,})", ai["name"])


def in_roster(ai):
    return ai["id"] in EXTRA_AIS or (ai["typeName"] in LDEQ_TYPES and looks_like_company(ai))


def site_key(ai):
    return join_key(ai.get("physicalAddress")) or site_address(ai)


def echo_selected(row, rmp_keys):
    sics = set(re.findall(r"\d{4}", row.get("FacSICCodes") or ""))
    return bool(
        row.get("TRIIDs") or row.get("GHGFlag") == "Y" or sics & INDUSTRIAL_SICS
        or join_key(row.get("FacStreet")) in rmp_keys
    )


def company_word(name):
    for word in re.findall(r"[A-Z0-9&]+", name.upper()):
        if len(word) >= 3 and word not in NAME_NOISE:
            return word
    return ""


def own_record(ai_name, echo_name):
    """A shared registry speaks for a tenant only if EPA's name for it is that company's."""
    word = company_word(ai_name)
    return bool(word) and word in re.findall(r"[A-Z0-9&]+", echo_name.upper())


def join(ais, echo, program_ids):
    """Link ECHO rows to AIs on any shared permit ID, then on address. Returns {registry: (ais, how)}."""
    by_id, by_addr = {}, {}
    for ai in ais:
        for raw in ai["alternateIds"]:
            for form in id_forms(raw):
                by_id.setdefault(form, set()).add(ai["id"])
        key = join_key(ai.get("physicalAddress"))
        if key:
            by_addr.setdefault(key, set()).add(ai["id"])
    out = {}
    for row in echo:
        registry = row["RegistryID"]
        ids = set(program_ids.get(registry, ())) | set((row.get("TRIIDs") or "").split())
        matched = set()
        for raw in ids:
            for form in id_forms(raw):
                matched |= by_id.get(form, set())
        if matched:
            out[registry] = (matched, "ID")
        elif join_key(row.get("FacStreet")) in by_addr:
            out[registry] = (by_addr[join_key(row["FacStreet"])], "address")
        else:
            out[registry] = (set(), "")
    return out


def build_roster():
    ais = ldeq_ais()
    echo = echo_active()
    rmp = rmp_rows()
    # Only live filings: a long-deregistered one would pull in anything sharing its address.
    rmp_keys = {join_key(r.get("address")) for r in rmp
                if not (r.get("sub_last") or {}).get("date_dereg")} - {""}

    outside = [r for r in echo if (r.get("FacCity") or "").upper() not in PARISH_TOWNS]
    inside = [r for r in echo if r not in outside and echo_selected(r, rmp_keys)]
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        program_ids = dict(zip(
            (r["RegistryID"] for r in inside),
            pool.map(lambda r: frs_ids(r["RegistryID"]), inside),
        ))
    links = join(ais, inside, program_ids)

    by_ai = {a["id"]: a for a in ais}
    rows = {a["id"]: {"ai": a, "echo": []} for a in ais if in_roster(a)}
    unjoined = []
    for row in inside:
        matched, how = links[row["RegistryID"]]
        if how == "address" and len(matched) > 1:
            unjoined.append(row)  # an address alone can't pick among co-located AIs
            continue
        if not matched:
            unjoined.append(row)
        for ai_id in matched:
            rows.setdefault(ai_id, {"ai": by_ai[ai_id], "echo": []})
            rows[ai_id]["echo"].append({"row": row, "how": how, "shared": len(matched) > 1})
    groups = {}
    for entry in rows.values():
        groups.setdefault(site_key(entry["ai"]), []).append(entry)
    return groups, unjoined, outside, rmp, len(ais), len(echo)


def status_cell(entry):
    if not entry["echo"]:
        return "LDEQ AI only"
    name = entry["ai"]["name"]
    direct = [x for x in entry["echo"]
              if not x["shared"] or own_record(name, x["row"]["FacName"])]
    if not direct:
        return "On a shared EPA record, not in this company's name"
    if {x["how"] for x in direct} == {"address"}:
        return "EPA active (joined by address)"
    return "EPA active"


def echo_cell(entry):
    seen = {x["row"]["RegistryID"]: x for x in entry["echo"]}
    return "; ".join(
        f"{k} {seen[k]['row']['FacName'].strip()}" + (" (shared)" if seen[k]["shared"] else "")
        for k in sorted(seen)
    ) or "-"


def rmp_label(facility):
    sub = facility.get("sub_last") or {}
    dereg = sub.get("date_dereg")
    return (f"{facility['EPAFacilityID']} {facility.get('name', '').strip()} "
            f"(validated {sub.get('date_val')}" + (f"; deregistered {dereg})" if dereg else ")"))


def heading(entries):
    names = [site_address(e["ai"]) for e in entries]
    names = [n for n in names if len(n) > 3]
    return min(names, key=len) if names else "No street address"


def markdown(groups, unjoined, outside, rmp, n_ai, n_echo, today):
    out = [
        "# St. Charles Parish facility roster",
        "",
        f"Generated {today} by `scripts/facilities.py roster --md`. Don't edit by hand; rebuild it.",
        "",
        f"Sources: LDEQ EDMS AI search ({n_ai} AIs in the parish), EPA ECHO active facilities for FIPS "
        f"{FIPS} ({n_echo} rows), EPA FRS program IDs for the selected rows, and RMP filings "
        "from the Data Liberation Project's FOIA copy of EPA's database.",
        "",
        "**How to read it.**",
        "",
        "- A row means a site is registered, not that it is operating. The names are the agencies' "
        "and can lag a sale, so EPA's name for a record can be a past owner's.",
        "- **EPA active:** ECHO lists an active permit or program on a record that is this AI's "
        "alone or in this company's name. A permit can outlast production.",
        "- **On a shared EPA record, not in this company's name:** EPA tracks a whole complex under one "
        "registry ID, marked (shared), and this AI shares a permit ID with it. That says nothing about "
        "this tenant's own status.",
        "- **LDEQ AI only:** no selected ECHO record links here. It can be a new, proposed, closed or "
        "renamed site, so check it with `bayou:ldeq-permit-status` or LDEQ's Check Permit Status page.",
        "- **joined by address:** no shared permit ID, only a matching street number and name. Confirm it.",
        "- **RMP filings** are listed by address and aren't assigned to a company, because several "
        "companies can share an address. Read the filing's own name.",
        "- Selected by rule: LDEQ's chemical, refining and pipeline types, a short list of named power "
        "and terminal sites, and ECHO rows with a TRI ID, a greenhouse gas flag, an industrial SIC code or a "
        "live RMP filing at the address. A site outside that rule isn't here, so use `find`.",
        "",
    ]
    filings = {}
    for facility in rmp:
        filings.setdefault(join_key(facility.get("address")), []).append(facility)

    def filing_text(key):
        return "; ".join(rmp_label(f) for f in sorted(filings.get(key, []), key=lambda f: f["EPAFacilityID"]))

    shared = sorted((k for k in groups if len(groups[k]) > 1), key=lambda k: (-len(groups[k]), k))
    single = sorted((k for k in groups if len(groups[k]) == 1),
                    key=lambda k: heading(groups[k]).lower())
    out += ["## Addresses with more than one LDEQ AI", ""]
    for key in shared:
        out += [f"### {heading(groups[key])}", "",
                "| LDEQ AI | LDEQ name | EPA registry ID and name | Records |", "|---|---|---|---|"]
        for entry in sorted(groups[key], key=lambda e: e["ai"]["name"]):
            ai = entry["ai"]
            out.append(f"| {ai['id']} | {ai['name']} | {echo_cell(entry)} | {status_cell(entry)} |")
        out.append("")
        if filing_text(key):
            out += [f"RMP filings at this address: {filing_text(key)}.", ""]
    out += ["## Addresses with one LDEQ AI", "",
            "| Address | LDEQ AI | LDEQ name | EPA registry ID and name | Records | RMP filings at this address |",
            "|---|---|---|---|---|---|"]
    for key in single:
        entry = groups[key][0]
        ai = entry["ai"]
        out.append(f"| {heading(groups[key])} | {ai['id']} | {ai['name']} | {echo_cell(entry)} "
                   f"| {status_cell(entry)} | {filing_text(key) or '-'} |")
    out.append("")
    loose = [f for f in rmp if join_key(f.get("address")) not in groups]
    if loose:
        out += ["## RMP filings with no roster address", "",
                "RMP addresses are the filer's, and many differ from LDEQ's for the same plant.", "",
                "| RMP filing | Address |", "|---|---|"]
        for facility in sorted(loose, key=lambda f: f.get("name", "")):
            address = (facility.get("address") or "").replace("•", "/")
            out.append(f"| {rmp_label(facility)} | {address} |")
        out.append("")
    if unjoined:
        out += ["## EPA rows with no single LDEQ match", "",
                "| EPA registry ID | EPA name | Address |", "|---|---|---|"]
        for row in sorted(unjoined, key=lambda r: r["FacName"]):
            out.append(f"| {row['RegistryID']} | {row['FacName']} | {row['FacStreet']}, {row['FacCity']} |")
        out.append("")
    out += ["## Left out", "",
            f"{len(outside)} of ECHO's parish rows name a town outside the parish, or none, so they "
            "weren't selected. Check any you need by hand: " +
            ", ".join(sorted({(r.get('FacCity') or 'blank').title() for r in outside})) + ".", ""]
    return "\n".join(out)


def cmd_roster(args):
    built = build_roster()
    text = markdown(*built, today=time.strftime("%Y-%m-%d"))
    if args.md:
        with open(args.md, "w", encoding="utf-8") as fh:
            fh.write(text)
        groups = built[0]
        print(f"{sum(len(v) for v in groups.values())} sites at {len(groups)} addresses: {args.md}")
    else:
        print(text)


def print_ai(ai, suffix=""):
    address = (ai.get("physicalAddress") or "").replace("\n", ", ")
    print(f"{ai['id']:>7}  {ai['name']}\n         {address} | {ai['typeName']}{suffix}")


def cmd_find(args):
    term = args.term.lower()
    ais = ldeq_ais()
    hits = [a for a in ais if term in a["name"].lower()
            or term in (a.get("physicalAddress") or "").lower()
            or any(term == x.lower() for x in a["alternateIds"])]
    print(f"{len(hits)} of {len(ais)} LDEQ AIs in St. Charles Parish match {args.term!r}. "
          "LDEQ names lag sales, so try the old owner and the address too.")
    for ai in hits:
        print_ai(ai)
    if args.neighbors:
        for key in sorted({site_key(a) for a in hits if site_key(a)}):
            near = [a for a in ais if site_key(a) == key and a not in hits]
            if near:
                print(f"\nAlso at {site_address(near[0])}:")
                for ai in near:
                    print_ai(ai)


def distance_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def cmd_near(args):
    rows = []
    for ai in ldeq_ais():
        if ai.get("latitude") is None or ai.get("longitude") is None:
            continue
        if not args.all and (ai["typeName"] not in NEAR_TYPES or not looks_like_company(ai)):
            continue
        km = distance_km(args.lat, args.lon, ai["latitude"], ai["longitude"])
        if km <= args.km:
            rows.append((km, ai))
    print(f"{len(rows)} LDEQ AIs within {args.km} km, by LDEQ's plotted point. Distance doesn't "
          "show a source; a point can be a gate or an old office, and wind decides what reaches you.")
    for km, ai in sorted(rows, key=lambda r: r[0]):
        print_ai(ai, f" | {km:.1f} km")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    roster = sub.add_parser("roster")
    roster.add_argument("--md")
    find = sub.add_parser("find")
    find.add_argument("term")
    find.add_argument("--neighbors", action="store_true")
    near = sub.add_parser("near")
    near.add_argument("lat", type=float)
    near.add_argument("lon", type=float)
    near.add_argument("--km", type=float, default=5)
    near.add_argument("--all", action="store_true", help="every AI type, which can include people's names")
    args = parser.parse_args()
    try:
        {"roster": cmd_roster, "find": cmd_find, "near": cmd_near}[args.cmd](args)
    except RuntimeError as exc:
        sys.exit(f"source unavailable: {exc}")


if __name__ == "__main__":
    main()
