import time

import adafruit_displayio_ssd1306
import board
import busio
import displayio
import usb_cdc
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_progressbar.verticalprogressbar import HorizontalProgressBar
from digitalio import DigitalInOut, Direction, Pull

import config

# serial port
serial = usb_cdc.data
uart = busio.UART(board.GP4, board.GP5, baudrate=115200)

if config.serialUART is True:
    serial = uart

# release displays
displayio.release_displays()

# Our reset button
btn = DigitalInOut(board.GP15)
btn.direction = Direction.INPUT
btn.pull = Pull.UP

# Create the I2C interface for the oled
i2c2 = busio.I2C(scl=board.GP21, sda=board.GP20)

# Display bus
display_bus = displayio.I2CDisplay(i2c2, device_address=60)
display = adafruit_displayio_ssd1306.SSD1306(
    display_bus, width=128, height=64, rotation=180
)
display.brightness = 0.01

# Fonts
small_font = "fonts/Roboto-Medium-16.bdf"
#  glyphs for fonts
glyphs = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-,.: "
#  loading bitmap fonts
small_font = bitmap_font.load_font(small_font)
small_font.load_glyphs(glyphs)

# Display content
splash = displayio.Group()
display.root_group = splash

# Progress bar
prog_bar = HorizontalProgressBar((1, 1), (127, 18))
splash.append(prog_bar)

# Steps head
steps_head = Label(small_font, text=config.head)
steps_head.x = 28
steps_head.y = 10

# Steps taken
text_input = Label(small_font, text="Init...")
text_input.x = 1
text_input.y = 34

# Steps per hour
text_bottom = Label(small_font, text=config.bottom)
text_bottom.x = 1
text_bottom.y = 58

# Add to display
splash.append(text_bottom)
splash.append(steps_head)
splash.append(text_input)


def recvSerial():
    if serial is not None:
        if config.serialUART is False:
            if serial.connected:
                if serial.in_waiting > 0:
                    return serial.read(serial.in_waiting)
                else:
                    return None
        else:
            if serial.in_waiting > 0:
                letter = serial.read(serial.in_waiting)
                return letter
            else:
                return None


def sendSerial(data):
    serial.write(data)


buf = ""
reset_pending = False
reset_mono = time.monotonic()
last_input = "Booting..."
brightness_pending = True
brightness_mono = time.monotonic()

while True:
    input = recvSerial()
    if input is not None:
        buf = buf + input.decode("utf-8")
        if input == b"\r":
            text_input.text = buf
            last_input = buf
            print(last_input)
            buf = ""
            display.wake()
            display.brightness = 1
            brightness_pending = True
            brightness_mono = time.monotonic()
    if btn.value is False:
        display.wake()
        display.brightness = 1
        brightness_pending = True
        brightness_mono = time.monotonic()
        reset_prog = int(((time.monotonic() - reset_mono) / 5) * 100)
        if reset_prog > 100:
            reset_prog = 100
        prog_bar.progress = float(reset_prog)
        text_input.text = "Keep pressing"
        if reset_prog == 100:
            text_input.text = "Shuting down ..."
            last_input = "Shutting down ..."
            sendSerial(bytes("shutdown\r\n", "ascii"))
            prog_bar.progress = float(0)
            reset_pending = False
            while btn.value is False:
                time.sleep(0.001)
    else:
        prog_bar.progress = float(0)
        text_input.text = last_input
        reset_mono = time.monotonic()
    if brightness_pending is True and (
        int(time.monotonic() - brightness_mono) > config.dimTime
    ):
        display.brightness = 0.01
    if brightness_pending is True and (
        int(time.monotonic() - brightness_mono) > config.sleepTime
    ):
        # display.sleep()
        brightness_pending = False
