import math
import random
import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# Sun & Moon clock: a body travels around an oval track once per day.
#   6 AM  -> left of the oval (sunrise)
#   12 PM -> top of the oval, the sun is at its biggest and brightest
#   6 PM  -> right of the oval (sunset)
#   12 AM -> bottom of the oval, it has fully turned into a crescent moon
# Hold button A to fast-forward through the day (handy for the demo video).

# Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 64000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the ST7789 display:
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

# Create blank image for drawing.
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Buttons are active-LOW because of pull-ups
buttonA = digitalio.DigitalInOut(board.D23)
buttonA.switch_to_input(pull=digitalio.Pull.UP)

# Oval track
CX, CY = width // 2, height // 2 + 6
RX, RY = 95, 42

# Colors
NOON_SKY = (110, 190, 255)
DUSK_SKY = (230, 120, 80)
NIGHT_SKY = (8, 10, 35)
SUN_NOON = (255, 235, 60)
SUN_LOW = (255, 140, 40)
MOON = (225, 225, 240)

random.seed(7)
STARS = [(random.randrange(width), random.randrange(height)) for _ in range(30)]


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_scene(hours):
    # Angle around the oval: 0 = midnight (bottom), increases through left, top, right.
    theta = 2 * math.pi * hours / 24
    x = CX - RX * math.sin(theta)
    y = CY + RY * math.cos(theta)

    # moonness: 0 at noon (full sun) -> 0.5 at sunrise/sunset -> 1 at midnight (moon)
    moonness = (1 + math.cos(theta)) / 2
    brightness = max(0.0, 1 - 2 * moonness)  # sun glow, strongest at noon

    if moonness < 0.5:
        t = (moonness * 2) ** 2  # stay blue most of the day, warm up near sunset
        sky = lerp(NOON_SKY, DUSK_SKY, t)
        body = lerp(SUN_NOON, SUN_LOW, t)
    else:
        sky = lerp(DUSK_SKY, NIGHT_SKY, math.sqrt((moonness - 0.5) * 2))  # get dark quickly
        body = lerp(SUN_LOW, MOON, (moonness - 0.5) * 2)

    draw.rectangle((0, 0, width, height), fill=sky)

    # Stars fade in as the night deepens
    if moonness > 0.6:
        star = lerp(sky, (255, 255, 255), (moonness - 0.6) / 0.4)
        for sx, sy in STARS:
            draw.point((sx, sy), fill=star)

    # Dotted oval track
    track = lerp(sky, (255, 255, 255), 0.35)
    for deg in range(0, 360, 6):
        a = math.radians(deg)
        draw.point((CX + RX * math.cos(a), CY + RY * math.sin(a)), fill=track)

    # The sun is bigger at noon and shrinks as it turns into the moon
    r = 12 + 6 * (1 - moonness)

    # Glow rings and rays, only while it is still a sun
    if brightness > 0:
        for i in (3, 2, 1):
            rr = r + i * 5 * brightness
            glow = lerp(sky, body, 0.3 * (4 - i) / 3 * brightness)
            draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=glow)
        for k in range(8):
            a = k * math.pi / 4
            r1, r2 = r + 4, r + 4 + 10 * brightness
            draw.line((x + r1 * math.cos(a), y + r1 * math.sin(a),
                       x + r2 * math.cos(a), y + r2 * math.sin(a)), fill=body, width=2)

    # Body, with a shadow that carves out a crescent after sunset
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((x - r, y - r, x + r, y + r), fill=255)
    if moonness > 0.5:
        k = (moonness - 0.5) * 2
        offset = r * (2 - 1.4 * k)
        sx, sy = x + offset, y - offset * 0.3
        mask_draw.ellipse((sx - r, sy - r, sx + r, sy + r), fill=0)
    image.paste(body, (0, 0, width, height), mask)

    # Time in the middle of the oval
    h, m = int(hours) % 24, int(hours * 60) % 60
    label = "%d:%02d %s" % (h % 12 or 12, m, "AM" if h < 12 else "PM")
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    luminance = 0.299 * sky[0] + 0.587 * sky[1] + 0.114 * sky[2]
    text_color = (20, 30, 60) if luminance > 140 else (240, 240, 255)
    draw.text((CX - (right - left) / 2, CY - (bottom - top) / 2 - top), label, font=font, fill=text_color)


demo_hours = None

while True:
    if not buttonA.value:
        now = time.localtime()
        if demo_hours is None:
            demo_hours = now.tm_hour + now.tm_min / 60
        demo_hours = (demo_hours + 0.25) % 24  # a full day in ~10 seconds
        hours = demo_hours
    else:
        demo_hours = None
        now = time.localtime()
        hours = now.tm_hour + now.tm_min / 60 + now.tm_sec / 3600

    draw_scene(hours)
    disp.image(image, rotation)
    time.sleep(0.02 if demo_hours is not None else 1)
