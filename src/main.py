# -*- coding: utf-8 -*-

"""
MatrixClock - an ESP32 driven HUB75 LED matrix clock.
* Synchronization with NTP.
* Temperature/humidity ambient sensor (Sensirion SHT40).

@author: mada
@version: 2023-12-06
"""

## system modules
from machine import Timer
from machine import Pin
from machine import I2C

import ntptime

import uasyncio as asyncio
import utime as time

## 3rd party modules
import hub75
import matrixdata
from logo import logo

## custom modules
import wlan_util  # => creds.py
import datetime_util
import characters

##*****************************************************************************
##*****************************************************************************

## DEBUG mode -----------------------------------------------------------------
debug_mode = False
# debug_mode = True

## NTP sync interval ----------------------------------------------------------
ntp_interval = 3600 * 12 # 3600s = 60min = 1h
ts_ntpsync = 0

## init clock -----------------------------------------------------------------
if debug_mode:
    ## start at 05:59:00 UTC = 06:59:00 CET ...
    ts_clocktick = 60 * 60 * 5 + 59 * 60
else:
    ## start at 00:00:00 UTC
    ts_clocktick = time.time()

## HUB75 LED matrix with custom pinout ----------------------------------------
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

matrix = matrixdata.MatrixData(row_size=32, col_size=64)
matrix.record_dirty_bytes = False

hub75spi = hub75.Hub75Spi(matrix, config)

## dot matrix characters ------------------------------------------------------
big_blue = {
    '0' : characters.big0,
    '1' : characters.big1,
    '2' : characters.big2,
    '3' : characters.big3,
    '4' : characters.big4,
    '5' : characters.big5,
    '6' : characters.big6,
    '7' : characters.big7,
    '8' : characters.big8,
    '9' : characters.big9,
    '.' : characters.big_dot,
    ':' : characters.big_colon,
    '°' : characters.big_degree,
    '%' : characters.big_percent,
    '-' : characters.big_dash,
    ' ' : characters.big_space,
    '~' : characters.pixel_black,
}

small_blue = {
    '0' : characters.small0,
    '1' : characters.small1,
    '2' : characters.small2,
    '3' : characters.small3,
    '4' : characters.small4,
    '5' : characters.small5,
    '6' : characters.small6,
    '7' : characters.small7,
    '8' : characters.small8,
    '9' : characters.small9,
    '.' : characters.small_dot,
    ':' : characters.small_colon,
    '°' : characters.small_degree,
    '%' : characters.small_percent,
    '-' : characters.small_dash,
    ' ' : characters.small_space,
    '~' : characters.pixel_black,
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

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def read_sensor():
    '''
    Read measurement data from Sensirion SHT40.

    Returns
    -------
    * t_degC : float
    * rh_pRH : float
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

##=============================================================================
def set_clock(timestamp=None):
    '''
    Update the display readings.
    '''
    ##-------------------------------------------------------------------------
    ## assemble time and sensor strings
    if not timestamp:
        timestamp = ts_clocktick

    localtime = datetime_util.cettime(timestamp)
    # if len(localtime) == 8:
    #     ## MicroPython
    #     year, month, mday, hour, minute, second, weekday, yearday = localtime
    # elif len(localtime) == 9:
    #     ## CPython
    #     year, month, mday, hour, minute, second, weekday, yearday, dst = localtime
    hour, minute, second = localtime[3:6]
    try:
        temp, hum = read_sensor()
    except:
        temp, hum = None, None

    ## TODO: show full timestamp when flickerfree
    # time_str = "{:02d}:{:02d}.{:02d}".format(hour, minute, second)
    time_str = "{:02d}:{:02d}".format(hour, minute)
    try:
        sensor_str = "{:4.1f}~° {:4.1f}~%".format(temp, hum)
    except:
        sensor_str = '----- -----'
    print("{} / {}".format(time_str, sensor_str))

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
    ## TODO: show full timestamp when flickerfree
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
    #matrix.clear_dirty_bytes()
    matrix.clear_all_bytes()
    ## TODO: show full timestamp when flickerfree
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

##-----------------------------------------------------------------------------
async def _set_clock(lock):
    '''
    Scheduler to update the display readings.
    '''
    while True:
        print("{:02d}.{:02d}:{:02d}".format(*time.localtime(ts_clocktick)[3:6]))
        ## DEBUG
        # print(ts_clocktick % 60)
        ## TODO: show full timestamp when flickerfree
        # if ts_clocktick % 30 == 0:  # 2023-06-30: update every 30secs
        if ts_clocktick % 10 == 0:  # 2023-12-06: update every 10secs
            await lock.acquire()
            set_clock()
            lock.release()
        await asyncio.sleep(1)

##=============================================================================
def sync_time_NTP():
    '''
    Synchronize via NTP.
    '''
    try:
        print('\n>> syncing with NTP ...')
        ## check connection status, and (re-)connect if required
        wlan_util.connect()

        ## get time
        # print('<< NTP timestamp:', ntptime.time())
        ## set time
        ntptime.settime()
        print('<< NTP timestamp:', time.time())
        return True

    except:
        print('!! NTP synchronization failed!')
        return False

##-----------------------------------------------------------------------------
async def _sync_time_NTP(lock):
    '''
    Scheduler to synchronize via NTP.
    '''
    global ts_clocktick
    global ts_ntpsync

    while True:
        if (ts_ntpsync == 0) or (ts_clocktick - ts_ntpsync > ntp_interval):
            await lock.acquire()
            for _ in range(5):
                if sync_time_NTP():
                    ts_clocktick = time.time()
                    ts_ntpsync = ts_clocktick
                    #print(datetime_util.cettime(ts_clocktick))

                    ## update clock immediately after NTP sync
                    set_clock()
                    break
            lock.release()

        await asyncio.sleep(5)

##-----------------------------------------------------------------------------
async def _refresh_display(lock):
    '''
    Scheduler to show/refresh the display.
    '''
    while True:
        await lock.acquire()
        hub75spi.display_data()
        lock.release()
        await asyncio.sleep(0)

##-----------------------------------------------------------------------------
def _clocktick(timer):
    '''
    Timed function to add one second.
    '''
    global ts_clocktick

    ts_clocktick += 1

##=============================================================================
async def main():
    ##-------------------------------------------------------------------------
    ## show Python Logo
    matrix.set_pixels(0, 16, logo)
    for _ in range(100):
        hub75spi.display_data()

    ##-------------------------------------------------------------------------
    ## init WiFi
    wlan_util.init()

    ##-------------------------------------------------------------------------
    ## init timer
    ## https://docs.micropython.org/en/latest/esp8266/quickref.html#timers
    ## https://docs.micropython.org/en/latest/esp32/quickref.html#timers
    tim = Timer(0)
    if not debug_mode:
        period = 1000
    else:
        ## run 5x faster
        period = 200
    tim.init(period=period, mode=Timer.PERIODIC, callback=_clocktick)

    ##-------------------------------------------------------------------------
    ## create the Lock instance
    lock = asyncio.Lock()

    ##-------------------------------------------------------------------------
    ## create co-routines (cooperative tasks)
    asyncio.create_task(_set_clock(lock))
    asyncio.create_task(_refresh_display(lock))
    asyncio.create_task(_sync_time_NTP(lock))

    while True:
        await asyncio.sleep(0)

try:
    asyncio.run(main())
finally:
    ## clear retained state
    _ = asyncio.new_event_loop()
