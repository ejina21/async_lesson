import asyncio
import datetime
import json
from tkinter import messagebox
import time
from anyio import sleep, create_task_group, run
import async_timeout
import configargparse
import gui
import aiofiles

parser = configargparse.ArgParser(default_config_files=['send_conf.conf'])
parser.add('--host', help='set host')
parser.add('-p', '--port', help='set port')
parser.add('--token', help='set users token')
parser.add('--name', help='set your name')
parser.add('--message', help='set message, which you want to send')
parser.add('--history', help='path to save history')

options = parser.parse_args()


class InvalidToken(Exception):
    pass


async def check_token(reader):
    text = await reader.readline()
    if (data := json.loads(text.decode())) is None:
        messagebox.showinfo("Неверный токен", "Проверьте токен, сервер его не узнал.")
        raise InvalidToken
    return data["nickname"]


async def save_messages(filepath, queue, text):
    async with aiofiles.open(filepath, 'a') as file:
        date_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        await queue.put(await file.write(f'[{date_time}] {text}'))


async def read_history(filepath, queue):
    async with aiofiles.open(filepath, 'r') as file:
        queue.put_nowait(await file.read())


async def read_msgs(host, port, send_queue, status_queue, watch_queue):
    status_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    await read_history(options.history, send_queue)
    reader, _ = await asyncio.open_connection(host, port)
    save_queue = asyncio.Queue()
    while True:
        text = await reader.read(1024)
        send_queue.put_nowait(text.decode())
        watch_queue.put_nowait('New message in chat')
        await save_messages(options.history, save_queue, text.decode())


async def authenticate(token, reader, writer):
    await reader.readline()
    writer.write(f'{token}\n'.encode())
    nickname = await check_token(reader)
    return nickname


async def ping_pong(writer):
    while True:
        writer.write(f'\n\n'.encode())
        await sleep(1)


async def send_msgs(host, port, send_queue, status_queue, watch_queue):
    status_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    reader, writer = await asyncio.open_connection(host, port)
    watch_queue.put_nowait('Prompt before auth')
    nickname = await authenticate(options.token, reader, writer)
    watch_queue.put_nowait('Authorization done')
    status_queue.put_nowait(gui.NicknameReceived(nickname))
    while True:
        if send_queue.empty():
            writer.write(f'\n\n'.encode())
            await reader.read(1024)
            watch_queue.put_nowait('Ping is True')
            await sleep(1)
        else:
            message = await send_queue.get()
            writer.write(f'{message}\n\n'.encode())
            watch_queue.put_nowait('Message sent')


async def watch_for_connection(watch_queue, status_queue):
    while True:
        try:
            async with async_timeout.timeout(3) as cm:
                message = await watch_queue.get()
                status_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)
                status_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
                date = time.time()
                print(f'[{date}] {message}')
        except asyncio.exceptions.TimeoutError:
            if cm.expired:
                status_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)
                status_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
                print(f'[{date}] 1s timeout is elapsed')
                await sleep(5)


async def handle_connection():
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()
    try:
        async with create_task_group() as tg:
            tg.start_soon(gui.draw, messages_queue, sending_queue, status_updates_queue)
            tg.start_soon(read_msgs, options.host, 5000, messages_queue, status_updates_queue, watchdog_queue)
            tg.start_soon(send_msgs, options.host, 5050, sending_queue, status_updates_queue, watchdog_queue)
            tg.start_soon(watch_for_connection, watchdog_queue, status_updates_queue)
    except (KeyboardInterrupt, gui.TkAppClosed, InvalidToken):
        pass

if __name__ == '__main__':
    run(handle_connection)
