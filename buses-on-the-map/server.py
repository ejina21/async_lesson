from contextlib import suppress
import configargparse

import trio
from trio_websocket import serve_websocket, ConnectionClosed
import json
from fake_bus import options, relaunch_on_disconnect
from dataclasses import dataclass


parser = configargparse.ArgParser(default_config_files=['setting_server.conf'])
parser.add('-bp', '--bus_port', type=int, help='порт для имитатора автобусов')
parser.add('-p', '--browser_port', type=int, help='порт для браузера')

ports = parser.parse_args()
buses = {}


@dataclass
class WindowBounds:
    east_lng: float
    north_lat: float
    south_lat: float
    west_lng: float

    def is_inside(self, lat, lng):
        if self.west_lng <= lng <= self.east_lng and self.south_lat <= lat <= self.north_lat:
            return True
        return False

    def update(self, south_lat, north_lat, west_lng, east_lng):
        self.south_lat = south_lat
        self.north_lat = north_lat
        self.west_lng = west_lng
        self.east_lng = east_lng


async def talk_to_browser(ws, bounds):
    while True:
        data = {
            "msgType": "Buses",
            "buses": [el for _, el in buses.items() if bounds.is_inside(el['lat'], el['lng'])]
        }
        print(len(data['buses']))
        await ws.send_message(json.dumps(data))
        await trio.sleep(options.refresh_timeout)


async def echo_server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            message = json.loads(message)
            bus_id = message['busId']
            buses[bus_id] = message
            print(message)
        except ConnectionClosed:
            break
        except (KeyError, json.JSONDecodeError):
            print(json.dumps({"errors": ["Requires valid JSON"], "msgType": "Errors"}))


async def listen_browser(ws, bounds):
    while True:
        try:
            message = await ws.get_message()
            mes = json.loads(message)
            data = mes['data']
            bounds.update(data['south_lat'], data['north_lat'], data['west_lng'], data['east_lng'])
        except (KeyError, json.JSONDecodeError):
            print(json.dumps({"errors": ["Requires valid JSON"], "msgType": "Errors"}))


async def browser_server(request):
    ws = await request.accept()
    bounds = WindowBounds(37.65563964843751, 55.77367652953477, 55.72628839374007, 37.54440307617188)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, bounds)
        nursery.start_soon(talk_to_browser, ws, bounds)


@relaunch_on_disconnect
async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, echo_server, '127.0.0.1', ports.bus_port, None)
        nursery.start_soon(serve_websocket, browser_server, '127.0.0.1', ports.browser_port, None)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        trio.run(main)
