#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 14 20:31:18 2020

@author: mada
@version: 2023-03-03

NeoClock - an ESP8266 driven LED clock for a 60px outer NeoPixel ring.
Colors and brightness for daytime and at night.
Synchronization with NTP (WiFi configuration see creds.py) and OLED status display.

* Clock face indicators (inner and outer ring)
* Hours (inner ring)
* Minutes (outer ring)
* Seconds (outer ring)
"""

## system modules
from machine import Timer, Pin, I2C

import neopixel

import ntptime
import uasyncio
# import _thread
import utime as time
#import time

## custom modules
import wlan_util  # => creds.py
import datetime_util
from oleds import SSD1306_I2C_enh

##*****************************************************************************
##*****************************************************************************

## Neopixels ------------------------------------------------------------------
#np_o = neopixel.NeoPixel(Pin(5), 60)  # D1 !!! NOK !!!
#np_i = neopixel.NeoPixel(Pin(4), 24)  # D2 !!! NOK !!!
#np_i = neopixel.NeoPixel(Pin(2), 24)  # D4 !! startup blink !!
np_o = neopixel.NeoPixel(Pin(0), 60)   # D3
np_i = neopixel.NeoPixel(Pin(14), 24)  # D5

## check start pixel positions for rotational offset
# np_o[0] = 0,1,0
# np_i[0] = 0,1,0
# np_o.write()
# np_i.write()
# time.sleep(10)

## rotational offset outer/inner ring
np_o.offset = 10
np_i.offset = 9
idx_i = {i : (i + np_i.offset) % np_i.n for i in range(np_i.n)}
idx_o = {i : (i + np_o.offset) % np_o.n for i in range(np_o.n)}
set_i = {}
set_o = {}

## clock color definitions ----------------------------------------------------
## face colors
face_colors = {
    'hours' :           (0,0,1),  # blue
    'quarters' :        (0,0,5),  # blue
    'quarters_dark' :   (0,0,1),  # blue
}
## hand colors
hand_colors = {
    'hour' :        (5,0,0),  # red
    'hour_dark' :   (1,0,0),  # red
    'minute' :      (0,5,0),  # green
    'minute_dark' : (0,1,0),  # green
    'second' :      (0,1,1),  # cyan
}
hand_colors['minhour'] = tuple(sum(x) for x in zip(hand_colors['hour'], hand_colors['minute']))
hand_colors['minhour_dark'] = tuple(sum(x) for x in zip(hand_colors['hour_dark'], hand_colors['minute_dark']))

## clock face indicators ------------------------------------------------------
hrs_i = [int(np_i.n/12 * _) for _ in range(12)]
hrs_o = [int(np_o.n/12 * _) for _ in range(12)]
quarters_i = 0, np_i.n/4, np_i.n/2, np_i.n/4*3
quarters_i = [int(_) for _ in quarters_i]
quarters_o = 0, np_o.n/4, np_o.n/2, np_o.n/4*3
quarters_o = [int(_) for _ in quarters_o]

## NTP sync interval ----------------------------------------------------------
ntp_interval = 3600 * 12 # 3600s = 60min = 1h
ts_ntpsync = 0
ts_clocktick = time.time()

## DEBUG mode -----------------------------------------------------------------
debug_mode = False
# debug_mode = True

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def clear_face(write=True):
    '''
    Reset all index colors.
    '''
    global set_i
    global set_o

    ## set initial pixels
    set_i = {i : (0,0,0) for i in range(np_i.n)}
    set_o = {i : (0,0,0) for i in range(np_o.n)}

    if write:
        for idx, color in set_i.items():
            np_i[idx_i[idx]] = color
        for idx, color in set_o.items():
            np_o[idx_o[idx]] = color
        np_i.write()
        np_o.write()

##=============================================================================
def set_clock(ts_clocktick, write=True):
    '''
    Set hour, minute, and second on NeoPixel clock face.
    '''
    global set_i
    global set_o

    n_i = np_i.n
    n_o = np_o.n

    ##-------------------------------------------------------------------------
    ## assemble time and sensor strings
    localtime = datetime_util.cettime(ts_clocktick)
    # if len(localtime) == 8:
    #     ## MicroPython
    #     year, month, mday, hour, minute, second, weekday, yearday = localtime
    # elif len(localtime) == 9:
    #     ## CPython
    #     year, month, mday, hour, minute, second, weekday, yearday, dst = localtime
    hour, minute, second = localtime[3:6]

    ## DEBUG
    # print("{:02d}.{:02d}:{:02d} > {}".format(hour, minute, second, localtime[3:6]))
    # if second % 5 == 0:
    #     print('%02i.%02i:%02i' % (hour, minute, second))

    ##-------------------------------------------------------------------------
    ## use darkmode during night time
    if hour in [20,21,22,23,0,1,2,3,4,5,6]:
        darkmode = True
    else:
        darkmode = False

    ##-------------------------------------------------------------------------
    ## determine clock indices
    ## seconds
    idx_second = int(second * (n_o / 60))

    ## minutes
    idx_minute = int(minute * (n_o / 60))

    ## inner & outer hours in 1/12th steps
    hour_ = hour % 12   # 24 hrs > 12 am/pm
    idx_hour_i = int(hour_ * (n_i / 12))
    idx_hour_o = int(hour_ * (n_o / 12))

    ## 1) intermediate inner hours
    delta_hour_i = n_i / 12  # := 2
    delta_hour_i *= (minute / 60)
    idx_hour_i = range(idx_hour_i, idx_hour_i + int(delta_hour_i) + 1)

    ## 2a) align outer hours with inner hours
    # if int(delta_hour_i) > 0:
    #     idx_hour_o.append(idx_hour_o[-1] + 2)
    ## 2b) intermediate outer hours
    # delta_hour_o = n_o / 12  # := 5
    # delta_hour_o *= (minute / 60)
    # idx_hour_o = range(idx_hour_o, idx_hour_o + int(delta_hour_o) + 1)
    ## 2c) intermediate outer hours in 15 mins steps (2022-11-09)
    delta_hour_o = minute // 15
    idx_hour_o = range(idx_hour_o, idx_hour_o + delta_hour_o + 1)

    ##-------------------------------------------------------------------------
    ## set index colors
    clear_face(write=False)

    if darkmode:
        ## clockface
        #set_i.update({i : face_colors['quarters_dark'] for i in quarters_i})
        set_o.update({i : face_colors['quarters_dark'] for i in quarters_o})
        ## hour
        # set_i[idx_hour_i] = hand_colors['hour_dark']
        # set_o[idx_hour_o] = hand_colors['hour_dark']
        for _i in idx_hour_i:
            set_i[_i] = hand_colors['hour_dark']
        for _o in idx_hour_o:
            set_o[_o] = hand_colors['hour_dark']
        ## minute
        if idx_minute in idx_hour_o:
            set_o[idx_minute] = hand_colors['minhour_dark']
        else:
            set_o[idx_minute] = hand_colors['minute_dark']
    else:
        ## clockface
        #set_i.update({i : face_colors['hours'] for i in hrs_i})
        set_o.update({i : face_colors['hours'] for i in hrs_o})
        set_i.update({i : face_colors['quarters'] for i in quarters_i})
        set_o.update({i : face_colors['quarters'] for i in quarters_o})
        ## hour
        # set_i[idx_hour_i] = hand_colors['hour']
        # set_o[idx_hour_o] = hand_colors['hour']
        for _i in idx_hour_i:
            set_i[_i] = hand_colors['hour']
        for _o in idx_hour_o:
            set_o[_o] = hand_colors['hour']
        ## minute
        if idx_minute in idx_hour_o:
            set_o[idx_minute] = hand_colors['minhour']
        else:
            set_o[idx_minute] = hand_colors['minute']
        set_o[idx_minute] = hand_colors['minute']
        ## second
        set_o[idx_second] = hand_colors['second']

    ##-------------------------------------------------------------------------
    ## write out new pixel states
    if write:
        for idx, color in set_i.items():
            np_i[idx_i[idx]] = color
        for idx, color in set_o.items():
            np_o[idx_o[idx]] = color
        np_i.write()
        np_o.write()

##=============================================================================
def demo_clockaccuracy():
    '''
    https://github.com/micropython/micropython/issues/2724
    '''
    pass
    # ## Initialize RTC time with NTP
    # ts_ntp = ntptime.time()
    # ts_tm = time.localtime(ts_ntp)
    # ts_day = ts_ntp - ts_tm[3]*3600 - ts_tm[4]*60 - ts_tm[5]
    # ts_ntp -= ts_day

    # rtc = RTC()
    # now = rtc.datetime()
    # ts_rtc = now[4]*3600*1000 + now[5]*60*1000 + now[6]*1000 + now[7]

    # ts_diff = ts_ntp*1000 - ts_rtc
    # print("Initial time offset = %d" % (ts_diff))
    # cnt = 0
    # while True:
    #     # Wait 10 sec
    #     time.sleep_ms(10000)
    #     cnt += 1
    #     try:
    #         ts_ntp = ntptime.time() - ts_day
    #         now = rtc.datetime()
    #         ts_rtc = now[4]*3600*1000 + now[5]*60*1000 + now[6]*1000 + now[7]
    #         print("%.3d: Time drift = %d" % (cnt, ts_ntp*1000 - ts_rtc - ts_diff))
    #     except Exception as e:
    #         print("Failed to query NTP time: %s" % e)

##-----------------------------------------------------------------------------
def clocktick(timer):
    '''
    Timed function to add one second.
    '''
    global ts_clocktick

    ## 1) increase clock counter
    ts_clocktick += 1

    ## 2) update status on OLED (if available)
    update_oled()

    ## 3) update time display
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
                wlan_util.connect()
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

##=============================================================================
def update_oled():
    '''
    Update OLED screen and print to stdout.
    '''
    global oled
    if not oled:
        return

    def ts_toString(timestamp):
        #localtime = time.localtime(timestamp)
        localtime = datetime_util.cettime(timestamp)
        year, month, mday, hour, minute, second, weekday, yearday = localtime
        timestr = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
        return timestr

    ## system RTC (not precise)
    # ts_now1 = time.time()
    # timestr1 = ts_toString(ts_now1)

    ## timed counter (derived from the main crystal)
    ts_now2 = ts_clocktick
    timestr2 = ts_toString(ts_now2)

    ## ticks_ms() counter (derived from the main crystal)  # TODO: update ticks_ms() after NTP sync
    # ts_now3 = int(round((time.ticks_ms() - ts_offset_ticksms) / 1000))  # + ts_ntpsync
    # timestr3 = ts_toString(ts_now3)

    ## last successful NTP sync
    timestr4 = ts_toString(ts_ntpsync)

    ## connection status
    connectstr = '%s' % wlan_util.isconnected()

    oled.fill(0)
    # oled.text("time()  " + timestr1, 0, 10)
    oled.text("ctick() " + timestr2, 0, 20)
    # oled.text("ticks() " + timestr3, 0, 30)
    oled.text("synced: " + timestr4, 0, 40)
    oled.text("connected: " + connectstr , 0, 50)
    oled.show()

    ## print timestamps as 'hh:mm:ss'
    # print()
    # print('utime.time()    ', timestr1)
    print('clocktick()     ', timestr2)
    # print('utime.ticks_ms()', timestr3)
    # print('last NTP sync   ', timestr4)
    ## DEBUG
    #print(ts_clocktick, ts_ntpsync, ntp_interval, ts_clocktick-ts_ntpsync)

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def main():
    global ts_ntpsync
    global ts_clocktick
    global oled

    ##-------------------------------------------------------------------------
    ## init clock
    set_clock(ts_clocktick)

    ##-------------------------------------------------------------------------
    ## init WiFi
    wlan_util.init()

    ##-------------------------------------------------------------------------
    ## init OLED
    # scl = 4  # ESP8266 D2 - *GPIO 4* - SCL
    # sda = 5  # ESP8266 D1 - *GPIO 5* - SDA
    # # i2c_freq = 1e6
    # i2c = I2C(scl=Pin(scl), sda=Pin(sda))
    # print(">> I2C devices:", i2c.scan(), "(default I²C address of SSD1306 is 0x3c=60)")
    # oled = SSD1306_I2C_enh(i2c)
    # oled.init_display()

    ## don't use OLED all the time as it seems to rapidly degrade
    oled = None

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
