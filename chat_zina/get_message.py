import asyncio
import datetime
import aiofiles
import configargparse

parser = configargparse.ArgParser(default_config_files=['*.conf'])
parser.add('--host', help='set host')
parser.add('-p', '--port', help='set port')
parser.add('--history', help='path to save history')
options = parser.parse_args()


async def get_chat():
    reader, _ = await asyncio.open_connection(options.host, options.port)
    async with aiofiles.open(f'{options.history}history.txt', 'a') as file:
        while True:
            if reader.at_eof():
                break
            text = await reader.read(1024)
            date_time = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
            text = text.decode()
            await file.write(f'[{date_time}] {text}')
            print(text)


def main():
    asyncio.run(get_chat())


if __name__ == '__main__':
    main()