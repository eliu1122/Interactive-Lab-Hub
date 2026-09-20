import math
import random
import time
import digitalio
import board
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789

# Sun & Moon clock, barebones version: the animation only, with nothing to press.
# The sun and moon travel along a half circle above the horizon:
#   sunrise  -> left end of the arc
#   noon     -> top of the arc
#   sunset   -> right end of the arc
#   midnight -> top of the arc again, now a crescent moon heading back left
# The sky, the ground and the body itself all change color along the way, and
# the stars fade in once night sets in.
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

# The half circle the sun and moon travel along, sitting on the horizon
CX, HORIZON, R = width // 2, 120, 86
BODY_R = 14

# Colors at noon, at sunrise and sunset, and at midnight
SKY = ((110, 190, 255), (230, 120, 80), (8, 10, 35))
BODY = ((255, 235, 60), (255, 140, 40), (225, 225, 240))
GROUND = ((60, 120, 50), (35, 70, 35), (10, 25, 20))

random.seed(7)
STARS = [(random.randrange(width), random.randrange(HORIZON)) for _ in range(30)]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def blend(colors, moonness):
    # moonness: 0 at noon, 0.5 at sunrise and sunset, 1 at midnight
    noon, dusk, night = colors
    if moonness < 0.5:
        return mix(noon, dusk, moonness * 2)
    return mix(dusk, night, moonness * 2 - 1)


def draw_scene(progress):
    # progress: 0 = sunrise, 0.25 = noon, 0.5 = sunset, 0.75 = midnight
    # The sun goes left to right during the day, the moon comes back at night
    angle = math.pi * abs(1 - 2 * progress)
    x = CX + R * math.cos(angle)
    y = HORIZON - R * math.sin(angle)
    moonness = (1 - math.sin(2 * math.pi * progress)) / 2

    sky = blend(SKY, moonness)
    draw.rectangle((0, 0, width, height), fill=sky)

    # Stars fade in as the night deepens
    if moonness > 0.6:
        star = mix(sky, (255, 255, 255), (moonness - 0.6) / 0.4)
        for star_x, star_y in STARS:
            draw.point((star_x, star_y), fill=star)

    # Dotted half circle track
    track = mix(sky, (255, 255, 255), 0.35)
    for degrees in range(0, 181, 6):
        a = math.radians(degrees)
        draw.point((CX + R * math.cos(a), HORIZON - R * math.sin(a)), fill=track)

    # The sun or moon itself
    draw.ellipse((x - BODY_R, y - BODY_R, x + BODY_R, y + BODY_R), fill=blend(BODY, moonness))

    # After sunset a sky colored circle slides over the body to carve out a crescent
    if moonness > 0.5:
        shift = BODY_R * (2 - 1.4 * (moonness * 2 - 1))
        draw.ellipse((x + shift - BODY_R, y - BODY_R, x + shift + BODY_R, y + BODY_R), fill=sky)

    # Ground drawn last so the sun and moon rise out from behind it
    draw.rectangle((0, HORIZON, width, height), fill=blend(GROUND, moonness))


start = time.monotonic()

while True:
    progress = ((time.monotonic() - start) / DAY_SECONDS) % 1
    draw_scene(progress)
    disp.image(image, rotation)
    time.sleep(0.02)
