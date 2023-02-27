#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 12:41:46 2023

@author: mada
@version: 2023-02-27

MatrixClock - an ESP32 driven HUB75 LED matrix clock.
* Synchronization with NTP.
* Temperature/humidity ambient sensor (Sensirion SHT40).
"""

## system modules
from machine import Timer
from machine import I2C
from machine import Pin

import ntptime
import uasyncio
import _thread
import utime as time
#import time

## 3rd party modules
import hub75
import matrixdata
from logo import logo

## custom modules
import wlan_helper  # => creds.py
import datetime_helper
import madFonts

##*****************************************************************************
##*****************************************************************************

## HUB75 LED matrix with custom pinout
config = hub75.Hub75SpiConfiguration()

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

ROW_SIZE = 32
COL_SIZE = 64

matrix = matrixdata.MatrixData(ROW_SIZE, COL_SIZE)
hub75spi = hub75.Hub75Spi(matrix, config)

## Show Python Logo
matrix.set_pixels(0, 16, logo)
for i in range(100):
    hub75spi.display_data()

## NTP sync interval ----------------------------------------------------------
ntp_interval = 3600 * 12 # 3600s = 60min = 1h
ts_ntpsync = 0
ts_clocktick = time.time()

## DEBUG mode -----------------------------------------------------------------
debug_mode = False
# debug_mode = True

## characters -----------------------------------------------------------------
big_blue = {
    '0' : madFonts.big0,
    '1' : madFonts.big1,
    '2' : madFonts.big2,
    '3' : madFonts.big3,
    '4' : madFonts.big4,
    '5' : madFonts.big5,
    '6' : madFonts.big6,
    '7' : madFonts.big7,
    '8' : madFonts.big8,
    '9' : madFonts.big9,
    '.' : madFonts.big_dot,
    ':' : madFonts.big_colon,
    '°' : madFonts.big_degree,
    '%' : madFonts.big_percent,
    ' ' : madFonts.big_space,
    '~' : madFonts.pixel_black,
}

small_blue = {
    '0' : madFonts.small0,
    '1' : madFonts.small1,
    '2' : madFonts.small2,
    '3' : madFonts.small3,
    '4' : madFonts.small4,
    '5' : madFonts.small5,
    '6' : madFonts.small6,
    '7' : madFonts.small7,
    '8' : madFonts.small8,
    '9' : madFonts.small9,
    '.' : madFonts.small_dot,
    ':' : madFonts.small_colon,
    '°' : madFonts.small_degree,
    '%' : madFonts.small_percent,
    ' ' : madFonts.small_space,
    '~' : madFonts.pixel_black,
}

big_yellow = {}
for char in big_blue:
    big_yellow[char] = []
    for i,row in enumerate(big_blue[char]):
        row = [col * 6 for col in row]  # yellow
        big_yellow[char].append(row)
small_yellow = {}
for char in small_blue:
    small_yellow[char] = []
    for i,row in enumerate(small_blue[char]):
        row = [col * 6 for col in row]  # yellow
        small_yellow[char].append(row)

## SHT40 temperature & pressure sensor ----------------------------------------
modes = (
    ("SERIAL_NUMBER", 0x89, "Serial number", 0.01),
    ("NOHEAT_HIGHPRECISION", 0xFD, "No heater, high precision", 0.01),
    ("NOHEAT_MEDPRECISION", 0xF6, "No heater, med precision", 0.005),
    ("NOHEAT_LOWPRECISION", 0xE0, "No heater, low precision", 0.002),
    ("HIGHHEAT_1S", 0x39, "High heat, 1 second", 1.1),
    ("HIGHHEAT_100MS", 0x32, "High heat, 0.1 second", 0.11),
    ("MEDHEAT_1S", 0x2F, "Med heat, 1 second", 1.1),
    ("MEDHEAT_100MS", 0x24, "Med heat, 0.1 second", 0.11),
    ("LOWHEAT_1S", 0x1E, "Low heat, 1 second", 1.1),
    ("LOWHEAT_100MS", 0x15, "Low heat, 0.1 second", 0.11),
    )
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
i2c_devs = i2c.scan()
print("\n>> found I2C devices:", i2c_devs)
sht40 = i2c_devs[0]
temp = 99.9
hum = 99.9

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def set_clock(ts_clocktick):
    '''
    Update time display.
    '''
    global temp
    global hum

    ##-------------------------------------------------------------------------
    ## assemble time and sensor strings
    localtime = datetime_helper.cettime(ts_clocktick)
    # if len(localtime) == 8:
    #     ## MicroPython
    #     year, month, mday, hour, minute, second, weekday, yearday = localtime
    # elif len(localtime) == 9:
    #     ## CPython
    #     year, month, mday, hour, minute, second, weekday, yearday, dst = localtime
    hour, minute, second = localtime[3:6]
    temp, hum = read_sensor()

    ## TODO: display full time when flickerfree
    # time_str = "{:02d}:{:02d}.{:02d}".format(hour, minute, second)
    time_str = "{:02d}:{:02d}".format(hour, minute)
    sensor_str = "{:4.1f}~° {:4.1f}~%".format(temp, hum)

    ## DEBUG
    # print("{} > {}".format(time_str, localtime[3:6]))
    # print("{}".format(sensor_str))

    ##-------------------------------------------------------------------------
    ## use darkmode during night time
    ## TODO: handle darkmode
    # if hour in [20,21,22,23,0,1,2,3,4,5,6]:
    #     darkmode = True
    # else:
    #     darkmode = False
    big = big_yellow
    small = small_yellow

    ##-------------------------------------------------------------------------
    ## assemble character images lists per line
    # time_display = []
    ## TODO: display full time when flickerfree
    # for char in time_str[:-3]:
    #     time_display.append(big[char])
    # for char in time_str[-3:]:
    #     time_display.append(small[char])
    time_display = []
    for char in time_str:
        time_display.append(big[char])

    sensor_display = []
    for char in sensor_str:
        sensor_display.append(small[char])

    ##-------------------------------------------------------------------------
    ## write out new pixel states
    # matrix.clear_dirty_bytes()
    matrix.clear_all_bytes()
    ## TODO: display full time when flickerfree
    # col = 4
    # for img in time_display[:-3]:
    #     matrix.set_pixels(5, col+1, img)
    #     col += len(img[0]) + 1
    # for img in time_display[-3:]:
    #     matrix.set_pixels(12, col+1, img)
    #     col += len(img[0]) + 1
    col = 10
    for img in time_display:
        matrix.set_pixels(5, col+1, img)
        col += len(img[0]) + 2

    col = 2
    for img in sensor_display:
        matrix.set_pixels(22, col+1, img)
        col += len(img[0]) + 1

##=============================================================================
def read_sensor():
    '''
    Read measurement data from Sensirion SHT40.

    Returns
    -------
    t_degC : float
    rh_pRH : float
    '''
    # print ("\n>> reading sensor data ...")
    mode =  modes[1]  # NOHEAT_HIGHPRECISION
    i2c.writeto(sht40, bytearray([mode[1]]))
    time.sleep(mode[-1])
    rx_bytes = i2c.readfrom(sht40, 6)
    # print('>', rx_bytes, len(rx_bytes))
    t_ticks = rx_bytes[0] * 256 + rx_bytes[1]
    rh_ticks = rx_bytes[3] * 256 + rx_bytes[4]
    t_degC = -45 + 175 * t_ticks/65535  # 2^16 - 1 = 65535
    rh_pRH = -6 + 125 * rh_ticks/65535
    if (rh_pRH > 100):
        rh_pRH = 100
    if (rh_pRH < 0):
        rh_pRH = 0
    # print('> temperature:', t_degC)
    # print('> humidity:', rh_pRH)
    return t_degC, rh_pRH

##-----------------------------------------------------------------------------
def clocktick(timer):
    '''
    Timed function to add one second.
    '''
    global ts_clocktick

    ## 1) increase clock counter
    ts_clocktick += 1

    ## 2) update status on OLED (if available)
    # update_oled()

    ## 3) update time display
    ## TODO: update time display every second (when flickerfree)
    if ts_clocktick % 60 == 0:
        set_clock(ts_clocktick)

##-----------------------------------------------------------------------------
## https://docs.micropython.org/en/latest/library/uasyncio.html
## https://gpiocc.github.io/learn/micropython/esp/2020/06/13/martin-ku-asynchronous-programming-with-uasyncio-in-micropython.html
async def sync_time_NTP():
    '''
    Resync with NTP.
    '''
    global ts_ntpsync
    global ts_clocktick
    global ntp_interval
    if debug_mode:
        ntp_interval = 50  # each 50s * 0.2 = each 10s

    while True:
        try:
            if (ts_ntpsync == 0) or (ts_clocktick - ts_ntpsync > ntp_interval):
                print('\n>> syncing with NTP ...')
                ## check connection status, and (re-)connect if required
                ts_delta_1 = ts_clocktick - time.time()
                wlan_helper.connect()
                ts_delta_2 = ts_clocktick - time.time()
                if not debug_mode:
                    ts_clocktick += (ts_delta_2 - ts_delta_1)

                if debug_mode:
                    ## get time
                    print('<< NTP timestamp:', ntptime.time())
                else:
                    ## set time
                    ntptime.settime()
                    ts_clocktick = time.time()
                    print('<< NTP timestamp:', ts_clocktick)
                ts_ntpsync = ts_clocktick

                ## update clock immediately after NTP sync
                set_clock(ts_ntpsync)
            else:
                pass

        except:
            print('!! NTP synchronization failed!')
        finally:
            ## sleep before checking again
            await uasyncio.sleep(5)

##-----------------------------------------------------------------------------
async def scheduled_sync():
    '''
    Scheduler function for NTP coroutine.
    '''
    # print("\n>> scheduling NTP sync ...")
    event_loop = uasyncio.get_event_loop()
    event_loop.create_task(sync_time_NTP())
    event_loop.run_forever()

##-----------------------------------------------------------------------------
def displayThread():
    while True:
        hub75spi.display_data()

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def main():
    global ts_ntpsync
    global ts_clocktick
    global temp
    global hum

    ##-------------------------------------------------------------------------
    ## init clock
    temp, hum = read_sensor()
    set_clock(ts_clocktick)

    ##-------------------------------------------------------------------------
    ## run display thread
    _thread.start_new_thread(displayThread, ())

    ##-------------------------------------------------------------------------
    ## init WiFi
    wlan_helper.init()

    ##-------------------------------------------------------------------------
    ## init timers
    ## https://docs.micropython.org/en/latest/esp8266/quickref.html#timers
    ## https://docs.micropython.org/en/latest/esp32/quickref.html#timers
    ## https://docs.micropython.org/en/latest/library/pyb.Timer.html
    tim = Timer(0)
    if not debug_mode:
        tim.init(period=1000, mode=Timer.PERIODIC, callback=clocktick)
    else:
        ## start at 05:59:00 UTC = 06:59:00 CET ...
        ts_clocktick = 60 * 60 * 5 + 59 * 60
        ## ... and run 5x faster
        tim.init(period=200, mode=Timer.PERIODIC, callback=clocktick)

    ##-------------------------------------------------------------------------
    ## run scheduled sync as thread
    uasyncio.run(scheduled_sync())

##*****************************************************************************
##*****************************************************************************

main()
