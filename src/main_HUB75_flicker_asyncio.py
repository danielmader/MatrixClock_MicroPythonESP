#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:37:30 2023

@author: mada
@version: 2023-03-06
"""

import hub75
import matrixdata

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

##-----------------------------------------------------------------------------
rect_14x32 = [
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

rect_64x32_w = [ [7] * 64] * 32
rect_64x32_r = [ [4] * 64] * 32
rect_64x32_g = [ [2] * 64] * 32
rect_64x32_b = [ [1] * 64] * 32
      
##-----------------------------------------------------------------------------
async def setpixel1(lock):
    '''
    Clear matrix pixels in two ways:
        * only dirty pixels
        * all pixels
    Set images.
    '''
    def _seconds():
        return time.localtime()[5]

    print("\n>> Clear matrix demo ...")
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
        matrix.set_pixels(0,0, rect_14x32)
        matrix.set_pixels(0,25, rect_14x32)
        matrix.set_pixels(0,50, rect_14x32)

        ## release lock
        lock.release()
        
        await asyncio.sleep(0)  # round-robin scheduling

##-----------------------------------------------------------------------------
async def setpixel2(lock):
    '''
    Clear matrix pixels and set new image.
    '''
    print("\n>> Flicker demo ...")
    for pattern in (rect_64x32_r, rect_64x32_g, rect_64x32_b, rect_64x32_w):
        ## wait for released lock
        await lock.acquire()
        
        matrix.clear_all_bytes()
        matrix.set_pixels(0,0, pattern)
        
        ## release lock
        lock.release()
        
        await asyncio.sleep(15)  # pause for 15s

##-----------------------------------------------------------------------------
async def refresh(lock):
    while True:
        await lock.acquire()
        hub75spi.display_data()
        lock.release()
        await asyncio.sleep(0)

##-----------------------------------------------------------------------------
async def main():
    ## create the Lock instance
    lock = asyncio.Lock()

    ## create co-routines (cooperative tasks)
    asyncio.create_task(refresh(lock))   

    ## 1) demonstrate speed of clear*() methods
    task1 = asyncio.create_task(setpixel1(lock))
    await asyncio.sleep(20)  # pause for 20s
    task1.cancel()
    
    ## 2) show general flicker even without parallel tasks
    task2 = asyncio.create_task(setpixel2(lock))      
    await asyncio.sleep(60)  # pause for 60s
    task2.cancel()
    print("\n>> Done.")

##-----------------------------------------------------------------------------
try:
    asyncio.run(main())
finally:
    ## clear retained state
    _ = asyncio.new_event_loop()
