"""
Desk Curfew: a bedtime promise that the desk holds you to.

Hardware: the Raspberry Pi, the webcam, and the Mini PiTFT from Lab 2 (its screen and
two buttons). Nothing else.

Before bed (Part G): the screen shows tonight's curfew. The bottom button adds 15
minutes; the top button hands the night over. The screen says GOODNIGHT and goes dark.
Overnight (Part H): overnight.py runs underneath and logs who is in the desk chair.
The top button shows the curfew for three seconds; holding the bottom one for 2 s
ends the night early.
Morning (Part I): at --morning logging stops and the screen lights up, green if the
chair stayed empty after curfew and red if it did not, with the details below. It stays
lit so it can be read from bed. The top button shows Qwen's morning message, a page at
a time; holding the bottom one turns the screen off.

    python curfew.py                            # the whole night (start it inside tmux)
    python curfew.py --curfew 00:30             # where the curfew starts before the bottom button moves it
    python curfew.py --morning 07:30            # when to stop watching and light up the answer
    python curfew.py --interval 10              # seconds between looks, passed to overnight.py
    python curfew.py --report nights/2026-10-30 # replay an archived morning, no camera
    python curfew.py --no-qwen                  # show the checked template only

Fake a night first: --curfew one minute from now, --morning three minutes from now
(`date -d '+3 min' +%H:%M`). Without the PiTFT everything prints in the terminal and
Enter replaces the top button.
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import time

import night_report

MORNING_HOURS = 3           # the morning screen stays lit this long unless the bottom button is held
COLORS = {"kept": (40, 170, 80), "missed": (200, 50, 40)}   # morning background; anything else is amber
UNSURE = (200, 150, 40)
HOLD = 2.0                  # seconds to hold the bottom button to end the night or finish
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LOG, PLEDGE = pathlib.Path("night_log.jsonl"), pathlib.Path("tonight.json")


class Hardware:
    """Mini PiTFT screen and buttons (Lab 2). Without it, everything goes to the terminal."""

    def __init__(self):
        self.disp = self.top = self.bottom = None
        try:
            import adafruit_rgb_display.st7789 as st7789
            import board
            import digitalio
            self.disp = st7789.ST7789(board.SPI(), cs=digitalio.DigitalInOut(board.D5),
                                      dc=digitalio.DigitalInOut(board.D25), rst=None, baudrate=64000000,
                                      width=135, height=240, x_offset=53, y_offset=40)
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output()
            self.top = digitalio.DigitalInOut(board.D23)
            self.bottom = digitalio.DigitalInOut(board.D24)
            for b in (self.top, self.bottom):
                b.switch_to_input(pull=digitalio.Pull.UP)       # reads False while held down
        except Exception as e:
            print("no Mini PiTFT, using the terminal instead:", e)

    def show(self, lines, background=None):
        """Three lines of text; with `background`, the whole screen is filled so it reads from across the room."""
        print(" | ".join(l for l in lines if l), flush=True)
        if not self.disp:
            return
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (240, 135), background or (0, 0, 0))
        draw = ImageDraw.Draw(img)
        color, detail = ((255, 255, 255), (235, 235, 235)) if background else ((255, 255, 255), (200, 200, 200))
        size = 28
        while size > 14 and draw.textlength(lines[0], font=ImageFont.truetype(FONT, size)) > 228:
            size -= 2                                           # shrink a long headline to fit the 240 px screen
        big, small = ImageFont.truetype(FONT, size), ImageFont.truetype(FONT, 20)
        draw.text((6, 8), lines[0], font=big, fill=color)
        for i, line in enumerate(lines[1:3]):
            draw.text((6, 52 + i * 34), line, font=small, fill=detail)
        self.disp.image(img, 90)
        self.backlight.value = True

    def dark(self):
        if self.disp:
            from PIL import Image
            self.disp.image(Image.new("RGB", (240, 135)), 90)
            self.backlight.value = False

    def pressed(self, button):
        return button is not None and not button.value

    def held(self, button):
        """True if `button` is held for HOLD seconds; returns as soon as it is released."""
        t0 = time.time()
        while self.pressed(button):
            if time.time() - t0 >= HOLD:
                return True
            time.sleep(0.05)
        return False

    def wait_release(self, button):
        while self.pressed(button):
            time.sleep(0.05)

    def page(self, rows, n, total):
        """Show one page of wrapped text (from pages()), with "n/total" in the corner."""
        print("\n".join(rows), flush=True)
        if not self.disp:
            return
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (240, 135))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(FONT, 17)
        for i, row in enumerate(rows):
            draw.text((6, 4 + i * 21), row, font=font, fill=(255, 255, 255))
        draw.text((200, 116), f"{n + 1}/{total}", font=ImageFont.truetype(FONT, 13), fill=(150, 150, 150))
        self.disp.image(img, 90)
        self.backlight.value = True


def pages(text, width=24, rows=6):
    """Wrap `text` for the 240x135 screen and split it into pages of `rows` lines."""
    import textwrap
    lines = textwrap.wrap(text, width)
    return [lines[i:i + rows] for i in range(0, len(lines), rows)] or [[]]


def next_at(hhmm, after):
    t = datetime.datetime.combine(after.date(), datetime.time.fromisoformat(hhmm))
    return t if t > after else t + datetime.timedelta(days=1)


def bedtime(hw, curfew):
    """Part G: the hand-off. Returns tonight's curfew as HH:MM."""
    if not hw.top:
        while True:
            s = input(f"curfew tonight [{curfew}], Enter to hand over: ").strip() or curfew
            try:
                datetime.time.fromisoformat(s)
                return s
            except ValueError:
                print("use HH:MM, for example 00:30")
    h, m = map(int, curfew.split(":"))
    minutes = h * 60 + m
    hhmm = lambda: f"{minutes // 60:02d}:{minutes % 60:02d}"
    hw.show(["CURFEW " + hhmm(), "bottom: +15 min", "top: goodnight"])
    while True:
        if hw.pressed(hw.bottom):
            minutes = (minutes + 15) % (24 * 60)
            hw.show(["CURFEW " + hhmm(), "bottom: +15 min", "top: goodnight"])
            hw.wait_release(hw.bottom)
        elif hw.pressed(hw.top):
            hw.wait_release(hw.top)
            return hhmm()
        time.sleep(0.05)


def archive_leftovers():
    """A log from an earlier, unfinished run would be mixed into tonight's: move it aside."""
    if LOG.exists():
        dest = pathlib.Path("nights") / f"unfinished-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        dest.mkdir(parents=True)
        for p in (LOG, PLEDGE):
            if p.exists():
                shutil.move(str(p), dest / p.name)
        print("moved an earlier log to", dest)


def night_shift(hw, curfew, morning, interval):
    """Part H: run overnight.py until the morning time, a 2 s hold on the bottom button, or Ctrl-C."""
    proc = subprocess.Popen([sys.executable, "overnight.py", "--interval", str(interval)])
    try:
        while proc.poll() is None and datetime.datetime.now() < morning:
            if hw.pressed(hw.top):
                hw.show(["WATCHING", f"curfew {curfew}", f"until {morning:%H:%M}"])
                hw.wait_release(hw.top)
                time.sleep(3)
                hw.dark()
            elif hw.pressed(hw.bottom) and hw.held(hw.bottom):
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass                                     # Ctrl-C in tmux reaches overnight.py too
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
    proc.wait(timeout=30)
    with open(LOG, "a") as log:                  # the log only records changes, so mark when watching ended
        log.write(json.dumps({"t": datetime.datetime.now().isoformat(timespec="seconds"), "stopped": True}) + "\n")


def phrase(sentences, model, verdict):
    """Ask Qwen to make the checked sentences gentler.

    Rejected if it changes or invents a time, drops the verdict, or talks as if it were the
    person (the first fake night got "I was at the desk at 16:52..." past a times-only check).
    """
    import requests                              # only needed on the Pi, where Ollama runs
    facts = " ".join(sentences)
    prompt = f"""You are a small bedside device that watched a desk chair overnight. These facts are already checked:

{facts}

Rewrite them as a friendly morning message of at most three sentences, spoken to the person who just woke up.
Begin with the first sentence's opening words ("Curfew kept" or "Curfew missed") unchanged. Call the person "you".
Use only these facts. Keep every time exactly as written. Do not add people, reasons or advice."""
    try:
        r = requests.post("http://localhost:11434/api/generate", json={
            "model": model, "prompt": prompt, "think": False, "stream": False,
            "options": {"temperature": 0.3, "num_predict": 150},
        }, timeout=300)
        r.raise_for_status()
        answer = r.json()["response"].strip()
    except requests.RequestException as e:
        print("Qwen unavailable, using the template:", e)
        return facts, None
    times = lambda s: set(re.findall(r"\b\d{2}:\d{2}\b", s))
    must_say = {"kept": "curfew kept", "missed": "curfew missed"}.get(verdict, "")
    ok = (answer and times(answer) == times(facts) and must_say in answer.lower()
          and not re.search(r"\bI (was|sat|left|came)\b", answer))
    if not ok:
        print("Qwen changed the facts, using the template instead:\n ", answer)
    return (answer if ok else facts), answer


def morning_reveal(hw, folder, use_qwen, model, replay):
    """Part I: a lit, colored screen first; Qwen's message on request. Writes report.json next to the log."""
    entries, pledge = night_report.load_night(folder / LOG.name, folder / PLEDGE.name)
    facts = night_report.summarize(entries, pledge)
    lines, sentences = night_report.screen_lines(facts), night_report.sentences(facts)
    background = COLORS.get(facts["verdict"], UNSURE)
    text, raw = " ".join(sentences), None
    if use_qwen and facts["verdict"] != "no data":
        hw.show([lines[0], "writing report...", ""])
        t0 = time.time()
        text, raw = phrase(sentences, model, facts["verdict"])
        print(f"Qwen took {time.time() - t0:.1f} s")
    hw.show(lines, background)
    print("\n" + text + "\n")
    (folder / "report.json").write_text(json.dumps(
        {"screen": lines, "checked": sentences, "qwen_raw": raw, "spoken": text, "verdict": facts["verdict"]},
        indent=2))
    if not (replay and hw.top):
        return
    print("top button: Qwen's message, page by page; hold bottom: screen off", flush=True)
    message = pages(text)
    t_end, shown = time.time() + MORNING_HOURS * 3600, -1   # -1 = the green/red summary
    try:
        while time.time() < t_end:
            if hw.pressed(hw.top):
                hw.wait_release(hw.top)
                shown += 1
                if shown < len(message):
                    hw.page(message[shown], shown, len(message))
                else:                                       # past the last page: back to the summary
                    shown = -1
                    hw.show(lines, background)
            elif hw.pressed(hw.bottom) and hw.held(hw.bottom):
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    hw.dark()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--curfew", default="00:30", help="the curfew the screen starts at (HH:MM)")
    parser.add_argument("--morning", default="07:00", help="when to stop watching (HH:MM)")
    parser.add_argument("--interval", type=float, default=10, help="seconds between looks")
    parser.add_argument("--report", help="replay the morning for an archived night folder")
    parser.add_argument("--no-qwen", action="store_true")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    args = parser.parse_args()
    datetime.time.fromisoformat(args.curfew)     # fail now, not at 7 a.m., if the time is malformed
    hw = Hardware()

    if args.report:
        morning_reveal(hw, pathlib.Path(args.report), not args.no_qwen, args.model, replay=False)
        raise SystemExit

    archive_leftovers()
    curfew = bedtime(hw, args.curfew)
    start = datetime.datetime.now()
    morning = next_at(args.morning, start)
    PLEDGE.write_text(json.dumps({"curfew": curfew, "start": start.isoformat(timespec="seconds"),
                                  "morning": args.morning}))
    hw.show(["GOODNIGHT", f"curfew {curfew}", f"watching till {morning:%H:%M}"])
    time.sleep(3)
    hw.dark()                                    # the acknowledgement ends in darkness, not a glowing screen

    night_shift(hw, curfew, morning, args.interval)

    folder = pathlib.Path("nights") / f"{start:%Y-%m-%d-%H%M}"
    folder.mkdir(parents=True, exist_ok=True)
    for p in (LOG, PLEDGE):
        if p.exists():
            shutil.move(str(p), folder / p.name)
    print("night saved to", folder)
    morning_reveal(hw, folder, not args.no_qwen, args.model, replay=True)
