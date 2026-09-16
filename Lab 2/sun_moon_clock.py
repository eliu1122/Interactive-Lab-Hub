import math
import random
import time
import digitalio
import board
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789

# Sun & Moon clock (version 1: animation only, not tied to the real time yet)
# The body travels along a half circle above the horizon:
#   sunrise  -> left end, the sun rises out of the ground
#   noon     -> top of the arc, the sun is at its biggest and brightest
#   sunset   -> right end, it fades and starts turning into the moon
#   midnight -> top of the arc again, now a crescent moon heading back left
#   dawn     -> back on the left, the moon turns back into the sun
#
# AI Disclaimer: partially written with help from AI (Claude Code): the visuals,
# the coordinates along the half circle, smoothing the animation, and checking
# that the script runs without errors.

# How many seconds one full day takes in the animation
DAY_SECONDS = 12

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

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Half circle track sitting on the horizon
CX, HORIZON = width // 2, 120
R = 86

# Colors
NOON_SKY = (110, 190, 255)
DUSK_SKY = (230, 120, 80)
NIGHT_SKY = (8, 10, 35)
SUN_NOON = (255, 235, 60)
SUN_LOW = (255, 140, 40)
MOON = (225, 225, 240)
DAY_GROUND = (60, 120, 50)
NIGHT_GROUND = (10, 25, 20)

random.seed(7)
STARS = [(random.randrange(width), random.randrange(HORIZON)) for _ in range(30)]


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_scene(progress):
    # progress: 0 = sunrise, 0.25 = noon, 0.5 = sunset, 0.75 = midnight, 1 = sunrise again
    if progress < 0.5:
        angle = math.pi * (1 - progress * 2)  # sun goes left -> right
    else:
        angle = math.pi * (progress - 0.5) * 2  # moon goes right -> left
    x = CX + R * math.cos(angle)
    y = HORIZON - R * math.sin(angle)

    # moonness: 0 at noon (full sun) -> 0.5 at sunrise/sunset -> 1 at midnight (moon)
    moonness = (1 - math.sin(2 * math.pi * progress)) / 2
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

    # Dotted half circle track
    track = lerp(sky, (255, 255, 255), 0.35)
    for deg in range(0, 181, 6):
        a = math.radians(deg)
        draw.point((CX + R * math.cos(a), HORIZON - R * math.sin(a)), fill=track)

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

    # Ground drawn last so the sun and moon rise out from behind it
    draw.rectangle((0, HORIZON, width, height), fill=lerp(DAY_GROUND, NIGHT_GROUND, moonness))


start = time.monotonic()

while True:
    progress = ((time.monotonic() - start) / DAY_SECONDS) % 1
    draw_scene(progress)
    disp.image(image, rotation)
    time.sleep(0.02)
