#!/usr/bin/env python3
"""Mini Judge: a Wizard of Oz speech device for Lab 3 Part 2.

The Pi does everything the participant can see and hear. It opens court when
someone presses the top button, speaks the judge's lines with Piper, listens with
Silero VAD, transcribes with faster-whisper, and shows on the Mini PiTFT who has
the floor. A hidden wizard decides what the judge says next from a web page.

    python mini_judge.py
    python mini_judge.py --mic 4            # choose the microphone

Then open the controller from a laptop on the same network:
    http://<pi address>:5000

AI Disclaimer: partially written with help from AI (Claude Code): the audio,
screen, button and web controller code, and checking that it runs without
errors. The Mini Judge concept, the storyboard and the charger case are ours;
the food and chores cases were suggested by AI, and the judge's lines for all
three cases were drafted with AI help.
"""

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import adafruit_rgb_display.st7789 as st7789
import board
import digitalio
import numpy as np
import sherpa_onnx
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from flask import Flask, jsonify, render_template, request
from piper import PiperVoice
from PIL import Image, ImageDraw, ImageFont

from cases import CASES, OPENING, SHARED, VERDICT_TITLES

SAMPLE_RATE = 16000
HERE = Path(__file__).resolve().parent
LAB_DIR = HERE.parent
VAD_MODEL = LAB_DIR / "models" / "silero_vad.onnx"
VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
SESSIONS_DIR = HERE / "sessions"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
LISTEN_TIMEOUT = 30
SUBTITLE_TOP = 48

# Background and text color for every state, so the screen alone tells the
# participant whose turn it is. Verdict colors never reuse a turn color, so a
# FAIR verdict is not mistaken for LISTENING.
COLORS = {
    "idle": ((20, 24, 48), (210, 210, 230)),
    "speaking": ((110, 75, 10), (255, 238, 190)),
    "listening": ((10, 95, 45), (225, 255, 230)),
    "thinking": ((65, 35, 100), (238, 225, 255)),
    "unfair": ((140, 20, 20), (255, 225, 225)),
    "fair": ((25, 70, 150), (225, 235, 255)),
    "split": ((70, 70, 78), (235, 235, 240)),
}


class Screen:
    """The Mini PiTFT, set up the same way as in Lab 2."""

    def __init__(self):
        spi = board.SPI()
        self.disp = st7789.ST7789(
            spi,
            cs=digitalio.DigitalInOut(board.D5),
            dc=digitalio.DigitalInOut(board.D25),
            rst=None,
            baudrate=64000000,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
        )
        self.width, self.height = self.disp.height, self.disp.width
        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.fonts = {}
        self.lock = threading.Lock()

        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True

    def font(self, size):
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(FONT, size)
        return self.fonts[size]

    def wrap(self, text, font, max_width):
        lines, line = [], ""
        for word in text.split():
            trial = f"{line} {word}".strip()
            if self.draw.textlength(trial, font=font) <= max_width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    def layout(self, subtitle):
        """Picks the largest text size at which the whole subtitle fits."""
        for size in (16, 14, 12):
            lines = self.wrap(subtitle, self.font(size), self.width - 16)
            step = size + 4
            if len(lines) * step <= self.height - SUBTITLE_TOP:
                return size, lines, True
        return size, lines[: (self.height - SUBTITLE_TOP) // step], False

    def show(self, color, title, subtitle=""):
        background, ink = COLORS[color]
        with self.lock:
            self.draw.rectangle((0, 0, self.width, self.height), fill=background)

            # Shrink long titles until they fit across the screen
            size = 30
            while size > 16 and self.draw.textlength(title, font=self.font(size)) > self.width - 12:
                size -= 2
            self.draw.text((self.width // 2, 8), title, font=self.font(size), fill=ink, anchor="mt")

            size, lines, _ = self.layout(subtitle)
            y = SUBTITLE_TOP
            for line in lines:
                self.draw.text((self.width // 2, y), line, font=self.font(size), fill=ink, anchor="mt")
                y += size + 4

            self.disp.image(self.image, 90)


class Judge:
    """Runs one job at a time: speak a line, then listen, think or rule."""

    def __init__(self, args, screen):
        self.screen = screen
        self.mic = args.mic
        self.speaker = args.speaker
        self.whisper = WhisperModel(args.model, device="cpu", compute_type="int8")
        self.voice = PiperVoice.load(str(VOICE))

        self.jobs = queue.Queue()
        self.cancel = threading.Event()
        self.lock = threading.Lock()
        self.busy = False
        self.state = "idle"
        self.title = ""
        self.subtitle = ""
        self.transcript = []
        self.session = None
        self.turn = 0
        self.go_idle()

    # ---- state the controller and the screen both read ----

    def set_state(self, state, title, subtitle="", color=None):
        with self.lock:
            self.state, self.title, self.subtitle = state, title, subtitle
        self.screen.show(color or state, title, subtitle)

    def go_idle(self):
        self.set_state("idle", "MINI JUDGE", "Press the top button to file a complaint.")

    def snapshot(self):
        with self.lock:
            return {
                "state": self.state,
                "busy": self.busy,
                "title": self.title,
                "subtitle": self.subtitle,
                "transcript": self.transcript[-60:],
            }

    def submit(self, job):
        with self.lock:
            if self.busy:
                return False
            self.busy = True
        self.jobs.put(job)
        return True

    # ---- the dataset: every turn goes to sessions/<time>/ ----

    def open_session(self):
        self.session = SESSIONS_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
        self.session.mkdir(parents=True, exist_ok=True)
        self.turn = 0
        with self.lock:
            self.transcript = []

    def record(self, who, text, audio=None):
        entry = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "who": who,
            "text": text,
        }
        if audio is not None:
            self.turn += 1
            entry["audio"] = f"turn_{self.turn:02d}.wav"
            sf.write(self.session / entry["audio"], audio, SAMPLE_RATE)
        with open(self.session / "log.jsonl", "a", encoding="utf-8") as log:
            log.write(json.dumps(entry) + "\n")
        with self.lock:
            self.transcript.append(entry)

    # ---- speaking and listening ----

    def speak(self, text, color="speaking", title="THE JUDGE"):
        self.set_state("speaking", title, text, color)
        self.record("judge", text)
        for chunk in self.voice.synthesize(text):
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            sd.play(audio, samplerate=chunk.sample_rate, device=self.speaker)
            sd.wait()
        time.sleep(0.2)  # let the room go quiet so the mic does not hear the judge

    def listen(self, silence):
        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(VAD_MODEL)
        config.silero_vad.min_silence_duration = silence
        config.silero_vad.min_speech_duration = 0.25
        config.sample_rate = SAMPLE_RATE
        vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
        window = config.silero_vad.window_size

        self.cancel.clear()
        self.set_state("listening", "LISTENING", "Your turn. Pause when you are done.")
        buffer = np.empty(0, dtype=np.float32)
        deadline = time.monotonic() + LISTEN_TIMEOUT

        with sd.InputStream(device=self.mic, channels=1, dtype="float32",
                            samplerate=SAMPLE_RATE) as stream:
            while time.monotonic() < deadline and not self.cancel.is_set():
                chunk, _ = stream.read(int(0.1 * SAMPLE_RATE))
                buffer = np.concatenate([buffer, chunk.reshape(-1)])

                while len(buffer) > window:
                    vad.accept_waveform(buffer[:window])
                    buffer = buffer[window:]

                while not vad.empty():
                    utterance = np.array(vad.front.samples, dtype=np.float32)
                    vad.pop()
                    self.set_state("thinking", "THINKING...", "")
                    segments, _ = self.whisper.transcribe(utterance, beam_size=1)
                    text = " ".join(s.text.strip() for s in segments).strip()
                    if text:
                        self.record("participant", text, utterance)
                        return
                    # Only noise: go back to listening
                    self.set_state("listening", "LISTENING", "Your turn. Pause when you are done.")

        self.record("system", "cancelled by wizard" if self.cancel.is_set() else "no answer")

    # ---- the worker ----

    def run(self):
        while True:
            job = self.jobs.get()
            try:
                self.handle(job)
            except Exception as error:  # keep the court open if one turn fails
                print(f"Job failed: {error!r}", file=sys.stderr)
                self.set_state("thinking", "ONE MOMENT", "The court had a technical difficulty.")
            finally:
                with self.lock:
                    self.busy = False

    def handle(self, job):
        if self.session is None:
            self.open_session()
        then = job["then"]

        if then == "verdict":
            title = VERDICT_TITLES[job["verdict"]]
            self.speak(job["text"], color=job["verdict"], title=title)
            self.set_state("verdict", title, job["text"], job["verdict"])
            return

        self.speak(job["text"])

        if then == "listen":
            self.listen(job["silence"])
            self.set_state("thinking", "THINKING...", "The court is considering your answer.")
        elif then == "deliberate":
            self.set_state("thinking", "THINKING...", "The court is considering this dispute.")
            time.sleep(job["seconds"])
        elif then == "adjourn":
            self.session = None
            self.go_idle()
        else:
            self.set_state("thinking", "THINKING...", "")


def watch_button(judge):
    """Opens court when the top button is pressed, once per press."""
    button = digitalio.DigitalInOut(board.D23)
    button.switch_to_input(pull=digitalio.Pull.UP)
    armed = True
    while True:
        pressed = not button.value  # the pull up makes it read False while held
        if not pressed:
            armed = True
        elif judge.state != "idle":
            armed = False  # a press during a case must not carry over to the next one
        elif armed and judge.submit(dict(OPENING)):
            armed = False
        time.sleep(0.02)


app = Flask(__name__)
judge = None

THEN = {"listen", "think", "deliberate", "verdict", "adjourn"}


@app.get("/")
def controller():
    return render_template("controller.html", cases=CASES, shared=SHARED,
                           verdict_titles=VERDICT_TITLES)


@app.get("/state")
def state():
    return jsonify(judge.snapshot())


@app.post("/say")
def say():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    then = data.get("then", "think")
    if not text or then not in THEN:
        return jsonify(ok=False, error="bad request"), 400
    if then == "verdict" and data.get("verdict") not in VERDICT_TITLES:
        return jsonify(ok=False, error="unknown verdict"), 400

    try:
        silence = min(max(float(data.get("silence", 1.5)), 0.2), 3.0)
        seconds = min(max(float(data.get("seconds", 3)), 0.0), 10.0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad number"), 400

    job = {"text": text, "then": then, "verdict": data.get("verdict"),
           "silence": silence, "seconds": seconds}
    if not judge.submit(job):
        return jsonify(ok=False, error="the judge is busy"), 409
    return jsonify(ok=True)


@app.post("/cancel")
def cancel():
    judge.cancel.set()
    return jsonify(ok=True)


def main():
    global judge
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="tiny.en", help="whisper model size")
    parser.add_argument("--mic", default=None,
                        help="input device index or name (default: system default)")
    parser.add_argument("--speaker", default=None,
                        help="output device index or name (default: system default)")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    # sounddevice wants an int for a device index, a string for a name
    for name in ("mic", "speaker"):
        value = getattr(args, name)
        if value is not None and value.isdigit():
            setattr(args, name, int(value))

    for path, what in [(VAD_MODEL, "VAD model"), (VOICE, "Piper voice")]:
        if not path.is_file():
            sys.exit(f"{what} not found at {path}. Run speech-scripts/setup.sh first.")

    print("Loading models...", flush=True)
    screen = Screen()
    screen.show("thinking", "STARTING", "Loading the court...")
    judge = Judge(args, screen)

    threading.Thread(target=judge.run, daemon=True).start()
    threading.Thread(target=watch_button, args=(judge,), daemon=True).start()

    addresses = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split()
    print("\nWizard controller:")
    for address in addresses:
        host = f"[{address}]" if ":" in address else address
        print(f"  http://{host}:{args.port}")
    print()

    # "::" accepts both IPv6 and IPv4 on the Pi; fall back to IPv4 only if IPv6 is off
    try:
        app.run(host="::", port=args.port, threaded=True, use_reloader=False)
    except OSError:
        app.run(host="0.0.0.0", port=args.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCourt adjourned.")
