# -*- coding: utf-8 -*-

"""
Main script to demo threading with asyncio.

https://github.com/peterhinch/micropython-async/
https://glyph.twistedmatrix.com/2014/02/unyielding.html

@author: ChatGPT+mada
@version: 2023-03-02
"""

try:
    import utime as time
    import uasyncio as asyncio
    embedded = True
except ModuleNotFoundError:
    import time
    import asyncio
    embedded = False
    # import nest_asyncio
    # nest_asyncio.apply()

##*****************************************************************************
##*****************************************************************************

## 1)
# async def bar():
#     count = 0
#     while True:
#         count += 1
#         print(count)
#         await asyncio.sleep(1)
# asyncio.run(bar())

## 2)
# async def bar(x):
#     count = 0
#     while True:
#         count += 1
#         print('Instance: {} count: {}'.format(x, count))
#         await asyncio.sleep(1)  # Pause 1s
# async def main():
#     for x in range(3):
#         asyncio.create_task(bar(x))
#     print('Tasks are running ...')
#     await asyncio.sleep(5)
# asyncio.run(main())

## 2b)
# async def bar(x):
#     count = 0
#     while True:
#         count += 1
#         print('Instance: {} count: {}'.format(x, count))
#         await asyncio.sleep(1)  # Pause 1s
# async def main():
#     tasks = []
#     for x in range(3):
#         tasks.append(asyncio.create_task(bar(x)))
#     print('Tasks are running ...')
#     for task in tasks:
#         print(task)
#     await asyncio.sleep(5)
#     return tasks
# tasks = asyncio.run(main())
# for task in tasks:
#     print(task)
#     task.cancel()
#     print(task)

## 3)
# async def bar(t):
#     print('Bar started: waiting {}secs'.format(t))
#     await asyncio.sleep(t)
#     print('Bar done')
# async def main():
#     await bar(1)  # Pauses here until bar is complete
#     task = asyncio.create_task(bar(5))
#     await asyncio.sleep(0)  # bar has now started
#     print('Got here: bar running')  # Can run code here
#     await task  # Now we wait for the bar task to complete
#     print('All done')
# asyncio.run(main())

## 4)
# async def schedule(cbk, t, *args, **kwargs):
#     await asyncio.sleep(t)
#     cbk(*args, **kwargs)
# def callback(x, y):
#     print('x={} y={}'.format(x, y))
# async def bar():
#     asyncio.create_task(schedule(callback, 3, 42, 100))
#     for count in range(6):
#         print(count)
#         await asyncio.sleep(1)
# asyncio.run(bar())

## 5) embedded structure proposal ---------------------------------------------
# class MyClass():
#     async def foo(self):
#         print('foo!')
#         await asyncio.sleep(1)
#     async def run_forever(self):
#         while True:
#             print('.')
#             await asyncio.sleep(1)

# def set_global_exception():
#     def handle_exception(loop, context):
#         import sys
#         sys.print_exception(context["exception"])
#         sys.exit()
#     loop = asyncio.get_event_loop()
#     loop.set_exception_handler(handle_exception)

# async def main():
#     set_global_exception()  # debug aid
#     my_class = MyClass()  # constructor might create tasks
#     asyncio.create_task(my_class.foo())  # or you might do this
#     await my_class.run_forever()  # non-terminating method
# try:
#     asyncio.run(main())
# finally:
#     asyncio.new_event_loop()  # clear retained state

## 6)
# async def task(i, lock):
#     while 1:
#         await lock.acquire()
#         print("Acquired lock in task", i)
#         await asyncio.sleep(0.5)
#         lock.release()

# async def main():
#     lock = asyncio.Lock()  # the Lock instance
#     for n in range(1, 4):
#         asyncio.create_task(task(n, lock))
#     await asyncio.sleep(5)  # run for 5s

# asyncio.run(main())

## 7) simple scheduler --------------------------------------------------------
# async def task(i, lock):
#     while True:
#         await lock.acquire()
#         print("Acquired lock in task", i)
#         await asyncio.sleep(0.1)
#         lock.release()

# async def clocktick(lock):
#     while True:
#         await lock.acquire()
#         now = time.localtime()
#         print("Tick: {:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5]))
#         lock.release()
#         await asyncio.sleep(1)  # wait one second, allowing other coros to run

# async def main():
#     lock = asyncio.Lock()  # The Lock instance
#     # for n in range(1, 4):
#     asyncio.create_task(task(1, lock))
#     asyncio.create_task(clocktick(lock))
#     await asyncio.sleep(5)  # run for 5s

# asyncio.run(main())

## 8) calculated scheduler ---------------------------------------------------------
# async def task(i, lock):
#     while True:
#         await lock.acquire()
#         print("Acquired lock in task #%i: %.3f" % (i, time.time()))
#         time.sleep(0.1)
#         lock.release()
#         await asyncio.sleep(0)

# async def clocktick(lock):
#     global counter
#     counter = 1
#     ## init a counter between runs for precise scheduling
#     last_tick = time.time() - 1
#     while True:
#         t_start = time.time()
#         await lock.acquire()
#         t_diff = t_start - last_tick - 1
#         # now = time.localtime()
#         # print("Tick: {:02d}:{:02d}:{:02d}".format(now[3], now[4], now[5]))
#         ## simulate long operation
#         time.sleep(0.2)
#         now = time.time()
#         t_duration =  now - t_start
#         last_tick = now
#         print("Last tick:   {:.3f}".format(last_tick))
#         print("     Tick:   {:.3f}".format(t_start))
#         print("          Delta:       {:.3f}".format(t_diff))
#         print("          Duration:    {:.3f}".format(t_duration))
#         print("     Now:    {:.3f}".format(now))
#         lock.release()
#         counter += 1
#         await asyncio.sleep(1 - t_diff - t_duration)  # wait one second, allowing other coros to run

# async def main():
#     ## create the Lock instance
#     lock = asyncio.Lock()

#     asyncio.create_task(task(1, lock))
#     asyncio.create_task(clocktick(lock))
#     await asyncio.sleep(5)  # run for 5s
#     print(">>>> ", counter)

# asyncio.run(main())

# try:
#     asyncio.run(main())
# finally:
#     ## Clear retained state
#     asyncio.new_event_loop()
#     _ = asyncio.new_event_loop()

## 9) timed scheduler ---------------------------------------------------------
from machine import Timer

ts_clocktick = time.time()


def clocktick(timer):
    global ts_clocktick
    ts_clocktick += 1


tim = Timer(0)
tim.init(period=1000, mode=Timer.PERIODIC, callback=clocktick)


async def task(i, lock):
    while True:
        await lock.acquire()
        print("Acquired lock in task #%i: %.3f" % (i, time.time()))
        time.sleep(0.1)
        lock.release()
        await asyncio.sleep(0)


async def update(lock):
    while True:
        await lock.acquire()
        print("     Tick:   {:.3f}".format(ts_clocktick))
        time.sleep(0.2)
        lock.release()
        await asyncio.sleep(1)


async def main():
    ## create the Lock instance
    lock = asyncio.Lock()
    ## create co-routines (cooperative tasks)
    asyncio.create_task(task(1, lock))
    asyncio.create_task(update(lock))

    await asyncio.sleep(5)  # run for 5s


asyncio.run(main())

try:
    asyncio.run(main())
finally:
    ## Clear retained state
    _ = asyncio.new_event_loop()
