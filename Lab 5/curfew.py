"""
Desk Curfew: a bedtime promise that the desk holds you to.

Before bed (Part G): push the joystick up or down to set tonight's curfew in 15-minute
steps, then press it to hand the night over. The OLED says goodnight and goes dark, and
the flag drops to half-mast.
Overnight (Part H): overnight.py runs underneath and logs who is in the desk chair.
A short press shows the curfew for three seconds; nothing else lights up.
Morning (Part I): at --morning, or when you hold the joystick for 2 s, logging stops.
The flag goes up if the chair stayed empty after curfew and down if it did not. Press
the joystick to see the details on the OLED and hear them read aloud with Piper.

    python curfew.py                            # the whole night (start it inside tmux)
    python curfew.py --morning 07:30            # when to stop watching and raise the flag
    python curfew.py --interval 10              # seconds between looks, passed to overnight.py
    python curfew.py --report nights/2026-10-30 # replay an archived morning, no camera
    python curfew.py --no-qwen                  # speak the checked template only

Fake a night first: set the curfew to a minute from now and pass --morning two minutes
from now (`date -d '+2 min' +%H:%M`). Each part falls back to the keyboard or terminal
when its hardware is missing, so --report also works on a laptop.
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

FLAG_WATCHING, FLAG_KEPT, FLAG_MISSED = 60, 120, 0   # servo angles; 0-120 is the safe range from Lab 4
SERVO_CH = 0
STICK_UP_IS_HIGH = True     # flip if pushing the joystick up lowers the curfew
HOLD_TO_END = 2.0           # seconds to hold the button to end the night early
LOG, PLEDGE = pathlib.Path("night_log.jsonl"), pathlib.Path("tonight.json")


class Hardware:
    """Joystick, OLED and servo from Lab 4, Piper from Lab 3. Anything missing is replaced by the terminal."""

    def __init__(self, voices):
        self.stick = self.oled = self.servo = None
        self.voices = voices
        try:
            import qwiic_joystick
            stick = qwiic_joystick.QwiicJoystick()
            if stick.connected:
                stick.begin()
                self.stick = stick
        except Exception as e:
            print("no joystick, using the keyboard:", e)
        try:
            import adafruit_ssd1306
            import board
            import busio
            self.oled = adafruit_ssd1306.SSD1306_I2C(128, 32, busio.I2C(board.SCL, board.SDA))
        except Exception as e:
            print("no OLED, printing instead:", e)
        try:
            import pi_servo_hat
            self.servo = pi_servo_hat.PiServoHat()
            self.servo.restart()
        except Exception as e:
            print("no servo, printing instead:", e)

    def show(self, lines):
        print(" | ".join(l for l in lines if l), flush=True)
        if not self.oled:
            return
        from PIL import Image, ImageDraw
        img = Image.new("1", (128, 32))
        draw = ImageDraw.Draw(img)
        for i, line in enumerate(lines[:3]):
            draw.text((0, i * 11), line, fill=255)
        self.oled.image(img)
        self.oled.show()

    def dark(self):
        if self.oled:
            self.oled.fill(0)
            self.oled.show()

    def flag(self, angle):
        print(f"flag -> {angle} degrees", flush=True)
        if self.servo:
            self.servo.move_servo_position(SERVO_CH, angle)

    def pressed(self):
        return bool(self.stick) and self.stick.button == 0      # the Qwiic joystick reads 0 while pressed

    def tilt(self):
        """+1 for up, -1 for down, 0 for centered."""
        v = self.stick.vertical                                 # 0..1023, about 512 at rest
        d = 1 if v > 900 else -1 if v < 120 else 0
        return d if STICK_UP_IS_HIGH else -d

    def press_length(self):
        """Seconds the current press lasts (returns once released, or at HOLD_TO_END)."""
        t0 = time.time()
        while self.pressed() and time.time() - t0 < HOLD_TO_END:
            time.sleep(0.05)
        return time.time() - t0

    def say(self, text):
        piper = [sys.executable, "-m", "piper", "--model", "en_US-lessac-medium", "--data-dir", str(self.voices),
                 "--output-raw", "--", text]
        try:
            synth = subprocess.Popen(piper, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            subprocess.run(["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                           stdin=synth.stdout, check=True)
            if synth.wait() == 0:
                return
        except (OSError, subprocess.CalledProcessError):
            pass
        try:
            subprocess.run(["espeak", text], check=True, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            print("(no speaker)", text)


def next_at(hhmm, after):
    t = datetime.datetime.combine(after.date(), datetime.time.fromisoformat(hhmm))
    return t if t > after else t + datetime.timedelta(days=1)


def spoken_time(hhmm):
    """00:30 -> "12 30 a.m.", so Piper does not read it as a ratio."""
    h, m = map(int, hhmm.split(":"))
    minutes = "o'clock" if m == 0 else f"oh {m}" if m < 10 else str(m)
    return f"{h % 12 or 12} {minutes} {'a.m.' if h < 12 else 'p.m.'}"


def bedtime(hw, default):
    """Part G: the thirty-second hand-off. Returns the curfew as HH:MM."""
    if not hw.stick:
        while True:
            s = input(f"curfew tonight [{default}]: ").strip() or default
            try:
                datetime.time.fromisoformat(s)
                return s
            except ValueError:
                print("use HH:MM, for example 00:30")
    h, m = map(int, default.split(":"))
    minutes = h * 60 + m
    hhmm = lambda: f"{minutes // 60:02d}:{minutes % 60:02d}"
    hw.show(["CURFEW TONIGHT", "     " + hhmm(), "up/down, press = go"])
    while True:
        d = hw.tilt()
        if d:
            minutes = (minutes + 15 * d) % (24 * 60)
            hw.show(["CURFEW TONIGHT", "     " + hhmm(), "up/down, press = go"])
            time.sleep(0.35)
        elif hw.pressed():
            while hw.pressed():
                time.sleep(0.05)
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
    """Part H: run overnight.py until the morning time or a long press."""
    proc = subprocess.Popen([sys.executable, "overnight.py", "--interval", str(interval)])
    try:
        while proc.poll() is None and datetime.datetime.now() < morning:
            if hw.pressed():
                if hw.press_length() >= HOLD_TO_END:
                    break
                hw.show(["WATCHING", f"curfew {curfew}", f"until {morning:%H:%M}"])
                time.sleep(3)
                hw.dark()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass                                     # Ctrl-C in tmux reaches overnight.py too
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
    proc.wait(timeout=30)


def phrase(sentences, model):
    """Ask Qwen to make the checked sentences gentler. Rejected if it changes or invents a time."""
    import requests                              # only needed on the Pi, where Ollama runs
    facts = " ".join(sentences)
    prompt = f"""You are a small bedside device that watched a desk chair overnight. These facts are already checked:

{facts}

Rewrite them as a friendly morning message of at most three sentences for someone who just woke up.
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
    ok = answer and times(answer) <= times(facts) and times(facts) <= times(answer)
    if not ok:
        print("Qwen changed the facts, using the template instead:\n ", answer)
    return (answer if ok else facts), answer


def morning_reveal(hw, folder, use_qwen, model, wait):
    """Part I: flag, OLED and voice. Writes report.json next to the log."""
    entries, pledge = night_report.load_night(folder / LOG.name, folder / PLEDGE.name)
    facts = night_report.summarize(entries, pledge)
    hw.flag({"kept": FLAG_KEPT, "missed": FLAG_MISSED}.get(facts["verdict"], FLAG_WATCHING))
    lines, sentences = night_report.oled_lines(facts), night_report.sentences(facts)
    hw.show(lines)
    text, raw = " ".join(sentences), None
    if use_qwen and facts["verdict"] != "no data":
        hw.show([lines[0], "writing report...", ""])
        t0 = time.time()
        text, raw = phrase(sentences, model)
        print(f"Qwen took {time.time() - t0:.1f} s")
        hw.show(lines)
    print("\n" + text + "\n")
    (folder / "report.json").write_text(json.dumps(
        {"oled": lines, "checked": sentences, "qwen_raw": raw, "spoken": text, "verdict": facts["verdict"]},
        indent=2))
    hw.say(text)
    if not (wait and hw.stick):
        return
    lit = time.time()
    print("press to hear it again, hold to finish")
    while True:                                  # the screen goes dark after a minute; a press brings it back
        if hw.pressed():
            if hw.press_length() >= HOLD_TO_END:
                break
            hw.show(lines)
            hw.say(text)
            lit = time.time()
        if time.time() - lit > 60:
            hw.dark()
        time.sleep(0.1)
    hw.dark()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--morning", default="07:00", help="when to stop watching (HH:MM)")
    parser.add_argument("--interval", type=float, default=10, help="seconds between looks")
    parser.add_argument("--curfew", default="00:30", help="the joystick's starting value")
    parser.add_argument("--report", help="replay the morning for an archived night folder")
    parser.add_argument("--no-qwen", action="store_true")
    parser.add_argument("--model", default="qwen3.5:0.8b")
    parser.add_argument("--voices", default="../Lab 3/voices", help="Piper voices folder (Lab 3)")
    args = parser.parse_args()
    hw = Hardware(pathlib.Path(args.voices))

    if args.report:
        morning_reveal(hw, pathlib.Path(args.report), not args.no_qwen, args.model, wait=False)
        raise SystemExit

    archive_leftovers()
    curfew = bedtime(hw, args.curfew)
    start = datetime.datetime.now()
    morning = next_at(args.morning, start)
    PLEDGE.write_text(json.dumps({"curfew": curfew, "start": start.isoformat(timespec="seconds"),
                                  "morning": args.morning}))
    hw.flag(FLAG_WATCHING)
    hw.show(["GOODNIGHT", f"curfew {curfew}", f"watching till {morning:%H:%M}"])
    hw.say(f"Curfew {spoken_time(curfew)}. Goodnight.")
    time.sleep(3)
    hw.dark()                                    # the acknowledgement ends in darkness, not a glowing screen

    night_shift(hw, curfew, morning, args.interval)

    folder = pathlib.Path("nights") / f"{start:%Y-%m-%d}"
    folder.mkdir(parents=True, exist_ok=True)
    for p in (LOG, PLEDGE):
        if p.exists():
            shutil.move(str(p), folder / p.name)
    print("night saved to", folder)
    morning_reveal(hw, folder, not args.no_qwen, args.model, wait=True)
