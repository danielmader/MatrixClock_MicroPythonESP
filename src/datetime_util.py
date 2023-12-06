# -*- coding: utf-8 -*-

"""
Useful clock related functions.

@author: mada
@version: 2023-03-03
"""

try:
    import utime as time
except ModuleNotFoundError:
    import time

##*****************************************************************************
##*****************************************************************************

##=============================================================================
def _daylightSavingOffset(ts_utc=time.time()):
    '''
    https://forum.micropython.org/viewtopic.php?f=2&t=4034

    Returns
    -------
    offset : int
        daylight saving offset in seconds
    '''
    year = time.localtime(ts_utc)[0]  # get current year
    HHMarch   = time.mktime((year,  3, (31 - (int(5*year/4+4)) % 7), 1,0,0,0,0,0))  # Time of March change to CEST
    HHOctober = time.mktime((year, 10, (31 - (int(5*year/4+1)) % 7), 1,0,0,0,0,0))  # Time of October change to CET

    if ts_utc< HHMarch:
        ## we are before last Sunday of March
        offset = 3600  # CET: UTC+1H
    elif ts_utc < HHOctober:
        ## we are before last Sunday of October
        offset = 7200  # CEST: UTC+2H
    else:
        ## we are after last Sunday of October
        offset = 3600  # CEST: UTC+1H

    return offset

##=============================================================================
def cettime(ts_utc=time.time()):
    '''
    https://forum.micropython.org/viewtopic.php?f=2&t=4034

    Return the Central European Time (CET) including daylight saving.

    Winter (CET) is UTC+1H Summer (CEST) is UTC+2H.

    Changes happen last Sundays of March (CEST) and October (CET) at 01:00 UTC.
    Ref. formulas : http://www.webexhibits.org/daylightsaving/i.html
                    Since 1996, valid through 2099
    Returns
    -------
    ts_cet : float
        timestamp for CET
    '''
    offset = _daylightSavingOffset(ts_utc)
    ts_cet = time.localtime(ts_utc + offset)

    return ts_cet

##=============================================================================
def localtime_toString(localtime):
    '''
    Create a timestamp string from a time.struct_time.

    Remark: time.strftime() not available on MicroPython.

    Returns
    -------
    timestr : str
    datestr : str
    '''
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
    len_lt = len(localtime)
    if len_lt == 8:
        ## MicroPython
        year, month, mday, hour, minute, second, weekday, yearday = localtime
    elif len_lt == 9:
        ## CPython
        year, month, mday, hour, minute, second, weekday, yearday, dst = localtime

    timestr = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
    try:
        datestr = "{}, {:02d} {} {}".format(days[weekday], mday, months[month], year)
    except Exception:
        datestr = ''
    return timestr, datestr

##=============================================================================
def get_timetuple(short_time_tuple):
    '''
    Compute a full time tuple from a short time tuple without datetime module.

    Parameters
    ----------
    short_time_tuple : tuple/iterable
        Short time tuple (year, month, day, hour, minute, second).

    Returns
    -------
    year : int
    month : int
    day : int
    hour : int
    minute : int
    second : int
    day_of_week : int
        Monday is 0.
    day_of_year : int
    -1 : int
        placeholder for the daylight savings time flag (N/A here).
    '''
    year, month, day, hour, minute, second = short_time_tuple
    days_since_jan1 = (31, 28 + (year % 4 == 0), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    day_of_year = sum(days_since_jan1[:month-1]) + day
    days_since_1900 = (year - 1900) * 365 + (year - 1901) // 4 + day_of_year - 1
    days_since_1970 = days_since_1900 - 25568
    day_of_week = (days_since_1970 + 4) % 7
    # seconds_since_midnight = hour * 3600 + minute * 60 + second

    return year, month, day, hour, minute, second, day_of_week, day_of_year, -1

##*****************************************************************************
##*****************************************************************************
if __name__ == '__main__':
    '''
    Standard POSIX systems epoch: 1970-01-01 00:00:00 UTC (Thursday)
    Some embedded ports epoch:    2000-01-01 00:00:00 UTC (Saturday)
    '''
    print("\n> current timestamp (seconds since the epoch)")
    ts = time.time()
    print(ts)
    print("> convert to localtime tuple")
    localtime = cettime(ts)
    print(localtime)
    print("> convert localtime tuple to a string")
    print(localtime_toString(localtime))

    print("\n> manually create a localtime tuple")
    localtime = (2023, 3, 3, 5, 6, 7, 4, 62, 0)
    print(localtime)
    print("> convert localtime tuple to seconds since the epoch")
    ts = time.mktime(localtime)
    print(ts)
    print("> convert timestamp to a string")
    try:
        print(time.strftime("%H:%M:%S %a, %d %b %Y (UTC)", time.gmtime(ts)))
        print(time.strftime("%H:%M:%S %a, %d %b %Y (local time)", time.localtime(ts)))
    except AttributeError:
        print(localtime_toString(localtime))

    print("\n> create a full time tuple from a short time tuple")
    localtime_short = (2023, 3, 3, 5, 6, 7)  # year, month, day, hour, minute, second
    localtime_short = (2000, 1, 1, 0, 0, 0)  # year, month, day, hour, minute, second
    localtime_short = (1970, 1, 1, 0, 0, 0)  # year, month, day, hour, minute, second
    print(localtime_short)
    localtime_full = get_timetuple(localtime_short)
    print(localtime_full)
    print("> convert full time tuple to seconds since the epoch")
    seconds_since_epoch = time.mktime(localtime_full)
    print(seconds_since_epoch)
    print("> convert seconds to a full time tuple with weekday and yearday")
    ## TODO: this fails on ESP32 with OverflowError: overflow converting long int to machine word
    full_time_tuple = time.localtime(seconds_since_epoch)
    print(full_time_tuple)
