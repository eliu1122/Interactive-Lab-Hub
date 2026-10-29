"""
Desk Curfew, the morning arithmetic. Turns night_log.jsonl (from overnight.py) and the
bedtime pledge (tonight.json, from curfew.py) into facts the morning report can trust.

There is no language model in this file. In Parts D and E Qwen got a time gap wrong and
counted one person as three, so every count, time and duration is calculated here and
the model only rephrases the result (see curfew.py).

    python night_report.py                                  # tonight.json + night_log.jsonl
    python night_report.py --dir nights/2026-10-30          # a night that was already archived
"""
import argparse
import datetime
import json
import pathlib

MERGE_GAP = 120         # seconds of "nobody" between two sightings that still count as one stay (missed detections)
MIN_VISIT = 30          # sightings shorter than this are glimpses (or false positives): reported, not counted
BLIND_GAP = 15 * 60     # overnight.py writes at least every 10 min, so a longer silence means it was not watching
HANDOFF_WINDOW = 5 * 60 # a sighting this soon after the hand-off is the person still at the desk


def load_log(path):
    """night_log.jsonl as a list of (datetime, entry), oldest first."""
    entries = []
    for line in open(path):
        if line.strip():
            e = json.loads(line)
            entries.append((datetime.datetime.fromisoformat(e["t"]), e))
    return entries


def curfew_datetime(start, hhmm):
    """The curfew as a moment: 00:30 promised at 23:10 means 00:30 the next day."""
    c = datetime.datetime.combine(start.date(), datetime.time.fromisoformat(hhmm))
    if c < start - datetime.timedelta(hours=3):
        c += datetime.timedelta(days=1)
    return c


def secs(a, b):
    return (b - a).total_seconds()


def sightings(entries):
    """Change-only readings -> (start, end) intervals when someone was in view.

    Returns (stays, glimpses): stays after merging short "nobody" gaps and dropping
    anything shorter than MIN_VISIT, and the number of glimpses that were dropped.
    """
    raw, open_at = [], None
    for t, e in entries:
        if "reading" not in e:
            continue
        if e["reading"] != "nobody":
            if open_at is None:
                open_at = t
        elif open_at is not None:
            raw.append((open_at, t))
            open_at = None
    if open_at is not None:                       # still in view when the log stopped
        raw.append((open_at, entries[-1][0]))

    merged = []
    for s, e in raw:
        if merged and secs(merged[-1][1], s) < MERGE_GAP:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    stays = [v for v in merged if secs(*v) >= MIN_VISIT]
    return stays, len(merged) - len(stays)


def blind_spots(entries):
    """Stretches where nothing was written for longer than BLIND_GAP: the camera was not watching."""
    return [(a[0], b[0]) for a, b in zip(entries, entries[1:]) if secs(a[0], b[0]) > BLIND_GAP]


def overlap(a, b, start, end):
    return max(0.0, secs(max(a, start), min(b, end)))


def summarize(entries, pledge=None):
    """The night as a dict of plain facts. `pledge` is tonight.json (curfew, start), or None."""
    if not entries:
        return {"verdict": "no data"}
    start = datetime.datetime.fromisoformat(pledge["start"]) if pledge else entries[0][0]
    end = entries[-1][0]
    stays, glimpses = sightings(entries)
    blinds = blind_spots(entries)

    if stays and secs(start, stays[0][0]) <= HANDOFF_WINDOW:
        left_at, returns = stays[0][1], stays[1:]
    else:
        left_at, returns = None, stays            # the chair was already empty when watching began

    facts = {
        "start": start, "end": end, "left_at": left_at, "returns": returns,
        "glimpses": glimpses, "blind_spots": blinds, "curfew": None, "late_seconds": 0,
        "last_seen": stays[-1][1] if stays else None,
    }
    if not pledge:
        facts["verdict"] = "no pledge"
        return facts

    curfew = curfew_datetime(start, pledge["curfew"])
    late = sum(overlap(s, e, curfew, end) for s, e in stays)
    facts.update(curfew=curfew, late_seconds=late,
                 blind_after_curfew=any(b > curfew for _, b in blinds))
    facts["verdict"] = "missed" if late > 0 else "kept"
    return facts


def hm(t):
    return t.strftime("%H:%M")


def dur(seconds):
    m = round(seconds / 60)
    if m < 1:
        return "under a minute"
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h {m % 60} min" if m % 60 else f"{m // 60} h"


def sentences(f):
    """The checked, plain-language report: what the morning says if Qwen is off or wrong."""
    v = f["verdict"]
    if v == "no data":
        return ["The night log is empty, so I can't tell you anything about last night."]

    out = []
    if v == "kept":
        how = "as far as I could see" if f.get("blind_after_curfew") else "and the chair stayed empty after it"
        out.append(f"Curfew kept: you promised {hm(f['curfew'])}, {how}.")
    elif v == "missed":
        out.append(f"Curfew missed: you promised {hm(f['curfew'])}, but someone was at the desk "
                   f"for {dur(f['late_seconds'])} after it, last until {hm(f['last_seen'])}.")
    else:
        out.append("There was no curfew set last night, so this is just what the desk saw.")

    if f["left_at"]:
        out.append(f"You left the desk at {hm(f['left_at'])}.")
    else:
        out.append(f"The chair was already empty when I started watching at {hm(f['start'])}.")

    r = f["returns"]
    if not r:
        out.append(f"Nobody came back before I stopped at {hm(f['end'])}.")
    elif len(r) == 1:
        out.append(f"Someone came back once, at {hm(r[0][0])}, for {dur(secs(*r[0]))}.")
    else:
        longest = max(r, key=lambda v: secs(*v))
        out.append(f"Someone came back {len(r)} times; the longest was at {hm(longest[0])}, "
                   f"for {dur(secs(*longest))}.")

    for a, b in f["blind_spots"]:
        out.append(f"I wasn't watching from {hm(a)} to {hm(b)}, so I can't vouch for that stretch.")
    if f["glimpses"]:
        out.append(f"I also ignored {f['glimpses']} brief glimpse{'s' if f['glimpses'] > 1 else ''} "
                   f"shorter than {MIN_VISIT} seconds.")
    return out


def screen_lines(f):
    """Three short lines for the Mini PiTFT."""
    v = f["verdict"]
    if v == "no data":
        return ["NO DATA", "log is empty", ""]
    top = {"kept": "CURFEW KEPT", "missed": f"MISSED +{dur(f['late_seconds'])}"}.get(v, "NO CURFEW SET")
    left = f"left {hm(f['left_at'])}" if f["left_at"] else f"empty from {hm(f['start'])}"
    back = f"back {len(f['returns'])}x" if f["returns"] else "no returns"
    if f["blind_spots"]:
        back += ", gaps!"
    return [top, left, back]


def load_night(log="night_log.jsonl", pledge="tonight.json"):
    log, pledge = pathlib.Path(log), pathlib.Path(pledge)
    return (load_log(log) if log.exists() else []), (json.loads(pledge.read_text()) if pledge.exists() else None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="an archived night folder (nights/YYYY-MM-DD)")
    args = parser.parse_args()
    d = pathlib.Path(args.dir or ".")
    facts = summarize(*load_night(d / "night_log.jsonl", d / "tonight.json"))
    print("\n".join(screen_lines(facts)), "\n")
    print(" ".join(sentences(facts)))
