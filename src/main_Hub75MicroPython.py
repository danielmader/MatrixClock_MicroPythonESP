"""
Main script to demo the HUB75 library.

Uses a custom pinout.
"""

import hub75
import matrixdata
from logo import logo
from planets import earth, saturn
import bouncer

ROW_SIZE = 32
COL_SIZE = 64

config = hub75.Hub75SpiConfiguration()
##-----------------------------------------------------------------------------
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
config.illumination_time_microseconds = 25
##-----------------------------------------------------------------------------
matrix = matrixdata.MatrixData(ROW_SIZE, COL_SIZE)
hub75spi = hub75.Hub75Spi(matrix, config)

# Show Python Logo
matrix.set_pixels(0, 16, logo)
for i in range(100):
    hub75spi.display_data()

# Show bouncing objects
earth_bounce = bouncer.Bouncer(0, 0, len(earth[0]), len(earth), COL_SIZE - 1, ROW_SIZE - 1, dx=2)
saturn_bounce = bouncer.Bouncer(20, 10, len(saturn[0]), len(saturn), COL_SIZE - 1, ROW_SIZE - 1, dx=-2)
square = [
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    [1,1,2,2,3,3,4,4,5,5,6,6,7,7],  # noqa
    ]
square_bounce = bouncer.Bouncer(0,0, width=len(square[0]), height=len(square), max_x=63, max_y=31, min_x=0, min_y=0, dx=1, dy=1)  # noqa

while True:
    print('>> clear_dirty_bytes()')
    matrix.record_dirty_bytes = True
    for i in range(200):
        earth_bounce.update()
        saturn_bounce.update()
        square_bounce.update()

        matrix.clear_dirty_bytes()
        matrix.set_pixels(earth_bounce.y, earth_bounce.x, earth)
        matrix.set_pixels(saturn_bounce.y, saturn_bounce.x, saturn)
        matrix.set_pixels(square_bounce.y, square_bounce.x, square)
        hub75spi.display_data()

    print('>> clear_all_bytes()')
    matrix.record_dirty_bytes = False
    for i in range(200):
        earth_bounce.update()
        saturn_bounce.update()
        square_bounce.update()

        matrix.clear_all_bytes()
        matrix.set_pixels(earth_bounce.y, earth_bounce.x, earth)
        matrix.set_pixels(saturn_bounce.y, saturn_bounce.x, saturn)
        matrix.set_pixels(square_bounce.y, square_bounce.x, square)
        hub75spi.display_data()
