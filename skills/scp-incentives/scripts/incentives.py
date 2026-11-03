#!/usr/bin/env python3
"""Pull the public record of Industrial Development Board leases and related Council items.

  incentives.py idb [--term TEXT ...] [--dir DIR]
  incentives.py council --term TEXT [--term TEXT ...] [--since YYYY-MM-DD]
  incentives.py replays
  incentives.py audit --url URL --dir DIR

Downloads go in the user's project folder, never in the plugin. Standard library plus poppler.
"""
import argparse, json, re, subprocess, sys, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scp-meeting-record" / "scripts"))
import meeting_record as mr  # noqa: E402

IDB_BODY = 179
CABLECAST = "https://reflect-stcharlesparishla.cablecast.tv/cablecastapi/v1"
GATEWAY = "https://stcharlesgov.legistar.com/gateway.aspx?M=L&ID={}"


def hits(text, terms):
    return [t for t in terms if t.lower() in text.lower()]


def matching_lines(text, terms, limit=6):
    lines = [mr.squash(x) for x in text.splitlines()]
    return [x for x in lines if hits(x, terms)][:limit]


def cmd_idb(a):
    if a.dir:
        mr.check_output(a.dir)
    events = mr.legistar("/events", **{"$filter": f"EventBodyId eq {IDB_BODY}", "$orderby": "EventDate desc"})
    print(f"Legistar lists {len(events)} IDB meetings, the oldest on {events[-1]['EventDate'][:10]}. "
          "Earlier meetings aren't on Legistar.\n")
    for e in events:
        day = e["EventDate"][:10]
        print(f"## {day} (event {e['EventId']}): {e['EventInSiteURL']}")
        items = mr.legistar(f"/events/{e['EventId']}/eventitems")
        titles = [mr.squash(i.get("EventItemTitle")) for i in sorted(items, key=mr.sequence)]
        for title in titles:
            # Resolutions always print because agendas misspell applicants, which a term search misses.
            if not a.term or hits(title, a.term) or title.lower().startswith("resolution"):
                print(f"- {'[match] ' if hits(title, a.term or []) else ''}{title}")
        docs = [d for d in mr.parse_documents(mr.fetch(e["EventInSiteURL"]).decode("utf-8", "ignore"))
                if not re.search(r"sign.?in", d[0], re.I)]
        if not any("minutes" in name.lower() for name, _ in docs):
            print("Signed minutes: not posted on the meeting page.")
        for name, url in docs:
            if not a.dir:
                print(f"File: {name}: {url}")
                continue
            pdf, words = mr.save_document(f"{day}_{name}", url, a.dir)
            print(f"File: {pdf} ({words} words of text)")
            for line in matching_lines(pdf.with_suffix(".txt").read_text(errors="ignore"), a.term or []):
                print(f"    {line[:200]}")
        print()


def cmd_council(a):
    seen = set()
    for term in a.term:
        quoted = term.replace("'", "''")
        rows = mr.legistar("/matters", **{"$filter": f"substringof('{quoted}',MatterTitle)",
                                          "$orderby": "MatterIntroDate desc", "$top": "100"})
        rows = [r for r in rows if not a.since or (r.get("MatterIntroDate") or "")[:10] >= a.since]
        print(f"## \"{term}\": {len(rows)} titles" + (" (the API returned its limit of 100)" if len(rows) == 100 else ""))
        for r in rows:
            if r["MatterId"] in seen:
                continue
            seen.add(r["MatterId"])
            print(f"- {r['MatterFile']} {(r.get('MatterIntroDate') or '')[:10]} {r['MatterBodyName'].strip()}, "
                  f"{r['MatterStatusName']}, no. {r.get('MatterEnactmentNumber') or 'none'}: "
                  f"{mr.squash(r['MatterTitle'])[:220]} {GATEWAY.format(r['MatterId'])}")
    print("\nThis searches titles only. A title can leave out the company or the word it was searched for.")


def cmd_replays(a):
    query = urllib.parse.urlencode({"page_size": 100, "include": "vod", "search": "Industrial"})
    data = json.loads(mr.fetch(f"{CABLECAST}/shows?{query}"))
    vods = {v["id"]: v for v in data.get("vods", [])}
    for s in data["shows"]:
        if "industrial" not in s["title"].lower():
            continue
        urls = [vods[v].get("url") for v in s.get("vods", []) if v in vods]
        print(f"- {s['title']} (show {s['id']}): {urls[0] if urls else 'no video file listed'}")


def lease_note(text):
    """The audit note listing each lease, up to the next numbered note."""
    start = re.search(r"Note \d+:\s*DIRECT FINANCING LEASES.*", text)
    if not start:
        return ""
    body = []
    for line in text[start.start():].splitlines():
        if re.match(r"\s*Note \d+:", line) and "DIRECT FINANCING" not in line:
            break
        body.append(line.strip())
    return re.sub(r"\n{2,}", "\n", "\n".join(body)).strip()


def cmd_audit(a):
    mr.check_output(a.dir)
    folder = Path(a.dir)
    folder.mkdir(parents=True, exist_ok=True)
    pdf = folder / Path(urllib.parse.urlparse(a.url).path).name
    pdf.write_bytes(mr.fetch(a.url))
    subprocess.run(["pdftotext", "-layout", str(pdf), str(pdf.with_suffix(".txt"))], capture_output=True)
    text = pdf.with_suffix(".txt").read_text(errors="ignore")
    head = re.search(r"Parish of ([\w. ]+?),", text, re.I)
    period = re.search(r"December 31, \d{4}(?: and \d{4})?", text)
    print(f"{pdf}\nEntity: {mr.squash(head.group(0)) if head else 'not read'}\n"
          f"Period: {period.group(0) if period else 'not read'}\n")
    print(lease_note(text) or "No note headed \"Direct Financing Leases\" found. Read the notes by hand.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("idb"); s.add_argument("--term", action="append"); s.add_argument("--dir")
    s.set_defaults(fn=cmd_idb)
    s = sub.add_parser("council"); s.add_argument("--term", action="append", required=True); s.add_argument("--since")
    s.set_defaults(fn=cmd_council)
    s = sub.add_parser("replays"); s.set_defaults(fn=cmd_replays)
    s = sub.add_parser("audit"); s.add_argument("--url", required=True); s.add_argument("--dir", required=True)
    s.set_defaults(fn=cmd_audit)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
