import time

import Quartz

from config import MOVE_DURATION, CLICK_PAUSE


def quartz_move(x, y):
    event = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventMouseMoved,
        (x, y),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def quartz_click(x, y):
    print(f"Moving to: {x:.1f}, {y:.1f}")

    current = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    start_x, start_y = current.x, current.y

    steps = 40
    for i in range(1, steps + 1):
        t = i / steps
        nx = start_x + (x - start_x) * t
        ny = start_y + (y - start_y) * t
        quartz_move(nx, ny)
        time.sleep(MOVE_DURATION / steps)

    # Wiggle signal
    for dx in (15, -30, 15):
        quartz_move(x + dx, y)
        time.sleep(0.1)

    quartz_move(x, y)
    time.sleep(CLICK_PAUSE)

    down = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseDown,
        (x, y),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)

    time.sleep(0.05)

    up = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseUp,
        (x, y),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)

    print("Clicked")
