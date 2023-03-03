#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:37:30 2023

@author: mada
@version: 2023-03-02
"""

import hub75
import matrixdata
from logo import logo

import uasyncio as asyncio
import utime as time

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
matrix.clear_dirty_bytes()

##-----------------------------------------------------------------------------
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

async def set_pixels(lock):

    def _seconds():
        return time.localtime()[5]

    while True:
        ## wait for released lock
        await lock.acquire()

        if _seconds() % 10 < 5:
            matrix.record_dirty_bytes = False
            reset = matrix.clear_all_bytes
        else:
            matrix.record_dirty_bytes = True
            reset = matrix.clear_dirty_bytes
        print(reset.__name__, matrix.record_dirty_bytes)
        reset()
        matrix.set_pixels(0,0, square)
        matrix.set_pixels(0,25, square)
        matrix.set_pixels(0,50, square)

        ## release lock
        lock.release()
        await asyncio.sleep(0)

async def refresh_display(lock):
    while True:
        await lock.acquire()
        hub75spi.display_data()
        lock.release()
        await asyncio.sleep(0)

async def main():
    ## create the Lock instance
    lock = asyncio.Lock()
    ## create co-routines (cooperative tasks)
    asyncio.create_task(refresh_display(lock))
    asyncio.create_task(set_pixels(lock))
    await asyncio.sleep(30)  # run for 30s

try:
    asyncio.run(main())
finally:
    ## clear retained state
    _ = asyncio.new_event_loop()
