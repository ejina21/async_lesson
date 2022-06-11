import asyncio
import os
from aiohttp import web
import aiofiles
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--log', nargs='?', help='Включить логирование', default=False, const=True)
parser.add_argument('--path', type=str, help='Путь к каталогу с файлами', default='test_photos')
parser.add_argument('--delay', type=int, help='Задать задержку ответа', default=0)
args = parser.parse_args()

if args.log:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.FATAL)


async def archive(request):
    response = web.StreamResponse()
    name = request.match_info.get('archive_hash', 'archive')
    if not os.path.exists(f'{args.path}/{name}'):
        raise web.HTTPNotFound(text='Архив не существует или был удален')
    response.headers['Content-Type'] = 'multipart/form-data'
    response.headers['Content-Disposition'] = f'attachment; filename="{name}.zip"'
    await response.prepare(request)
    process = await asyncio.create_subprocess_shell(f'zip -r - {name}', stdout=asyncio.subprocess.PIPE, cwd=args.path)
    try:
        while True:
            archive = await process.stdout.read(n=5000)
            if process.stdout.at_eof():
                break
            logging.info('Sending archive chunk ...')
            await response.write(archive)
            if args.delay:
                await asyncio.sleep(args.delay)
    except asyncio.CancelledError:
        logging.error('Download was interrupted')
        response.force_close()
        raise
    finally:
        process.kill()
    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archive),
    ])
    web.run_app(app)
