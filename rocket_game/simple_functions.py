import math

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas):
    row = column = 0
    space_pressed = False
    row_speed = column_speed = 0

    while True:
        pressed_key_code = canvas.getch()
        if pressed_key_code == -1:
            break
        if pressed_key_code == UP_KEY_CODE:
            row_speed, column_speed = update_speed(row_speed, column_speed, -1, 0)
        if pressed_key_code == DOWN_KEY_CODE:
            row_speed, column_speed = update_speed(row_speed, column_speed, 1, 0)
        if pressed_key_code == RIGHT_KEY_CODE:
            column_speed = 0.5
            row_speed, column_speed = update_speed(row_speed, column_speed, 0, 1)
        if pressed_key_code == LEFT_KEY_CODE:
            column_speed = -0.5
            row_speed, column_speed = update_speed(row_speed, column_speed, 0, -1)
        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True
        row += row_speed
        column += column_speed
    return row, column, space_pressed


def get_frame_size(text):
    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def draw_frame(canvas, start_row, start_column, text, negative=False, ship=False):
    rows_number, columns_number = canvas.getmaxyx()
    rows, columns = get_frame_size(text)
    if ship:
        start_row = max(0, start_row)
        start_row = min(rows_number - rows, start_row)
        start_column = max(0, start_column)
        start_column = min(columns_number - columns, start_column)

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue
        if row >= rows_number:
            break
        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue
            if column >= columns_number:
                break
            if symbol == ' ':
                continue
            if row == rows_number - 1 and column == columns_number - 1:
                continue
            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def _limit(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _apply_acceleration(speed, speed_limit, forward=True):
    """Change speed — accelerate or brake — according to force direction."""

    speed_limit = abs(speed_limit)

    speed_fraction = speed / speed_limit

    delta = math.cos(speed_fraction) * 0.75

    if forward:
        result_speed = speed + delta
    else:
        result_speed = speed - delta

    result_speed = _limit(result_speed, -speed_limit, speed_limit)

    if abs(result_speed) < 0.1:
        result_speed = 0

    return result_speed


def update_speed(row_speed, column_speed, rows_direction, columns_direction, row_speed_limit=2, column_speed_limit=2,
                 fading=0.8):
    """Update speed smootly to make control handy for player. Return new speed value (row_speed, column_speed)

    rows_direction — is a force direction by rows axis. Possible values:
       -1 — if force pulls up
       0  — if force has no effect
       1  — if force pulls down

    columns_direction — is a force direction by colums axis. Possible values:
       -1 — if force pulls left
       0  — if force has no effect
       1  — if force pulls right
    """

    if rows_direction not in (-1, 0, 1):
        raise ValueError(f'Wrong rows_direction value {rows_direction}. Expects -1, 0 or 1.')

    if columns_direction not in (-1, 0, 1):
        raise ValueError(f'Wrong columns_direction value {columns_direction}. Expects -1, 0 or 1.')

    if fading < 0 or fading > 1:
        raise ValueError(f'Wrong columns_direction value {fading}. Expects float between 0 and 1.')

    row_speed *= fading
    column_speed *= fading

    row_speed_limit, column_speed_limit = abs(row_speed_limit), abs(column_speed_limit)

    if rows_direction != 0:
        row_speed = _apply_acceleration(row_speed, row_speed_limit, rows_direction > 0)

    if columns_direction != 0:
        column_speed = _apply_acceleration(column_speed, column_speed_limit, columns_direction > 0)

    return row_speed, column_speed