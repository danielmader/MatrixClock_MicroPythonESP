# MatrixClock_MicropythonESP
A simple clock for a 64x32 HUB75 LED matrix display with scheduled NTP sync and Sensirion SHT40 ambient sensor.

The display (23,95€) is from WaveShare (and was much cheaper than the similar product from Adafruit):
- https://www.waveshare.com/wiki/RGB-Matrix-P4-64x32
- https://eckstein-shop.de/WaveShare-RGB-Full-Color-LED-Matrix-Panel-64x32-Pixels-4mm-Pitch-Adjustable-Brightness

Here I've found very valuable information about how to use this kind of display:
- https://www.bigmessowires.com/2018/05/24/64-x-32-led-matrix-programming/
- https://www.sparkfun.com/news/2650

Interestingly enough, the display can be used without power supply, i.e. the small current fed into the HUB75 connector is enough to have the red pixels light up dimly, which is perfect for my use case as a night clock. During daytime, I'll turn on the 5V DC supply using a relay (yet to be implemented). The color of the display is yellow, which is a combination of red and green.

The 5V power supply is converted from a 12V power supply using this handy little DC-DC step-down converter (3.50€) with 10W output (15W max):
- https://eckstein-shop.de/LM2596SDC-DCeinstellbarerStep-DownSpannungsreglermitLED-VoltmeterAdjustablePowerModul

The sensor (7.95€) came on a convenient break-out board from Adafruit:
- https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor
- https://eckstein-shop.de/AdafruitSensirionSHT40Temperature26HumiditySensor-STEMMAQT2FQwiic

This project requires [Ben Emmett's Hub75MicroPython](https://github.com/benjohnemmett/Hub75MicroPython) library, which is perfectly suitable for a simple MicroPython-only application.

The flicker when the screen objects are changed is noticable, but acceptable every minute.

```
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:37:30 2023

@author: mada
"""

import hub75
import matrixdata
from logo import logo

import _thread
from machine import Timer
#import uasyncio

ROW_SIZE = 32
COL_SIZE = 64

config = hub75.Hub75SpiConfiguration()
##-----------------------------------------------------------------------------
## row select pins
config.line_select_a_pin_number = 15
config.line_select_b_pin_number = 2
config.line_select_c_pin_number = 4
config.line_select_d_pin_number = 16
config.line_select_e_pin_number = 12
## color data pins
config.red1_pin_number = 32
config.green1_pin_number = 33
config.blue1_pin_number = 25
config.red2_pin_number = 26
config.green2_pin_number = 27
config.blue2_pin_number = 14
## logic pins
config.clock_pin_number = 18
config.latch_pin_number = 5
config.output_enable_pin_number = 17  # active low
config.spi_miso_pin_number = 13  # not connected
## misc
config.illumination_time_microseconds = 1
##-----------------------------------------------------------------------------
matrix = matrixdata.MatrixData(ROW_SIZE, COL_SIZE)
hub75spi = hub75.Hub75Spi(matrix, config)

# Show Python Logo
matrix.set_pixels(0, 16, logo)
for i in range(100):
    hub75spi.display_data()

##-----------------------------------------------------------------------------
## run permanent display thread
def displayThread():
    while True:
        hub75spi.display_data()

_thread.start_new_thread(displayThread, ())

##-----------------------------------------------------------------------------
## run timed thread
square = [
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7]]

def clocktick(timer):
    matrix.clear_dirty_bytes()
    ## TODO: faster way to reset all pixels
    # matrix.clear_all_bytes()
    matrix.set_pixels(0,0, square)
    matrix.set_pixels(0,25, square)
    matrix.set_pixels(0,50, square)

tim = Timer(0)
tim.init(period=1000, mode=Timer.PERIODIC, callback=clocktick)
```
