# -*- coding: utf-8 -*-

"""
Main script to demo I2C readout of Sensirion SHT40 w/ NodeMCU ESP8266.

@author: mada
@version: 2023-02-20
"""

## system modules
import time
from machine import I2C
# from machine import SoftI2C
from machine import Pin
import uos
import sys

##*****************************************************************************
##*****************************************************************************

'''
_SHT4X_DEFAULT_ADDR = const(0x44)  # SHT4X I2C Address
_SHT4X_READSERIAL = const(0x89)    # Read Out of Serial Register
_SHT4X_SOFTRESET = const(0x94)     # Soft Reset
'''
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

##-----------------------------------------------------------------------------
## create I2C object
if uos.uname().sysname == 'esp8266':
    i2c = I2C(0, scl=Pin(5), sda=Pin(4))
else:
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
    #i2c = SoftI2C(scl=Pin(23), sda=Pin(22))

i2c_devs = i2c.scan()
for dev in i2c_devs:
    print("\n>> found I2C address:", dev, hex(dev))
    if dev == 0x44:
        break
    else:
        sys.exit()

##-----------------------------------------------------------------------------
print("\n>> getting the unique 32-bit serial number ...")
mode = modes[0]
i2c.writeto(dev, bytearray([mode[1]]))
time.sleep(mode[-1])
rx_bytes = i2c.readfrom(dev, 6)
print('>', rx_bytes, len(rx_bytes))
seno1 = rx_bytes[0:2]
seno1_crc = rx_bytes[2]
seno2 = rx_bytes[3:5]
seno2_crc = rx_bytes[5]
seno = (seno1[0] << 24) + (seno1[1] << 16) + (seno2[0] << 8) + seno2[1]
print('>', seno)
## TODO: unpacking using ustruct.unpack()
#fmt = '>h' #big-endian
#fmt = '<h' #little-endian
#print(ustruct.unpack(fmt, rx_bytes))

##-----------------------------------------------------------------------------
print("\n>> reading measurement values ...")
mode =  modes[1]  # NOHEAT_HIGHPRECISION
i2c.writeto(dev, bytearray([mode[1]]))
time.sleep(mode[-1])
rx_bytes = i2c.readfrom(dev, 6)
print('>', rx_bytes, len(rx_bytes))
t_ticks = rx_bytes[0] * 256 + rx_bytes[1]
rh_ticks = rx_bytes[3] * 256 + rx_bytes[4]
t_degC = -45 + 175 * t_ticks / 65535  # 2^16 - 1 = 65535
rh_pRH = -6 + 125 * rh_ticks / 65535
if (rh_pRH > 100):
    rh_pRH = 100
if (rh_pRH < 0):
    rh_pRH = 0
print('> temperature:', t_degC)
print('> humidity:', rh_pRH)
