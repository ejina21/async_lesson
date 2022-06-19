import aiohttp
from aiohttp import web
from anyio import create_task_group, run
import pymorphy2
from main import make_charged_words, process_article


async def handle(request):
    data = []
    async with aiohttp.ClientSession() as session:
        urls = request.rel_url.query.get('urls', '').split(',')
        if len(urls) > 10:
            return web.json_response({'error': 'too many urls in request, should be 10 or less'})
        morph = pymorphy2.MorphAnalyzer()
        charged_words1 = await make_charged_words('charged_dict/negative_words.txt')
        charged_words2 = await make_charged_words('charged_dict/positive_words.txt')
        charged_words = charged_words2 + charged_words1
        result_list = []
        async with create_task_group() as tg:
            for url in urls:
                tg.start_soon(process_article, session, morph, charged_words, url, 'TEST', result_list)
        for i in range(0, len(result_list), 5):
            data.append({
                "status": result_list[i + 1],
                "url": result_list[i + 4],
                "score": result_list[i + 2],
                "words_count": result_list[i + 3],
            })
    return web.json_response(data=data)

app = web.Application()
app.add_routes([web.get('/', handle)])

if __name__ == '__main__':
    web.run_app(app)
