#!/usr/bin/env python3
"""Who represents an address, which parish bodies meet, and whether one meeting's notice looks timely.

  government.py district "15045 River Rd, Hahnville"   council district, precinct, school board,
  government.py district --point 29.9634,-90.4070        state House and Senate, polling place
  government.py bodies [--months 12]                     Legistar bodies: meetings, last, next
  government.py notice --event 1994                      Open Meetings Law timing for one meeting
  government.py notice --body Planning --date 2026-11-05 [--holiday 2026-02-17]

district sends the address to the parish's own geocoder at maps.scpgis.com and nothing else, and
caches nothing. notice reports indicators, not violations: Legistar's agenda timestamp dates only the
website copy, and only its last publication, while R.S. 42:19 is met by the notice posted at the
office or published in the journal. Each finding is a question for the custodian.

Exit codes: 0 answered, 1 no match, 2 a source could not be reached. Stdlib only; pdftotext
(poppler), if installed, is used to read minutes.
"""
import argparse, collections, datetime as dt, json, re, shutil, subprocess, sys, time
import urllib.parse, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True  # the plugin folder may be a read-only snapshot
API = "https://webapi.legistar.com/v1/stcharlesgov"
GIS = "https://maps.scpgis.com/geoserver/rest/services"
GEOCODER = f"{GIS}/Address_Point_Locator/GeocodeServer/findAddressCandidates"
LAYERS = f"{GIS}/Public/GIS_Data/MapServer"
COUNCIL_LAYER, COMMUNITY_LAYER, FIRE_LAYER, PRECINCT_LAYER = 4, 2, 6, 7
ROSTER = Path(__file__).resolve().parents[2] / "scp-meeting-record" / "references" / "officials.md"
UA = {"User-Agent": "scp-civics/0.1 (public records research)"}
CENTRAL = ZoneInfo("America/Chicago")
MIN_SCORE = 90
# Legistar bodies that are staff, members or room bookings rather than public bodies that meet.
NOT_MEETING_BODIES = {"Council Secretary", "Council Member(s)", "Council Chairman", "SCP General Chamber Booking"}
CHAMBER_BOOKING = "SCP General Chamber Booking"
# The latest reapportionment and boundary change found on Legistar, checked 2026-11-17.
DISTRICT_ORDINANCES = ("Ord. 22-12-12 (reapportionment after the 2020 census)",
                       "Ord. 26-2-3 (passed 2026-02-09; revised Districts 1 and 7 south of Tinney Street)")
# Precinct fields kept, in print order. The layer also carries party vote totals, left out on purpose.
PRECINCT_FIELDS = (("name", "Precinct"), ("pj", "Council district on the precinct record"),
                   ("sb", "School Board district"), ("rep", "State House district"),
                   ("sen", "State Senate district"), ("con", "Congressional district"),
                   ("psc", "Public Service Commission district"), ("bese", "BESE district"),
                   ("pp", "Polling place"), ("pl", "Polling place address"))


class SourceError(Exception):
    pass


def fetch(url, tries=3):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as exc:  # the Legistar API and the parish GIS both drop requests at times
            if attempt == tries - 1:
                raise SourceError(f"{url.split('?')[0]}: {exc}") from exc
            time.sleep(2 * (attempt + 1))


def fetch_json(url):
    data = json.loads(fetch(url))
    if isinstance(data, dict) and data.get("error"):
        raise SourceError(f"{url.split('?')[0]}: {data['error']}")
    return data


def legistar(path, **params):
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe="$'(),")
    return fetch_json(f"{API}{path}" + (f"?{query}" if query else ""))


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def from_epoch_ms(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).astimezone(CENTRAL) if ms else None


# ---------------------------------------------------------------- holidays and the 24-hour window

def easter(year):
    """Gregorian Easter Sunday (anonymous algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    g = (b - (b + 8) // 25 + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return dt.date(year, month, day + 1)


def nth_weekday(year, month, weekday, n):
    first = dt.date(year, month, 1)
    return first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def last_weekday(year, month, weekday):
    last = dt.date(year + month // 12, month % 12 + 1, 1) - dt.timedelta(days=1)
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def legal_holidays(year):
    """R.S. 1:55(A)(1) and (4) legal holidays for one year as {date: name}, plus conditional ones.

    Conditional days count only if the parish declares them by ordinance: Mardi Gras under
    1:55(A)(3), and the Friday before a Saturday Christmas, New Year's Day or July 4 under 1:55(A)(4).
    Whether St. Charles has declared them isn't established, so callers show both readings.
    """
    fixed = {dt.date(year, 1, 1): "New Year's Day", dt.date(year, 1, 8): "Battle of New Orleans",
             dt.date(year, 7, 4): "Independence Day", dt.date(year, 8, 30): "Huey P. Long Day",
             dt.date(year, 11, 1): "All Saints' Day", dt.date(year, 11, 11): "Veterans' Day",
             dt.date(year, 12, 25): "Christmas Day"}
    days = dict(fixed)
    days[nth_weekday(year, 1, 0, 3)] = "Dr. Martin Luther King, Jr.'s Birthday"
    days[nth_weekday(year, 2, 0, 3)] = "Washington's Birthday"
    days[easter(year) - dt.timedelta(days=2)] = "Good Friday"
    days[last_weekday(year, 5, 0)] = "National Memorial Day"
    days[nth_weekday(year, 9, 0, 1)] = "Labor Day"
    days[nth_weekday(year, 10, 0, 2)] = "Christopher Columbus Day"
    days[nth_weekday(year, 11, 3, 4)] = "Thanksgiving Day"
    conditional = {easter(year) - dt.timedelta(days=47): "Mardi Gras (if declared by parish ordinance)"}
    for day in (dt.date(year, 1, 1), dt.date(year, 7, 4), dt.date(year, 12, 25)):
        if day.weekday() == 6:
            days[day + dt.timedelta(days=1)] = f"{fixed[day]}, observed"
        elif day.weekday() == 5:
            conditional[day - dt.timedelta(days=1)] = f"{fixed[day]}, observed (if declared by parish ordinance)"
    return days, conditional


def holidays_around(day, extra=()):
    days, conditional = {}, {}
    for year in (day.year - 1, day.year):
        d, c = legal_holidays(year)
        days.update(d)
        conditional.update(c)
    days.update({x: "given with --holiday" for x in extra})
    return days, conditional


def notice_deadline(start, holidays, hours=24):
    """The latest moment notice could go up: `hours` before `start`, skipping excluded days.

    R.S. 42:19 counts "twenty-four hours, exclusive of Saturdays, Sundays, and legal holidays". This
    walks back a calendar day at a time and counts only the part of each countable day before the
    running end point. Hours are wall-clock hours, so a daylight-saving change shifts the result by
    an hour on those two nights a year.
    """
    remaining = dt.timedelta(hours=hours)
    day, end = start.date(), start
    while True:
        day_start = dt.datetime.combine(day, dt.time(0), tzinfo=start.tzinfo)
        if day.weekday() < 5 and day not in holidays:
            available = end - day_start
            if available >= remaining:
                return end - remaining
            remaining -= available
        end = day_start  # midnight ends the previous day
        day -= dt.timedelta(days=1)


# ---------------------------------------------------------------- district

def geocode(address):
    url = GEOCODER + "?" + urllib.parse.urlencode(
        {"SingleLine": address, "outSR": 4326, "maxLocations": 5, "f": "json"})
    return fetch_json(url).get("candidates", [])


def layer_at(layer, lon, lat):
    params = {"geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}),
              "geometryType": "esriGeometryPoint", "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
              "outFields": "*", "returnGeometry": "false", "f": "json"}
    data = fetch_json(f"{LAYERS}/{layer}/query?" + urllib.parse.urlencode(params))
    return [f["attributes"] for f in data.get("features", [])]


def layer_edited(layer):
    params = {"where": "1=1", "outFields": "last_edited_date", "returnGeometry": "false", "f": "json"}
    rows = fetch_json(f"{LAYERS}/{layer}/query?" + urllib.parse.urlencode(params)).get("features", [])
    stamps = [r["attributes"].get("last_edited_date") for r in rows]
    known = [s for s in stamps if s]
    return (from_epoch_ms(max(known)) if known else None), len(stamps) - len(known)


def roster_members(path=ROSTER):
    """{seat label: name} from the officials roster's Parish Council table, e.g. {"Dist. 1": ...}."""
    if not path.exists():
        return {}
    members, in_council = {}, False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            in_council = line.strip() == "## Parish Council"
            continue
        m = re.match(r"\|\s*(.+?)\s*\((Dist\. \d|Div\. [AB])\)\s*\|", line)
        if in_council and m:
            members[m.group(2)] = m.group(1)
    return members


def split_values(text):
    return [v.strip() for v in (text or "").split("|") if v.strip()]


def precinct_report(attrs, council_district):
    """Lines describing a precinct record, with the cautions its values call for."""
    lines, notes = [], []
    for field, label in PRECINCT_FIELDS:
        value = (attrs.get(field) or "").strip()
        if not value:
            continue
        values = split_values(value)
        if len(values) > 1:
            notes.append(f"{label}: the precinct is split ({' or '.join(values)}), so the precinct alone "
                         "can't say which applies to this address. Ask the Registrar of Voters.")
        lines.append(f"  {label}: {value}")
    pj = split_values(attrs.get("pj"))
    if council_district and pj and council_district not in pj:
        notes.append(f"The Council District layer says {council_district} but the precinct record says "
                     f"{' or '.join(pj)}. One of the layers may predate a boundary change. Check with the "
                     "Registrar of Voters.")
    return lines, notes


def cmd_district(a):
    if a.point:
        try:
            lat, lon = (float(x) for x in a.point.split(","))
        except ValueError:
            sys.exit("--point takes LAT,LON in decimal degrees, e.g. 29.9634,-90.4070")
        print(f"Point {lat:.6f}, {lon:.6f}")
    else:
        candidates = geocode(a.address)
        if not candidates:
            print("The parish geocoder found no match. Try the street address without unit or ZIP, or --point.")
            return 1
        top = candidates[0]
        if top["score"] < MIN_SCORE:
            print(f"No confident match (best score {top['score']:.0f}). Candidates:")
            for c in candidates:
                print(f"  {c['score']:5.1f}  {c['address']}")
            print("Rerun with the exact address shown, or with --point.")
            return 1
        lon, lat = top["location"]["x"], top["location"]["y"]
        print(f"Matched {top['address']} (score {top['score']:.0f}) at {lat:.6f}, {lon:.6f}")

    council = layer_at(COUNCIL_LAYER, lon, lat)
    if not council:
        print("This point is outside every parish council district, so it is probably outside St. Charles Parish.")
        return 1
    district = str(council[0].get("district") or "").strip()
    members = roster_members()
    print(f"\nParish Council district: {district}")
    if members:
        print(f"  District member: {members.get(f'Dist. {district}', 'not in the roster')}")
        print(f"  At-large members, elected parishwide (Charter III.A.1): Division A {members.get('Div. A', '?')}, "
              f"Division B {members.get('Div. B', '?')}")
        print(f"  Names from {ROSTER.name}; check them against Legistar before relying on them.")
    edited, undated = layer_edited(COUNCIL_LAYER)
    vintage = f"last edit recorded {edited:%Y-%m-%d}" if edited else "no edit dates recorded"
    print(f"  Layer: parish GIS Council Districts, {vintage}; {undated} of its polygons carry no edit date.")
    own = from_epoch_ms(council[0].get("last_edited_date"))
    print(f"  This district's polygon: {'edited ' + f'{own:%Y-%m-%d}' if own else 'no edit date'}.")
    print(f"  Boundary ordinances to compare: {'; '.join(DISTRICT_ORDINANCES)}.")

    for label, layer, key in (("Community", COMMUNITY_LAYER, "name"), ("Fire district", FIRE_LAYER, "code")):
        rows = layer_at(layer, lon, lat)
        if rows:
            extra = f" ({rows[0].get('city')})" if key == "code" and rows[0].get("city") else ""
            print(f"{label}: {rows[0].get(key)}{extra}")
        else:
            print(f"{label}: none on the parish layer at this point")

    precincts = layer_at(PRECINCT_LAYER, lon, lat)
    print("\nVoting precinct (parish layer \"Precincts 2023 Mergers\"):")
    if not precincts:
        print("  none found at this point")
        return 0
    lines, notes = precinct_report(precincts[0], district)
    print("\n".join(lines))
    for n in notes:
        print(f"  Note: {n}")
    print("  The Registrar of Voters and the Secretary of State's voter portal are the authority for a voter's "
          "districts and polling place; this layer is the parish's 2023 copy.")
    return 0


# ---------------------------------------------------------------- bodies

def event_start(event):
    day = dt.date.fromisoformat(event["EventDate"][:10])
    clock = (event.get("EventTime") or "").strip().upper()
    try:
        t = dt.datetime.strptime(clock, "%I:%M %p").time()
    except ValueError:
        return None
    return dt.datetime.combine(day, t, tzinfo=CENTRAL)


def cmd_bodies(a):
    today = dt.date.today()
    since = today - dt.timedelta(days=round(a.months * 30.44))
    bodies = [b for b in legistar("/bodies") if b.get("BodyActiveFlag") and b["BodyName"] not in NOT_MEETING_BODIES]
    events = legistar("/events", **{"$filter": f"EventDate ge datetime'{since.isoformat()}'", "$top": 1000})
    if len(events) >= 1000:
        print("Warning: Legistar returned its 1,000-row maximum, so the oldest meetings in the period may be "
              "missing. Use a shorter --months.\n")
    by_body = collections.defaultdict(list)
    for e in events:
        by_body[e["EventBodyId"]].append(e)
    print(f"Legistar bodies for St. Charles Parish: meetings from {since} through yesterday, and the next one listed from today ({today}) on.")
    print("Legistar lists a meeting once the clerk publishes it, so 'next' can be empty for a meeting already "
          "on the public calendar (scp-watch `calendar` reads that).\n")
    print(f"{'Body':58} {'Held':>4}  {'Last':10}  {'Next':10}  Usual time, place")
    for b in sorted(bodies, key=lambda b: b["BodyName"]):
        rows = by_body.get(b["BodyId"], [])
        held = [e for e in rows if e["EventDate"][:10] < today.isoformat()
                and "cancel" not in (e.get("EventComment") or "").lower()
                and (e.get("EventAgendaStatusName") or "") != "Cancelled"]
        future = sorted(e["EventDate"][:10] for e in rows if e["EventDate"][:10] >= today.isoformat())
        last = max((e["EventDate"][:10] for e in held), default="")
        usual = collections.Counter(squash(f"{e.get('EventTime') or ''}, {e.get('EventLocation') or ''}")
                                    for e in rows).most_common(1)
        print(f"{b['BodyName'][:58]:58} {len(held):>4}  {last:10}  {(future[0] if future else ''):10}  "
              f"{usual[0][0] if usual else ''}")
    print("\n'Held' leaves out meetings Legistar marks cancelled. Bid openings are listed as their own body.")
    return 0


# ---------------------------------------------------------------- notice

def find_event(a):
    if a.event:
        return legistar(f"/events/{a.event}")
    if not (a.body and a.date):
        sys.exit("notice takes --event ID, or --body TEXT with --date YYYY-MM-DD")
    rows = legistar("/events", **{"$filter": f"EventDate eq datetime'{a.date}'"})
    want = a.body.lower()
    rows = [e for e in rows if want in e["EventBodyName"].lower() and e["EventBodyName"] != CHAMBER_BOOKING]
    if len(rows) != 1:
        if not rows:
            print(f"No Legistar meeting of a body matching {a.body!r} on {a.date}. The API lists a meeting only once "
                  "published; scp-watch `calendar` shows scheduled ones.")
        else:
            print("More than one meeting matches; rerun with --event:")
            for e in rows:
                print(f"  --event {e['EventId']}  {e['EventBodyName']} {e.get('EventTime')}")
        return None
    return rows[0]


def utc_to_central(stamp):
    if not stamp:
        return None
    return dt.datetime.fromisoformat(stamp[:19]).replace(tzinfo=dt.timezone.utc).astimezone(CENTRAL)


def minutes_text(url):
    if not url or not shutil.which("pdftotext"):
        return None
    try:
        pdf = fetch(url)
    except SourceError:
        return None
    out = subprocess.run(["pdftotext", "-layout", "-", "-"], input=pdf, capture_output=True)
    return out.stdout.decode("utf-8", "replace") if out.returncode == 0 else None


def decided_matters(items):
    """Distinct matters with a recorded pass/fail vote.

    One matter can carry several voted lines (amendments, closing nominations, then adoption), and
    motions such as adjournment carry no matter, so lines overcount the items comment must precede.
    """
    return {i["EventItemMatterId"] for i in items
            if i.get("EventItemPassedFlag") is not None and i.get("EventItemMatterId")}


def is_council_or_committee(event, body_types):
    return event["EventBodyName"] == "Parish Council" or body_types.get(event["EventBodyId"]) == "Committee"


def fmt(t):
    return f"{t:%a %Y-%m-%d %I:%M %p} Central" if t else "none"


def cmd_notice(a):
    event = find_event(a)
    if not event:
        return 1
    start = event_start(event)
    body_types = {b["BodyId"]: b.get("BodyTypeName") for b in legistar("/bodies")}
    print(f"{event['EventBodyName']}, {event['EventDate'][:10]} {event.get('EventTime') or '(no time listed)'}, "
          f"{event.get('EventLocation') or 'no location listed'}  (Legistar event {event['EventId']})")
    print(f"Meeting page: {event.get('EventInSiteURL') or 'none'}")
    if event.get("EventComment"):
        print(f"Clerk's note: {event['EventComment']}")
    print("Indicators only, not findings of a violation. See references/open-meetings.md for what each rule says.\n")

    print("1. Agenda timing (R.S. 42:19(A)(1)(b): notice with the agenda 24 hours ahead, not counting Saturdays, "
          "Sundays or legal holidays; the agenda may not be changed inside that window)")
    if not start:
        print("   Legistar gives no start time, so the window can't be computed.\n")
    else:
        holidays, conditional = holidays_around(start.date(), a.holiday)
        deadline = notice_deadline(start, holidays)
        print(f"   Latest time for notice: {fmt(deadline)}")
        skipped = [f"{d} {n}" for d, n in sorted(holidays.items()) if deadline.date() <= d <= start.date()]
        if skipped:
            print(f"   Legal holidays skipped (R.S. 1:55(A)(1); some are holidays though offices stay open): "
                  f"{'; '.join(skipped)}")
        in_window = {d: n for d, n in conditional.items() if deadline.date() <= d <= start.date()}
        alt = None
        if in_window:
            alt = notice_deadline(start, {**holidays, **in_window})
            print(f"   If {', '.join(in_window.values())} counts as a holiday: {fmt(alt)}")
        published = utc_to_central(event.get("EventAgendaLastPublishedUTC"))
        print(f"   Legistar agenda status {event.get('EventAgendaStatusName')!r}, last published {fmt(published)}")
        if not published:
            print("   Question: Legistar has no publish time for this agenda. Where and when was the notice posted?")
        elif published <= (alt or deadline):
            print("   Legistar's copy was last published before that time. That doesn't show when the notice was "
                  "posted at the office or published, which is what the statute requires.")
        elif published <= deadline:
            print("   Legistar's copy was last published before that time only if the conditional holiday above "
                  "doesn't count. Ask whether the parish declared it, and when the notice was posted.")
        else:
            print("   Question: Legistar's copy was last published inside the window. Either the agenda went up late, "
                  "or it was changed or republished late. A change inside the window is what 42:19 bars; a "
                  "republish with no change isn't. Ask the custodian for the posted notice, when it was posted, and "
                  "whether the agenda changed. Late website posting alone isn't a violation (42:19(A)(2)(a)).")
        booked = legistar("/events", **{"$filter": f"EventDate ge datetime'{deadline.date().isoformat()}' and "
                                                   f"EventDate le datetime'{start.date().isoformat()}'"})
        closed = sorted({e["EventDate"][:10] for e in booked if e["EventBodyName"] == CHAMBER_BOOKING
                         and "holiday" in (e.get("EventComment") or "").lower()})
        unlisted = [d for d in closed if dt.date.fromisoformat(d) not in holidays]
        if unlisted:
            print(f"   The chamber booking calendar marks {', '.join(unlisted)} as a courthouse holiday, which the "
                  "R.S. 1:55 list here doesn't. Rerun with --holiday if it is a legal holiday.")
        print()

    print("2. Minutes (R.S. 42:20: written minutes; adopted minutes posted on the website)")
    published = utc_to_central(event.get("EventMinutesLastPublishedUTC"))
    print(f"   Legistar minutes status {event.get('EventMinutesStatusName')!r}, last published {fmt(published)}")
    text = minutes_text(event.get("EventMinutesFile"))
    if event.get("EventMinutesFile") and text is None:
        print("   The minutes file couldn't be read here (no pdftotext, or the download failed).")
    print()

    print("3. Public comment before votes (R.S. 42:14(D); school boards are under 42:15)")
    items = legistar(f"/events/{event['EventId']}/eventitems")
    decided = decided_matters(items)
    print(f"   Matters with a recorded vote: {len(decided)} (agenda lines: {len(items)})")
    if text:
        opened = len(re.findall(r"public comment opened", text, re.I))
        none_ = len(re.findall(r"no public comment", text, re.I))
        print(f"   Minutes mention \"Public comment opened\" {opened} times (\"no public comment\" {none_}).")
        if decided and opened < len(decided):
            print("   Question: fewer comment openings than decided items. Comment may have been taken in one "
                  "period, which 42:14(D) allows if it comes before the votes. Check the recording.")
        if re.search(r"executive session", text, re.I):
            print("   The minutes mention an executive session: 42:16 requires a two-thirds vote in open meeting "
                  "with each member's vote and the reason recorded, and no final action inside.")
    else:
        print("   No minutes text to check.")
    print()

    print("4. Live broadcast (R.S. 42:23(B)(2)(a)(i): the Council and its committees, in a parish over 25,000)")
    if is_council_or_committee(event, body_types):
        print("   Required for this body. Legistar's video field is "
              f"{'set' if event.get('EventVideoPath') else 'empty'}; find the recording with "
              f"scp-meeting-record: find \"{event['EventBodyName']}\" {event['EventDate'][:10]}")
    else:
        print("   This statute names the governing authority and its committees, and nonelected boards that levy a "
              "tax (42:23(B)(1), recording). Sec. 2-16.3 of the parish code has all boards meet at the courthouse "
              "and be televised; whether this body does is a question.")
    print()

    if event["EventBodyName"] == "Parish Council":
        year = event["EventDate"][:4]
        print(f"5. Annual schedule (R.S. 42:19(A)(1)(a); Council Rule 1)")
        rows = legistar("/matters", **{"$filter": f"substringof('{year} Parish Council Meeting Schedule',MatterTitle)"})
        if rows:
            for m in rows:
                print(f"   {m['MatterFile']} {m['MatterTitle']} (introduced {m['MatterIntroDate'][:10]})")
        else:
            print(f"   No Legistar matter titled \"... {year} Parish Council Meeting Schedule\". Ask the Council "
                  "Secretary for the year's notice.")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("district", help="districts and representatives for an address or point")
    d.add_argument("address", nargs="?")
    d.add_argument("--point", help="LAT,LON instead of an address")
    b = sub.add_parser("bodies", help="Legistar bodies, how often each met, last and next meeting")
    b.add_argument("--months", type=float, default=12)
    n = sub.add_parser("notice", help="Open Meetings Law indicators for one meeting")
    n.add_argument("--event", type=int)
    n.add_argument("--body")
    n.add_argument("--date")
    n.add_argument("--holiday", action="append", default=[], type=dt.date.fromisoformat,
                   help="a legal holiday to exclude, YYYY-MM-DD (repeatable)")
    a = p.parse_args(argv)
    if a.cmd == "district" and not (a.address or a.point):
        p.error("district takes an address or --point")
    try:
        return {"district": cmd_district, "bodies": cmd_bodies, "notice": cmd_notice}[a.cmd](a)
    except SourceError as exc:
        print(f"Could not reach a source: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
