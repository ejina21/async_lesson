import warnings

from quart import websocket, request
from quart_trio import QuartTrio
from trio import sleep
import trio
import trio_asyncio
from trio_asyncio import TrioAsyncioDeprecationWarning
from hypercorn.trio import serve
from hypercorn.config import Config as HyperConfig
from main import request_smsc, LOGIN, PASSWORD, PHONE
import json
import argparse
import aioredis
from sms_sending_db.db import Database
warnings.simplefilter('ignore', TrioAsyncioDeprecationWarning)


def create_argparser():
    parser = argparse.ArgumentParser(description='Redis database usage example')
    parser.add_argument(
        '--address',
        action='store',
        dest='redis_uri',
        help='Redis URL. See examples at https://aioredis.readthedocs.io/en/latest/api/high-level/#aioredis.client.Redis.from_url',
        default='redis://localhost'
    )
    return parser


app = QuartTrio(__name__)


@app.route('/send/', methods=["POST"])
async def send():
    if request.method == "POST":
        form = await request.form
        payload = {
            'phone': PHONE,
            'text': form['text'],
        }

        responce = await request_smsc('GET', 'send', login=LOGIN, password=PASSWORD, payload=payload)
        status, sms_id = responce['text'].split(';')

        await trio_asyncio.aio_as_trio(app.db.add_sms_mailing(sms_id, [payload['phone']], payload['text']))

        sms_mailings = await trio_asyncio.aio_as_trio(app.db.get_sms_mailings(sms_id))
        print('sms_mailings')
        print(sms_mailings)
        pending_sms_list = await trio_asyncio.aio_as_trio(app.db.get_pending_sms_list())
        print('pending:')
        print(pending_sms_list)
        print(f'SMS с текстом {form["text"]} отправлено')
        return {}


@app.route('/')
async def hello():
    return await app.send_static_file('index.html')


@app.websocket('/ws')
async def ws():
    while True:
        data = {
            "msgType": "SMSMailingStatus",
            "SMSMailings": [],
        }
        pending_sms_list = await trio_asyncio.aio_as_trio(app.db.list_sms_mailings())
        sms_mailings = await trio_asyncio.aio_as_trio(app.db.get_sms_mailings(*pending_sms_list))
        for mail in sms_mailings:
            data['SMSMailings'].append(
                {
                    "timestamp": mail['created_at'],
                    "SMSText": mail['text'],
                    "mailingId": mail['sms_id'],
                    "totalSMSAmount": mail['phones_count'],
                    "deliveredSMSAmount": 0,
                    "failedSMSAmount": 0,
                }
            )
        await websocket.send(json.dumps(data))
        await sleep(2)


@app.before_serving
async def create_db_pool():
    parser = create_argparser()
    args = parser.parse_args()
    app.redis = aioredis.from_url(args.redis_uri, decode_responses=True)
    await trio_asyncio.aio_as_trio(app.redis.flushdb())
    app.db = Database(app.redis)


@app.after_serving
async def close_db_pool():
    await app.redis.close()


async def run_server():
    async with trio_asyncio.open_loop() as loop:
        config = HyperConfig()
        config.bind = [f"127.0.0.1:5000"]
        config.use_reloader = True
        app.static_folder = 'templates'
        await serve(app, config)


if __name__ == "__main__":
    trio.run(run_server)

