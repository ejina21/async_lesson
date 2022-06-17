import asyncio
import configargparse
import logging
import json

parser = configargparse.ArgParser(default_config_files=['send_conf.conf'])
parser.add('--host', help='set host')
parser.add('-p', '--port', help='set port')
parser.add('--token', help='set users token')
parser.add('--name', help='set your name')
parser.add('--message', help='set message, which you want to send')

options = parser.parse_args()


def set_logging():
    logging.basicConfig(
        filename='logs.log',
        filemode='a',
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG
    )


async def write_to_log(reader):
    text = await reader.read(1024)
    logging.info(f'sender:{text.decode()}')


async def check_token(reader, writer):
    text = await reader.readline()
    logging.info(f'sender:{text.decode()}')
    if data := json.loads(text.decode()) is None:
        await write_to_log(reader)
        message = input('Token is wrong. Write new username:').replace("\n", "")
        writer.write(f'{message}\n\n'.encode())
        logging.info(f'writer:{message}')
    else:
        print(f'Выполнена авторизация. Пользователь {data["username"]}.')


async def send_message_chat(reader, writer):
    while True:
        await write_to_log(reader)
        if options.message:
            message = options.message.replace("\n", "")
            writer.write(f'{message}\n\n'.encode())
            logging.info(f'writer:{message}')
            break
        message = input('Write message:').replace("\n", "")
        writer.write(f'{message}\n\n'.encode())
        logging.info(f'writer:{message}')


async def authenticate(token):
    reader, writer = await asyncio.open_connection(options.host, options.port)
    await write_to_log(reader)
    writer.write(f'{token}\n'.encode())
    logging.info(f'writer:{token}')
    await check_token(reader, writer)
    return reader, writer


async def register():
    reader, writer = await asyncio.open_connection(options.host, options.port)
    writer.write('\n'.encode())
    await write_to_log(reader)
    username = input('Write your username:').replace("\n", "") if not options.name else options.name.replace("\n", "")
    writer.write(f'{username}\n\n'.encode())
    logging.info(f'writer:{username}')
    text = await reader.readline()
    text = json.loads(text.decode())
    print(f"Ваш токен: {text['account_hash']}")


async def main():
    set_logging()
    await register()
    token = input('Input token:').replace("\n", "") if not options.token else options.token.replace("\n", "")
    reader, writer = await authenticate(token)
    await send_message_chat(reader, writer)


if __name__ == '__main__':
    asyncio.run(main())
