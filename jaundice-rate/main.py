import asyncio
from contextlib import contextmanager
from enum import Enum
import time
import aiohttp
import async_timeout
import pymorphy2
import logging
import aiofiles
from anyio import create_task_group, run
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from text_tools import split_by_words, calculate_jaundice_rate

TEST_ARTICLES = [
    'https://inosmi.ru/20220618/politika-254580026.html',
    'https://inosmi.ru/20220618/krizis-254590298.html',
    'https://inosmi.ru/20220618/vladimir-254551104.html',
    'https://inosmi.ru/20220618/turtsiya-254590685.html',
    'https://inosmi.ru/20220618/pulemety-254.html',
    'https://en.wikipedia.org/wiki/Main_Page',
]

logging.basicConfig(level=logging.DEBUG)


@contextmanager
def analys_time(*args, **kwargs):
    start_time = time.monotonic()
    try:
        yield
    finally:
        logging.info(f'Анализ {kwargs["name"]} закончен за {round(time.monotonic() - start_time, 2)} сек')


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def make_charged_words(path):
    async with aiofiles.open(path, 'r') as file:
        text = await file.read()
        return text.split('\n')


async def process_article(session, morph, charged_words, url, title, result_list, fetch_timeout=2, words_timeout=3):
    score = None
    len_words = None
    try:
        async with async_timeout.timeout(fetch_timeout) as cm:
            html = await fetch(session, url)
        clean_plaintext = sanitize(html, plaintext=True)
        with analys_time(name=title):
            async with async_timeout.timeout(words_timeout) as cm:
                words = await split_by_words(morph, clean_plaintext)
            score = calculate_jaundice_rate(words, charged_words)
        len_words = len(words)
        status = ProcessingStatus.OK.name
    except aiohttp.ClientError:
        status = ProcessingStatus.FETCH_ERROR.name
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR.name
    except asyncio.exceptions.TimeoutError:
        if cm.expired:
            status = ProcessingStatus.TIMEOUT.name
    result_list.append(title)
    result_list.append(status)
    result_list.append(score)
    result_list.append(len_words)
    result_list.append(url)


async def test_new(morph, charged_words):
    async with aiofiles.open('gogol_nikolay_taras_bulba_-_bookscafenet.txt', 'r') as file:
        text = await file.read()

    try:
        with analys_time(name='GOGOL') as cm:
            async with async_timeout.timeout(3) as cm:
                words = await split_by_words(morph, text)
            score = calculate_jaundice_rate(words, charged_words)
        print(len(words), score)
    except asyncio.exceptions.TimeoutError:
        if cm.expired:
            print('Время истекло')


async def main():
    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        charged_words1 = await make_charged_words('charged_dict/negative_words.txt')
        charged_words2 = await make_charged_words('charged_dict/positive_words.txt')
        charged_words = charged_words2 + charged_words1
        result_list = []
        # await test_new(morph, charged_words)
        async with create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(process_article, session, morph, charged_words, url, 'TEST', result_list)
        for i in range(0, len(result_list), 5):
            print('Заголовок:', result_list[i])
            print('Статус:', result_list[i + 1])
            print('Рейтинг:', result_list[i + 2])
            print('Слов в статье:', result_list[i + 3])


if __name__ == '__main__':
    run(main)
