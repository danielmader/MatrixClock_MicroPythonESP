# -*- coding: utf-8 -*-

"""
Minimum example for basic control of a HUB75 LED matrix (WaveShare 64x32) w/ NodeMCU ESP32.

@author: mada
@version: 2023-02-13
"""

## system modules
import time
#from machine import I2C
from machine import Pin

##*****************************************************************************
##*****************************************************************************

print(">>>> Setting pin definitions for HUB75 connector ...")
# R1 = Pin(25, Pin.OUT)
# G1 = Pin(26, Pin.OUT)
# B1 = Pin(27, Pin.OUT)
# R2 = Pin(14, Pin.OUT)
# G2 = Pin(12, Pin.OUT)
# B2 = Pin(13, Pin.OUT)
# E = Pin(32, Pin.OUT)
# A = Pin(19, Pin.OUT)
# B = Pin(18, Pin.OUT)
# C = Pin(5,  Pin.OUT)
# D = Pin(17, Pin.OUT)
# CLK = Pin(16, Pin.OUT)
# LAT = Pin(4,  Pin.OUT)
# OE = Pin(15, Pin.OUT)
# R1 = Pin(2, Pin.OUT)
# G1 = Pin(4, Pin.OUT)
# B1 = Pin(15, Pin.OUT)
# R2 = Pin(16, Pin.OUT)
# G2 = Pin(17, Pin.OUT)
# B2 = Pin(27, Pin.OUT)
# E = Pin(12, Pin.OUT)
# A = Pin(5, Pin.OUT)
# B = Pin(18, Pin.OUT)
# C = Pin(19,  Pin.OUT)
# D = Pin(21, Pin.OUT)
# CLK = Pin(22, Pin.OUT)
# LAT = Pin(26,  Pin.OUT)
# OE = Pin(25, Pin.OUT)
R1 = Pin(32, Pin.OUT)
G1 = Pin(33, Pin.OUT)
B1 = Pin(25, Pin.OUT)
R2 = Pin(26, Pin.OUT)
G2 = Pin(27, Pin.OUT)
B2 = Pin(14, Pin.OUT)
E = Pin(12, Pin.OUT)
A = Pin(15, Pin.OUT)
B = Pin(2, Pin.OUT)
C = Pin(4,  Pin.OUT)
D = Pin(16, Pin.OUT)
CLK = Pin(18, Pin.OUT)
LAT = Pin(5,  Pin.OUT)
OE = Pin(17, Pin.OUT)

##=============================================================================
def reset():
    '''
    Initialize all pins as low; disable output.

    Returns
    -------
    None.

    '''
    print(">>>> Reset color and row select pins ...")
    R1.value(0)
    R2.value(0)
    G1.value(0)
    G2.value(0)
    B1.value(0)
    B2.value(0)
    A.value(0)
    B.value(0)
    C.value(0)
    D.value(0)
    E.value(0)
    OE.value(0)  # enable output
    #OE.value(1)  # disable output
    CLK.value(0)
    LAT.value(0)

##=============================================================================
def set_color(rgb1, rgb2):
    '''
    Define the function to update the LED matrix.

    Parameters
    ----------
    rgb1 : TYPE
        DESCRIPTION.
    rgb2 : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    '''
    R1.value(rgb1[0])
    G1.value(rgb1[1])
    B1.value(rgb1[2])
    R2.value(rgb2[0])
    G2.value(rgb2[1])
    B2.value(rgb2[2])

##-----------------------------------------------------------------------------
## 1)
'''
https://www.bigmessowires.com/2018/05/24/64-x-32-led-matrix-programming/

1. Begin with OE, CLK, and LAT low.
2. Initialize a private row counter N to 0.
3. Set R1,G1,B1 to the desired color for row N, column 0.
4. Set R2,G2,B2 to the desired color for row HEIGHT/2+N, column 0.
5. Set CLK high, then low, to shift in the color bit.
6. Repeat steps 3-5 WIDTH times for the remaining columns.
7. Set OE high to disable the LEDs.
8. Set LAT high, then low, to load the shift register contents into the LED outputs.
9. Set ABC (or ABCD) to the current row number N.
10. Set OE low to re-enable the LEDs.
11. Increment the row counter N.
12. Repeat steps 3-11 HEIGHT/2 times for the remaining rows.
'''
reset()
for i in range(10):
#while True:
    for row in range(16):
        for col in range(64):
            if i % 3 == 0:
                if col < 21:
                    set_color((1,0,0), (0,0,1))
                elif col < 41:
                    set_color((0,1,0), (1,0,0))
                else:
                    set_color((0,0,1), (0,1,0))
            elif i % 3 == 1:
                if col < 21:
                    set_color((0,0,1), (0,1,0))
                elif col < 41:
                    set_color((1,0,0), (0,0,1))
                else:
                    set_color((0,1,0), (1,0,0))
            elif i % 3 == 2:
                if col < 21:
                    set_color((0,1,0), (1,0,0))
                elif col < 41:
                    set_color((0,0,1), (0,1,0))
                else:
                    set_color((1,0,0), (0,0,1))
            CLK.value(1)  # a) CLK hi to shift in the color bit
            CLK.value(0)  # b) CLK lo to shift in the color bit
        OE.value(1)   # c) disable output
        LAT.value(1)  # d) LAT hi to load the shift register contents into the LED output
        LAT.value(0)  # e) LAT lo to load the shift register contents into the LED output
        A.value(row % 2)
        B.value((row // 2) % 2)
        C.value((row // 4) % 2)
        D.value((row // 8) % 2)
        E.value((row // 16) % 2)
        # print('>>', row)
        # print('A', A.value())
        # print('B', B.value())
        # print('C', C.value())
        # print('D', D.value())
        # print('E', E.value())
        OE.value(0)   # f) re-enable output

        time.sleep_ms(20)
    #time.sleep(1)

##-----------------------------------------------------------------------------
## 2)
'''
(https://www.sparkfun.com/news/2650
For each row of pixels, we repeat the following cycle of steps:
1. Clock in the data for the current row one bit at a time
2. Pull the latch and output enable pins high. This enables the latch, allowing the row data to reach the output driver but it also disables the output so that no LEDs are lit while we're switching rows.
3. Switch rows by driving the appropriate row select lines.
4. Pull the latch and output enable pins low again, enabling the output and closing the latch so we can clock in the next row of data.
'''
colors = [
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1), (1,1,0), (0,1,1),
    (1,0,1)
]

colors = [(0,0,0)] * 63 + [(1,0,0)]
colors = [(0,0,0)] * 63 + [(0,1,0)]
colors = [(0,0,0)] * 63 + [(0,0,1)]

reset()
for _ in range(50):
#while True:
    for row in range(16):
        ## 1) Clock in the data for the current row one bit at a time
        for i, col in enumerate(range(64)):
            set_color(colors[i], colors[i])
            CLK.value(1)
            CLK.value(0)
        ## 2) Pull the latch and output enable pins high.
        ## This enables the latch, allowing the row data to reach the output driver
        ## but it also disables the output so that no LEDs are lit while we're switching rows.
        LAT.value(1)
        OE.value(1)
        ## 3) Switch rows by driving the appropriate row select lines.
        A.value(row % 2)
        B.value((row // 2) % 2)
        C.value((row // 4) % 2)
        D.value((row // 8) % 2)
        E.value((row // 16) % 2)
        # print('>>', row)
        # print('A', A.value())
        # print('B', B.value())
        # print('C', C.value())
        # print('D', D.value())
        # print('E', E.value())
        ## 4) Pull the latch and output enable pins low again,
        ## enabling the output and closing the latch
        ## so we can clock in the next row of data.
        LAT.value(0)
        OE.value(0)

##-----------------------------------------------------------------------------

print("\n<<<< Done.\n")
