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

# Colors at noon, at sunrise/sunset, and at midnight
SKY = ((110, 190, 255), (230, 120, 80), (8, 10, 35))
BODY = ((255, 235, 60), (255, 140, 40), (225, 225, 240))
GROUND = ((60, 120, 50), (35, 70, 35), (10, 25, 20))

random.seed(7)
STARS = [(random.randrange(width), random.randrange(HORIZON)) for _ in range(30)]


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def blend(colors, moonness):
    # Noon -> sunset colors during the day, sunset -> midnight colors at night
    noon, dusk, night = colors
    if moonness < 0.5:
        return lerp(noon, dusk, (moonness * 2) ** 2)  # stay bright most of the day
    return lerp(dusk, night, math.sqrt(moonness * 2 - 1))  # get dark quickly


def draw_scene(progress):
    # progress: 0 = sunrise, 0.25 = noon, 0.5 = sunset, 0.75 = midnight, 1 = sunrise again
    # The sun goes left -> right during the day, the moon comes back right -> left at night
    angle = math.pi * abs(1 - 2 * progress)
    x = CX + R * math.cos(angle)
    y = HORIZON - R * math.sin(angle)

    # moonness: 0 at noon (full sun) -> 0.5 at sunrise/sunset -> 1 at midnight (moon)
    moonness = (1 - math.sin(2 * math.pi * progress)) / 2
    sky, body = blend(SKY, moonness), blend(BODY, moonness)
    r = 12 + 6 * (1 - moonness)  # biggest at noon

    draw.rectangle((0, 0, width, height), fill=sky)

    # Stars fade in as the night deepens
    if moonness > 0.6:
        star = lerp(sky, (255, 255, 255), (moonness - 0.6) / 0.4)
        for star_x, star_y in STARS:
            draw.point((star_x, star_y), fill=star)

    # Dotted half circle track
    track = lerp(sky, (255, 255, 255), 0.35)
    for deg in range(0, 181, 6):
        a = math.radians(deg)
        draw.point((CX + R * math.cos(a), HORIZON - R * math.sin(a)), fill=track)

    # Sun glow and rays: strongest at noon, gone by sunset
    glow = 1 - 2 * moonness
    if glow > 0:
        gr = r + 8 * glow
        draw.ellipse((x - gr, y - gr, x + gr, y + gr), fill=lerp(sky, (255, 255, 255), 0.35 * glow))
        for k in range(8):
            a = k * math.pi / 4
            r1, r2 = r + 4, r + 4 + 10 * glow
            draw.line((x + r1 * math.cos(a), y + r1 * math.sin(a),
                       x + r2 * math.cos(a), y + r2 * math.sin(a)), fill=body, width=2)

    draw.ellipse((x - r, y - r, x + r, y + r), fill=body)

    # After sunset, a sky-colored circle slides over the body to carve out a crescent
    if moonness > 0.5:
        offset = r * (2 - 1.4 * (moonness * 2 - 1))
        sx, sy = x + offset, y - offset * 0.3
        draw.ellipse((sx - r, sy - r, sx + r, sy + r), fill=sky)

    # Ground drawn last so the sun and moon rise out from behind it
    draw.rectangle((0, HORIZON, width, height), fill=blend(GROUND, moonness))


start = time.monotonic()

while True:
    progress = ((time.monotonic() - start) / DAY_SECONDS) % 1
    draw_scene(progress)
    disp.image(image, rotation)
    time.sleep(0.02)
