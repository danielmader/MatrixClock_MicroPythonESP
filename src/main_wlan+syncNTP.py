# -*- coding: utf-8 -*-

"""
Main script for bare clock function w/ NTP over Wifi.

@author: mada
@version: 2023-03-02
"""

## system modules
from machine import Timer

import ntptime

import uasyncio as asyncio
import utime as time

## custom modules
import wlan_helper  # => creds.py
import datetime_helper

##*****************************************************************************
##*****************************************************************************

## DEBUG mode -----------------------------------------------------------------
debug_mode = False
# debug_mode = True

## NTP sync interval ----------------------------------------------------------
ntp_interval = 15  # 3600s = 60min = 1h
ts_ntpsync = 0
if debug_mode:
    ## start at 05:59:00 UTC = 06:59:00 CET ...
    ts_clocktick = 60 * 60 * 5 + 59 * 60
else:
    ## start at 00:00:00 UTC
    ts_clocktick = time.time()

##*****************************************************************************
##*****************************************************************************


##=============================================================================
def sync_time_NTP():
    '''
    Synchronize via NTP.
    '''
    try:
        print('\n>> syncing with NTP ...')
        ## check connection status, and (re-)connect if required
        wlan_helper.connect()

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
async def _scheduled_sync(lock):
    '''
    Synchronize via NTP.
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
                    print(datetime_helper.cettime(ts_clocktick))
                    break
            lock.release()

        await asyncio.sleep(5)


##-----------------------------------------------------------------------------
async def _refresh_display(lock):
    '''
    Refresh clock display.
    '''
    while True:
        await lock.acquire()
        print("\t\t\trefresh...")
        lock.release()
        await asyncio.sleep_ms(100)


##-----------------------------------------------------------------------------
async def _set_clock(lock):
    '''
    Update time display.
    '''
    while True:
        ##---------------------------------------------------------------------
        ## assemble time and sensor strings
        localtime = datetime_helper.cettime(ts_clocktick)
        # if len(localtime) == 8:
        #     ## MicroPython
        #     year, month, mday, hour, minute, second, weekday, yearday = localtime
        # elif len(localtime) == 9:
        #     ## CPython
        #     year, month, mday, hour, minute, second, weekday, yearday, dst = localtime
        hour, minute, second = localtime[3:6]

        ## TODO: show full timestamp when flickerfree
        # time_str = "{:02d}:{:02d}.{:02d}".format(hour, minute, second)
        time_str = "{:02d}:{:02d}".format(hour, minute)

        ## DEBUG
        print("{} > {}".format(time_str, localtime[3:6]))

        await lock.acquire()
        ## write out new pixel states
        print("\t\t\tset clock...")
        lock.release()

        await asyncio.sleep(1)


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
    ## init WiFi
    wlan_helper.init()

    ##-------------------------------------------------------------------------
    ## init timer
    ## https://docs.micropython.org/en/latest/esp8266/quickref.html#timers
    ## https://docs.micropython.org/en/latest/esp32/quickref.html#timers
    tim = Timer(0)
    if not debug_mode:
        tim.init(period=1000, mode=Timer.PERIODIC, callback=_clocktick)
    else:
        ## run 5x faster
        tim.init(period=200, mode=Timer.PERIODIC, callback=_clocktick)

    ##-------------------------------------------------------------------------
    ## create the Lock instance
    lock = asyncio.Lock()

    ##-------------------------------------------------------------------------
    ## create co-routines (cooperative tasks)
    asyncio.create_task(_set_clock(lock))
    asyncio.create_task(_refresh_display(lock))
    asyncio.create_task(_scheduled_sync(lock))

    while True:
        await asyncio.sleep(0.001)

try:
    asyncio.run(main())
finally:
    ## clear retained state
    _ = asyncio.new_event_loop()
