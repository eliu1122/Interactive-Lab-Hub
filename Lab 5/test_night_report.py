"""
Checks the morning arithmetic on made-up nights, no camera or Pi needed:

    python -m unittest test_night_report
"""
import datetime
import unittest

from night_report import sentences, summarize

DAY = datetime.date(2026, 10, 30)


def at(hhmmss, next_day=False):
    d = DAY + datetime.timedelta(days=1) if next_day else DAY
    return datetime.datetime.combine(d, datetime.time.fromisoformat(hhmmss))


def night(*lines):
    """lines: (time, reading) or (time, None) for a heartbeat."""
    return [(t, {"t": t.isoformat(), "alive": True} if r is None else {"t": t.isoformat(), "reading": r})
            for t, r in lines]


def beats(start, end, every=600):
    t, out = start, []
    while t <= end:
        out.append((t, None))
        t += datetime.timedelta(seconds=every)
    return out


PLEDGE = {"curfew": "00:30", "start": at("23:10:00").isoformat()}
ME = "1 person(s) at center/close"


def build(*lines, until=at("07:00:00", True)):
    """A night from 23:10 to `until` with heartbeats every 10 min plus the given readings."""
    return sorted(night(*beats(at("23:10:00"), until), *lines), key=lambda x: x[0])


class Nights(unittest.TestCase):
    def test_kept(self):
        f = summarize(build((at("23:10:05"), ME), (at("00:12:00", True), "nobody")), PLEDGE)
        self.assertEqual(f["verdict"], "kept")
        self.assertEqual(f["left_at"], at("00:12:00", True))
        self.assertEqual(f["returns"], [])

    def test_missed_by_staying_up(self):
        f = summarize(build((at("23:10:05"), ME), (at("01:47:00", True), "nobody")), PLEDGE)
        self.assertEqual(f["verdict"], "missed")
        self.assertEqual(f["late_seconds"], 77 * 60)
        self.assertIn("1 h 17 min after it, last until 01:47", " ".join(sentences(f)))

    def test_missed_by_coming_back(self):
        f = summarize(build((at("23:10:05"), ME), (at("00:05:00", True), "nobody"),
                            (at("03:10:00", True), ME), (at("03:14:00", True), "nobody")), PLEDGE)
        self.assertEqual(f["verdict"], "missed")
        self.assertEqual(len(f["returns"]), 1)
        self.assertEqual(f["late_seconds"], 4 * 60)

    def test_quiet_night_is_reported_honestly(self):
        f = summarize(build(), PLEDGE)
        self.assertEqual(f["verdict"], "kept")
        self.assertIsNone(f["left_at"])
        self.assertIn("already empty", " ".join(sentences(f)))

    def test_missed_detections_do_not_split_a_stay(self):
        f = summarize(build((at("23:10:05"), ME), (at("23:40:00"), "nobody"), (at("23:40:30"), ME),
                            (at("00:10:00", True), "nobody")), PLEDGE)
        self.assertEqual(f["left_at"], at("00:10:00", True))
        self.assertEqual(f["returns"], [])

    def test_glimpse_is_ignored_but_mentioned(self):
        f = summarize(build((at("02:00:00", True), ME), (at("02:00:10", True), "nobody")), PLEDGE)
        self.assertEqual(f["verdict"], "kept")
        self.assertEqual(f["glimpses"], 1)
        self.assertIn("glimpse", " ".join(sentences(f)))

    def test_blind_spot_weakens_the_verdict(self):
        lines = [l for l in build() if not at("02:00:00", True) < l[0] < at("03:30:00", True)]
        f = summarize(lines, PLEDGE)
        self.assertEqual(len(f["blind_spots"]), 1)
        self.assertIn("as far as I could see", " ".join(sentences(f)))

    def test_empty_log(self):
        self.assertEqual(summarize([], PLEDGE)["verdict"], "no data")


if __name__ == "__main__":
    unittest.main()
