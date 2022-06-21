from dataclasses import asdict, dataclass

import configargparse
import trio
from sys import stderr
from trio_websocket import open_websocket_url, HandshakeError, ConnectionClosed
import json
import os
import random
from contextlib import suppress

parser = configargparse.ArgParser(default_config_files=['setting.conf'])
parser.add('--server', help='адрес сервера')
parser.add('-rb', '--routes_number', type=int, help='количество маршрутов')
parser.add('-bpr', '--buses_per_route', type=int, help='количество автобусов на каждом маршруте')
parser.add('-ws', '--websockets_number', type=int, help='количество открытых веб-сокетов')
parser.add('-id', '--emulator_id', help='префикс к busId на случай запуска нескольких экземпляров имитатора')
parser.add('-rt', '--refresh_timeout', type=int, help='задержка в обновлении координат сервера')

options = parser.parse_args()


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


def relaunch_on_disconnect(async_function):
    async def wrapper(*args, **kwargs):
        while True:
            try:
                await async_function(*args, **kwargs)
            except (HandshakeError, ConnectionClosed):
                print('Нет соединения, повторная попытка...')
                await trio.sleep(3)
    return wrapper


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"


@relaunch_on_disconnect
async def send_updates(receive_channel):
    async with open_websocket_url(f'ws://{options.server}') as ws:
        async for value in receive_channel:
            await ws.send_message(value)


async def run_bus(send_channel, bus_id, route):
    coordinates = route['coordinates']
    i = random.randint(0, len(coordinates) - 1)
    bus = Bus(bus_id, 0, 0, route['name'])
    while True:
        coord = coordinates[i]
        bus.lat = coord[0]
        bus.lng = coord[1]
        await send_channel.send('sdsdsds')#json.dumps(asdict(bus), ensure_ascii=False)
        if i == len(coordinates) - 1:
            i = -1
        i += 1
        await trio.sleep(options.refresh_timeout)


async def main():
    try:
        async with trio.open_nursery() as nursery:
            send_channels = []
            for i in range(options.websockets_number):
                send_channel, receive_channel = trio.open_memory_channel(0)
                send_channels.append(send_channel)
                nursery.start_soon(send_updates, receive_channel)
            for count, route in enumerate(load_routes()):
                for i in range(options.buses_per_route):
                    nursery.start_soon(
                        run_bus,
                        random.choice(send_channels),
                        generate_bus_id(f'{options.emulator_id}_{route["name"]}', i),
                        route
                    )
                if count >= options.routes_number:
                    break
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        trio.run(main)
