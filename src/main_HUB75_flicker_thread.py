# -*- coding: utf-8 -*-

"""
Main script to demo HUB75 refresh rate.

@author: mada
@version: 2023-03-01
"""

import hub75
import matrixdata
from logo import logo

import _thread
from machine import Timer

import time

##*****************************************************************************
##*****************************************************************************

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
matrix = matrixdata.MatrixData(row_size=32, col_size=64)
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
# run timed thread
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

def seconds():
    return time.localtime()[5]

def clocktick(timer):
    if seconds() % 10 < 5:
        matrix.record_dirty_bytes = False
        reset = matrix.clear_all_bytes
    else:
        matrix.record_dirty_bytes = True
        reset = matrix.clear_dirty_bytes
    # print(reset.__name__, matrix.record_dirty_bytes)
    reset()
    matrix.set_pixels(0,0, square)
    matrix.set_pixels(0,25, square)
    matrix.set_pixels(0,50, square)

tim0 = Timer(0)
tim0.init(period=500, mode=Timer.PERIODIC, callback=clocktick)

## prevent exit to see the prints
while True:
    pass
