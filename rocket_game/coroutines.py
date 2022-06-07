import asyncio
import curses
import random

from simple_functions import draw_frame, read_controls, update_speed, get_frame_size
from variables import loop, obstacles, obstacles_in_last_collisions, year
from obstacles import Obstacle, show_obstacles
from explosion import EXPLOSION_FRAMES


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)

    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        for obst in obstacles:
            if obst.has_collision(row, column):
                obstacles_in_last_collisions.append(obst)
                return
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(random.randint(1, 20))

        canvas.addstr(row, column, symbol)
        await sleep(random.randint(1, 3))

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(random.randint(1, 5))

        canvas.addstr(row, column, symbol)
        await sleep(random.randint(1, 3))


async def show_gameover(canvas, frame):
    rows_number, columns_number = canvas.getmaxyx()
    draw_frame(canvas, rows_number / 2 - 5, columns_number / 2 - 30, frame)
    canvas.refresh()


async def animate_spaceship(canvas, row, column, ship, game_over):
    global loop
    sh = next(ship)
    draw_frame(canvas, row, column, sh, ship=True)
    await sleep(1)
    rows, columns = get_frame_size(sh)
    while True:
        draw_frame(canvas, row, column, next(ship), negative=True, ship=True)
        for el in obstacles:
            if el.has_collision(row, column, rows, columns):
                while True:
                    await show_gameover(canvas, game_over)
                    await sleep(1)
        rows_direction, columns_direction, is_fire = read_controls(canvas)
        row += rows_direction
        column += columns_direction
        if year > 2020 and is_fire:
            loop.create_task(fire(canvas, row, column + 2))
        draw_frame(canvas, row, column, next(ship), ship=True)
        next(ship)
        canvas.refresh()
        await sleep(2)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)
    rows, columns = get_frame_size(garbage_frame)
    row = 0
    obst = Obstacle(row, column, rows, columns)
    obstacles.append(obst)
    while row < rows_number:
        for el in obstacles_in_last_collisions.copy():
            if el == obst:
                obstacles.remove(el)
                obstacles_in_last_collisions.remove(el)
                loop.create_task(explode(canvas, row + rows / 2, column + columns / 2))
                return
        draw_frame(canvas, row, column, garbage_frame)
        await sleep(3)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obst.row = row
    obstacles.remove(obst)


async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in EXPLOSION_FRAMES:
        draw_frame(canvas, corner_row, corner_column, frame)
        await sleep(1)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await sleep(1)


async def derwin(canvas):
    while True:
        canvas.addstr(1, 1, str(year))
        await sleep(1)


async def up_year():
    global year
    while year < 2050:
        year += 1
        await sleep(20)


async def fill_orbit_with_garbage(canvas, garbages):
    global loop
    global year
    rows_number, columns_number = canvas.getmaxyx()
    while True:
        loop.create_task(
            fly_garbage(canvas, random.randint(1, columns_number - 1), random.choice(garbages), speed=year / 2000))
        loop.create_task(derwin(canvas))
        await sleep(2051 - year)


async def sleep(tics=1):
    for secs_left in range(tics, 0, -1):
        await asyncio.sleep(1 / 10)