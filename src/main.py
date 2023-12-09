# -*- coding: utf-8 -*-

"""
MatrixClock - an ESP32 driven HUB75 LED matrix clock.
* Synchronization with NTP.
* Temperature/humidity ambient sensor (Sensirion SHT40).

@author: mada
@version: 2023-12-09
"""

## System modules
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

## Custom modules
import wlan_util  # => creds.py
import datetime_util
import characters

##*****************************************************************************
##*****************************************************************************

## DEBUG mode -----------------------------------------------------------------
debug_mode = False
# debug_mode = True

## NTP sync interval ----------------------------------------------------------
ntp_interval = 3600 * 12  # 3600s = 60min = 1h
ts_ntpsync = 0

## Init clock -----------------------------------------------------------------
if debug_mode:
    ## Start at 05:59:00 UTC = 06:59:00 CET ...
    ts_clocktick = 60 * 60 * 5 + 59 * 60
else:
    ## Start at 00:00:00 UTC
    ts_clocktick = time.time()

## HUB75 LED matrix with custom pinout ----------------------------------------
config = hub75.Hub75SpiConfiguration()
## Row select pins
config.line_select_a_pin_number = 15
config.line_select_b_pin_number = 2
config.line_select_c_pin_number = 4
config.line_select_d_pin_number = 16
config.line_select_e_pin_number = 12
## Color data pins
config.red1_pin_number = 32
config.green1_pin_number = 33
config.blue1_pin_number = 25
config.red2_pin_number = 26
config.green2_pin_number = 27
config.blue2_pin_number = 14
## Logic pins
config.clock_pin_number = 18
config.latch_pin_number = 5
config.output_enable_pin_number = 17  # active low
config.spi_miso_pin_number = 13  # not connected
## Misc
# config.illumination_time_microseconds = 1

matrix = matrixdata.MatrixData(row_size=32, col_size=64)
matrix.record_dirty_bytes = True

hub75spi = hub75.Hub75Spi(matrix, config)

## Dot matrix characters ------------------------------------------------------
## Characters are 2D arrays with 0..7 for 3-bit colors RGB
## Blue is #001b, i.e. 1
big_blue = {
    '0' : characters.big0,         # 8 x14
    '1' : characters.big1,         # 8 x14
    '2' : characters.big2,         # 8 x14
    '3' : characters.big3,         # 8 x14
    '4' : characters.big4,         # 8 x14
    '5' : characters.big5,         # 8 x14
    '6' : characters.big6,         # 8 x14
    '7' : characters.big7,         # 8 x14
    '8' : characters.big8,         # 8 x14
    '9' : characters.big9,         # 8 x14
    '.' : characters.big_dot,      # 2 x14
    ':' : characters.big_colon,    # 2 x14
    '°' : characters.big_degree,   # 4 x14
    'C' : characters.big_degreeC,  # 8 x14
    '%' : characters.big_percent,  # 8 x14
    '-' : characters.big_dash,     # 8 x14
    ' ' : characters.big_space,    # 8 x14
    '~' : characters.pixel_black,  # 1 x1
    }

small_blue = {
    '0' : characters.small0,         # 5 x7
    '1' : characters.small1,         # 5 x7
    '2' : characters.small2,         # 5 x7
    '3' : characters.small3,         # 5 x7
    '4' : characters.small4,         # 5 x7
    '5' : characters.small5,         # 5 x7
    '6' : characters.small6,         # 5 x7
    '7' : characters.small7,         # 5 x7
    '8' : characters.small8,         # 5 x7
    '9' : characters.small9,         # 5 x7
    '.' : characters.small_dot,      # 1 x7
    ':' : characters.small_colon,    # 1 x7
    '°' : characters.small_degree,   # 3 x7
    'C' : characters.small_degreeC,  # 6 x7
    '%' : characters.small_percent,  # 5 x7
    '-' : characters.small_dash,     # 4 x7
    ' ' : characters.small_space,    # 5 x7
    '~' : characters.pixel_black,    # 1 x1
    }

## Yellow is #110b, i.e. 6
big_yellow = {}
for char in big_blue:
    big_yellow[char] = []
    for i, row in enumerate(big_blue[char]):
        row = [col * 6 for col in row]  # yellow
        big_yellow[char].append(row)
small_yellow = {}
for char in small_blue:
    small_yellow[char] = []
    for i, row in enumerate(small_blue[char]):
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
    t_degC = -45 + 175 * t_ticks / 65535  # 2^16 - 1 = 65535
    rh_pRH = -6 + 125 * rh_ticks / 65535
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
    ## Assemble raw time and sensor strings
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
    except Exception:
        temp, hum = None, None

    ## DEBUG
    # if second // 10 == 0:
    #     temp, hum = 9.9, 55.5
    # elif second // 10 == 1:
    #     temp, hum = -9.9, 55.5
    # elif second // 10 == 2:
    #     temp, hum = -11.1, 55.5
    # elif second // 10 == 3:
    #     temp, hum = 3.3, 4.4
    # elif second // 10 == 4:
    #     temp, hum = 22.2, 55.5
    # elif second // 10 == 5:
    #     temp, hum = None, None

    time_str = "{:02d}:{:02d}.{:02d}".format(hour, minute, second)
    try:
        sensor_str = "{:4.1f}C {:4.1f}%".format(temp, hum)
    except ValueError:
        sensor_str = '----  ----'
    print("{} / {}".format(time_str, sensor_str))

    ##-------------------------------------------------------------------------
    ## Use darkmode during night time
    ## TODO: handle darkmode
    # if hour in [20,21,22,23,0,1,2,3,4,5,6]:
    #     darkmode = True
    # else:
    #     darkmode = False
    big = big_yellow
    small = small_yellow

    ##-------------------------------------------------------------------------
    ## Assemble character images lists per line
    time_display = []
    sensor_display = []
    ## Time HH:MM in big chars
    for char in time_str[:-3]:
        time_display.append(big[char])
    ## Time .SS in small chars
    for char in time_str[-3:]:
        time_display.append(small[char])
    ## Sensor data in small chars
    for char in sensor_str:
        sensor_display.append(small[char])

    ##-------------------------------------------------------------------------
    ## Concatenate character arrays and center on screen
    matrix.clear_dirty_bytes()
    # matrix.clear_all_bytes()

    ## Default character spacings
    space_big = 2    # default spacing for 'big'
    space_small = 1  # default spacing for 'small'

    ## 1) pixels(HH:MM)    = 2*8(+4) + 2(+2) + 2*8(+2) = 42
    ## 2) pixels(HH:MM.SS) = 42(+2) + 1+2*5(+2)        = 57
    # => 1st column index is ((64 - pixels) / 2) =
    ## 1) : 11
    ## 2) :  3.5
    ## TODO: Show full timestamp when flickerfree, see async def _set_clock()
    col = 4   # HH:MM.ss
    col = 11  # HH:MM
    for img in time_display[:-3]:
        matrix.set_pixels(5, col, img)
        col += len(img[0]) + space_big
    # for img in time_display[-3:]:
    #     matrix.set_pixels(5, col, img)
    #     col += len(img[0]) + space_small

    ## 1) pixels('xx.xC xx.x%') = 5+5+1+5+6(+5) + [5](+1) + 5+5+1+5+5(+4) = 58
    ## 2) pixels('-x.xC xx.x%') = 4+5+1+5+6(+5) + [5](+1) + 5+5+1+5+5(+4) = 57
    ## 3) pixels('-xx.xC xx.x%') = 4(+1) + 58                             = 63
    ## 4) pixels('----  ----') = 8*4 + 2*5 (+9)                           = 51
    ## => 1st column index is ((64 - pixels) / 2) =
    ## 1) :  3
    ## 2) :  3.5
    ## 3) :  0.5
    ## 4) :  6.5
    if len(sensor_str) == 11 and temp >= 0:
        col = 3
    if len(sensor_str) == 11 and temp < 0:
        col = 4
    elif len(sensor_str) == 12:
        col = 1
    elif len(sensor_str) == 10:
        col = 7
    for img in sensor_display:
        matrix.set_pixels(22, col, img)
        col += len(img[0]) + space_small


##-----------------------------------------------------------------------------
async def _set_clock(lock):
    '''
    Scheduler to update the display readings.
    '''
    while True:
        print("{:02d}.{:02d}:{:02d}".format(*time.localtime(ts_clocktick)[3:6]))

        ## TODO: update every second when when flickerfree
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

    except Exception:
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
