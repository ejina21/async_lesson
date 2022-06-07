import curses
import random
from itertools import cycle
from coroutines import blink, animate_spaceship, fill_orbit_with_garbage, up_year
from variables import loop


def _get_cycle_frame(path_1, path_2):
    with open(path_1, 'r') as f:
        frame1 = f.read()
    with open(path_2, 'r') as f:
        frame2 = f.read()
    animate = cycle([frame1, frame2])
    return animate


def _get_frame(path_1):
    with open(path_1, "r") as f:
      frame = f.read()
    return frame


def draw(canvas):
    global coroutines
    ship = _get_cycle_frame('frames/rocket_frame_1.txt', 'frames/rocket_frame_2.txt')
    garbage1 = _get_frame('frames/garbage_1.txt')
    garbage2 = _get_frame('frames/garbage_2.txt')
    garbage3 = _get_frame('frames/garbage_3.txt')
    game_over = _get_frame('frames/game_over.txt')
    curses.curs_set(False)
    canvas.nodelay(True)
    row, column = canvas.getmaxyx()
    for _ in range(20):
        loop.create_task(
            blink(
                  canvas,
                  random.randint(1, row - 2),
                  random.randint(1, column - 2),
                  random.choice('+*.:')
              )
        )
    loop.create_task(animate_spaceship(canvas, row // 2, column // 2, ship, game_over))
    loop.create_task(fill_orbit_with_garbage(canvas, (garbage1, garbage2, garbage3)))
    loop.create_task(up_year())
    loop.run_forever()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)