import math
import time
import digitalio
import board
from PIL import Image, ImageDraw
import adafruit_rgb_display.st7789 as st7789

# Sun & Moon clock, barebones version: one circle in the middle of the screen
# that turns from the sun into the moon and back again.
#   start of the day -> a full yellow sun
#   middle of the day -> a white crescent moon
# Nothing moves and nothing else is drawn.
#
# AI Disclaimer: partially written with help from AI (Claude Code): the colors,
# the math that turns the sun into a crescent, and checking that the script runs
# without errors.

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

BACKGROUND = (0, 0, 0)
SUN = (255, 235, 60)
MOON = (225, 225, 240)

# The circle sits in the middle of the screen and never moves
CX, CY, RADIUS = width // 2, height // 2, 45


def draw_scene(progress):
    # moonness: 0 is a full sun, 1 is a crescent moon
    moonness = (1 - math.cos(2 * math.pi * progress)) / 2

    draw.rectangle((0, 0, width, height), fill=BACKGROUND)

    # The sun's yellow fades into the moon's white
    color = tuple(int(SUN[i] + (MOON[i] - SUN[i]) * moonness) for i in range(3))
    draw.ellipse((CX - RADIUS, CY - RADIUS, CX + RADIUS, CY + RADIUS), fill=color)

    # Past the halfway point a background colored circle slides across to bite
    # a crescent out of it
    if moonness > 0.5:
        shift = RADIUS * (2 - 1.4 * (moonness * 2 - 1))
        draw.ellipse(
            (CX + shift - RADIUS, CY - RADIUS, CX + shift + RADIUS, CY + RADIUS),
            fill=BACKGROUND,
        )


start = time.monotonic()

while True:
    progress = ((time.monotonic() - start) / DAY_SECONDS) % 1
    draw_scene(progress)
    disp.image(image, rotation)
    time.sleep(0.02)
