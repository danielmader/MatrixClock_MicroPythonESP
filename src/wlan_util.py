# -*- coding: utf-8 -*-

"""
Initialization of the ESP Wifi interface.

https://forum.micropython.org/viewtopic.php?t=2440
https://forum.micropython.org/viewtopic.php?t=2951

@author: mada
@version: 2023-02-28
"""

## system modules
import network

## own modules
from creds import creds_dict  # credentials of trusted APs

##*****************************************************************************
##*****************************************************************************

ap = None
wlan = None

##=============================================================================
def init():
    '''
    Setup and configuration of wifi interface.
    '''
    global ap
    global wlan

    ## configure access-point interface
    # print('>> setting up AP interface ...')
    # ap = network.WLAN(network.AP_IF)
    # ap.active(True)
    # ap.config(essid='myESP-AP')
    # ap.config(authmode=network.AUTH_WPA_WPA2_PSK, password="µPyESP-AP")

    ## disable access-point interface
    print('>> disabling AP interface ...')
    ap = network.WLAN(network.AP_IF)
    ap.active(False)

    ## configure station interface
    print('>> setting up station interface ...')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        wlan.config(reconnects=5)  # ESP32 only
    except:
        pass

    ## auto-connect to last network (ESP8266 standard behavior)
    pass

    ## connect to other network
    if not wlan.isconnected():
        connect()
    else:
        print("<< network established:", wlan.ifconfig())

##=============================================================================
def isconnected():
    '''
    Wrapper function to check connection status of station interface.
    '''
    return wlan.isconnected()

##=============================================================================
def connect():
    '''
    Connect WiFi station interface to known and trusted networks.

    https://docs.micropython.org/en/latest/esp8266/quickref.html#networking
    https://docs.micropython.org/en/latest/esp32/quickref.html#networking
    '''
    if wlan.isconnected():
        print('## already connected!')
    else:
        print('## not connected, searching for networks ...')
        ## find all networks
        ap_list = wlan.scan()
        print("== available networks:")
        for ap in ap_list:
            print('\t', ap)

        ## sort networks by signal strength
        ap_list.sort(key=lambda ap: ap[3], reverse=True)

        ## filter only trusted networks
        ap_list = list(filter(lambda ap: ap[0].decode('UTF-8') in creds_dict.keys(), ap_list))
        if ap_list != []:
            print("== trusted networks:")
            for ii, ap in enumerate(ap_list):
                print('\t# %i/%i - %r' % (ii+1, len(ap_list), ap))

            ## try to connect to networks
            for ap in ap_list:
                print('== connecting to network:')
                print('\t', ap)
                essid = ap[0].decode('UTF-8')
                wlan.active(True)
                wlan.connect(essid, creds_dict[essid])
                while wlan.status() == network.STAT_CONNECTING:
                    pass
                if wlan.isconnected():
                    print('## connected!')
                    print('## network config:', wlan.ifconfig())
                    return
            print('!! connection failed!')

##=============================================================================
if __name__ == '__main__':
    ## init WiFi and connect
    init()
