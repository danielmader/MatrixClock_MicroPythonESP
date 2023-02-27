#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: mada
@version: 2023-02-27
"""

## system modules
try:
    ## https://forum.core-electronics.com.au/t/utime-vs-time-and-ubinascii-vs-binascii/5437
    import utime as time
except ModuleNotFoundError:
    import time

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def daylightSavingOffset(timestamp=time.time()):
    '''
    https://forum.micropython.org/viewtopic.php?f=2&t=4034

    Return daylight saving offset.
    '''
    year = time.localtime(timestamp)[0]  # get current year
    HHMarch   = time.mktime((year,  3, (31 - (int(5*year/4+4)) % 7), 1,0,0,0,0,0))  # Time of March change to CEST
    HHOctober = time.mktime((year, 10, (31 - (int(5*year/4+1)) % 7), 1,0,0,0,0,0))  # Time of October change to CET

    if timestamp < HHMarch:
        ## we are before last Sunday of March
        offset = 3600  # CET: UTC+1H
    elif timestamp < HHOctober:
        ## we are before last Sunday of October
        offset = 7200  # CEST: UTC+2H
    else:
        ## we are after last Sunday of October
        offset = 3600  # CEST: UTC+1H

    return offset

##=============================================================================
def cettime(timestamp=time.time()):
    '''
    https://forum.micropython.org/viewtopic.php?f=2&t=4034

    Return the Central European Time (CET) including daylight saving.

    Winter (CET) is UTC+1H Summer (CEST) is UTC+2H.

    Changes happen last Sundays of March (CEST) and October (CET) at 01:00 UTC.
    Ref. formulas : http://www.webexhibits.org/daylightsaving/i.html
                    Since 1996, valid through 2099
    '''
    offset = daylightSavingOffset(timestamp)
    cet = time.localtime(timestamp + offset)

    return cet


##=============================================================================
days = {
    0 : "Mon",
    1 : "Tue",
    2 : "Wed",
    3 : "Thu",
    4 : "Fri",
    5 : "Sat",
    6 : "Sun"
}
months = {
    1 : "Jan",
    2 : "Feb",
    3 : "Mar",
    4 : "Apr",
    5 : "May",
    6 : "Jun",
    7 : "Jul",
    8 : "Aug",
    9 : "Sep",
    10 : "Oct",
    11 : "Nov",
    12 : "Dec"
}

##=============================================================================
def localtime_toString(localtime):
    '''
    Create a timestamp string from a time.struct_time.
    '''
    len_lt = len(localtime)
    if len_lt == 8:
        ## MicroPython
        year, month, mday, hour, minute, second, weekday, yearday = localtime
    elif len_lt == 9:
        ## CPython
        year, month, mday, hour, minute, second, weekday, yearday, dst = localtime

    timestr = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    try:
        datestr = "{}, {} {} {}".format(days[weekday], mday, months[month], year)
    except Exception:
        datestr = ''
    return timestr, datestr


##*****************************************************************************
##*****************************************************************************
if __name__ == '__main__':
    localtime = cettime()
    print(localtime)
    print(localtime_toString(localtime))
