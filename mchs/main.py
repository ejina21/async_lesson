import uuid
from contextlib import suppress
from unittest.mock import AsyncMock, patch

import trio
import asks
from asks import BasicAuth
import os
from dotenv import load_dotenv
load_dotenv()
LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')
PHONE = os.getenv('PHONE')
# bytearray(b'accepted;11111111')
# bytearray(b'11111111;queued') https://api.iqsms.ru/messages/v2/status/
# method not found
# error;absent required param: text
# error;invalid mobile phone


class SmscApiError(Exception):
    pass


async def side_effect(*args, **kwargs):
    mock = AsyncMock()
    mock.content = bytearray(f'accepted;{uuid.uuid4()}'.encode())
    mock.status_code = 200
    return mock


@patch('asks.request', side_effect)
async def request_smsc(http_method: str, api_method: str, login: str, password: str, payload: dict = {}) -> dict:
    responce = await asks.request(
            http_method,
            f'https://api.iqsms.ru/messages/v2/{api_method}/',
            params=payload,
            auth=BasicAuth((login, password))
        )
    if responce.status_code != 200:
        raise SmscApiError
    content = responce.content.decode("utf-8")
    if content in ['', 'method not found'] or 'error' in content:
        raise SmscApiError
    return {'text': content}


async def grabber():
    payload = {
        'phone': PHONE,
        'text': 'Сегодня будет гроза!',
    }
    responce = await request_smsc('GET', 'status', login=LOGIN, password=PASSWORD, payload=payload)
    # responce = await request_smsc('GET', 'noteexists', login=LOGIN, password=PASSWORD, payload=payload)
    # responce = await request_smsc('GET', 'send', login=LOGIN, password=PASSWORD, payload=payload)
    print(responce)


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(grabber)


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        trio.run(main)