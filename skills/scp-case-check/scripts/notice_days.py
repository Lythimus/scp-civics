#!/usr/bin/env python3
"""Count St. Charles Parish hearing-notice days against the rule for a hearing type.

Reports plain subtraction only. The code says days must "elapse" and no ruling on how
to count them has been checked, so a short count is a question for staff, not a defect.
"""
import argparse
import datetime as dt

THURSDAY = 3  # the Herald-Guide, the official journal, publishes on Thursdays

RULES = {
    "rezoning": {
        "cite": "App. A Sec. XV.B",
        "publications": 3,
        "separate_weeks": True,
        "lead": 15,
        "sign": 10,
        "mail": (10, "abutting owners"),
    },
    "plat": {
        "cite": "App. C Sec. II.E.4.d",
        "publications": 3,
        "separate_weeks": True,
        "lead": 15,
        "sign": 10,
        "mail": (10, "adjoining owners and the Council Secretary"),
    },
    "zba": {
        "cite": "App. A Sec. XIII.C.8",
        "publications": 3,
        "separate_weeks": True,
        "lead": 15,
        "sign": 10,
        "mail": (10, "abutting owners"),
    },
    "council": {
        "cite": "R.S. 33:4780.43",
        "publications": 3,
        "separate_weeks": True,
        "lead": 15,
        "sign": None,
        "mail": (10, "owners, unless more than 10 parcels are involved"),
    },
    "plan": {
        "cite": "R.S. 33:108(B)",
        "publications": 1,
        "separate_weeks": False,
        "lead": 10,
        "sign": None,
        "mail": None,
    },
}


def parse_date(text):
    try:
        return dt.date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not YYYY-MM-DD") from exc


def last_thursday_on_or_before(day):
    return day - dt.timedelta(days=(day.weekday() - THURSDAY) % 7)


def show(day):
    return f"{day:%a} {day.isoformat()}"


def deadlines(rule, hearing):
    latest = last_thursday_on_or_before(hearing - dt.timedelta(days=rule["lead"]))
    lines = [f"Latest first publication on a Thursday: {show(latest)} ({(hearing - latest).days} days ahead)"]
    if rule["sign"]:
        lines.append(f"Latest sign posting: {show(hearing - dt.timedelta(days=rule['sign']))}")
    if rule["mail"]:
        days, who = rule["mail"]
        lines.append(f"Latest certified mailing to {who}: {show(hearing - dt.timedelta(days=days))}")
    return lines


def audit(rule, hearing, published):
    published = sorted(set(published))
    lines = [f"Publications found: {', '.join(show(d) for d in published)}"]

    late = [d for d in published if d > hearing]
    if late:
        lines.append(f"QUESTION: after the hearing, so not counted: {', '.join(show(d) for d in late)}")
    counted = [d for d in published if d <= hearing]
    if not counted:
        lines.append("QUESTION: no publication on or before the hearing date")
        return lines

    if hearing in counted:
        lines.append("Note: one publication ran on the hearing date itself")

    elapsed = (hearing - counted[0]).days
    if elapsed >= rule["lead"]:
        lines.append(f"Lead time: {elapsed} days by plain subtraction; rule is at least {rule['lead']}. Met on this count")
    else:
        lines.append(
            f"QUESTION: lead time is {elapsed} days by plain subtraction; rule is at least {rule['lead']}. "
            "Ask staff how the parish counts"
        )

    if len(counted) < rule["publications"]:
        lines.append(f"QUESTION: {len(counted)} publications found; rule is at least {rule['publications']}")
    if rule["separate_weeks"]:
        weeks = {d.isocalendar()[:2] for d in counted}
        if len(weeks) < rule["publications"]:
            lines.append(f"QUESTION: publications fall in {len(weeks)} separate weeks; rule is {rule['publications']}")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rule", required=True, choices=sorted(RULES))
    parser.add_argument("--hearing", required=True, type=parse_date, help="YYYY-MM-DD")
    parser.add_argument("--published", nargs="*", type=parse_date, default=[], help="publication dates, YYYY-MM-DD")
    args = parser.parse_args()

    rule = RULES[args.rule]
    print(f"{args.rule} hearing {show(args.hearing)}; rule source: {rule['cite']}")
    for line in deadlines(rule, args.hearing):
        print(line)
    if args.published:
        for line in audit(rule, args.hearing, args.published):
            print(line)


if __name__ == "__main__":
    main()
