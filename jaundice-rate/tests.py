import asyncio

import aiohttp
import pytest
from text_tools import calculate_jaundice_rate, split_by_words
import pymorphy2
from main import process_article, ProcessingStatus


def test_calculate_jaundice_rate():
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert 33.0 < calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']) < 34.0


@pytest.mark.asyncio
async def test_process_article():
    async with aiohttp.ClientSession() as session:
        morph = pymorphy2.MorphAnalyzer()
        charged_words = ['hello', 'ветер', 'память', 'место']
        list_test = []
        await process_article(session, morph, charged_words, 'https://inosmi.ru/20220618/pulemety-254.html', 'TEST', list_test)
        assert list_test[1] == ProcessingStatus.FETCH_ERROR.name
        await process_article(session, morph, charged_words, 'https://en.wikipedia.org/wiki/Main_Page', 'TEST', list_test)
        assert list_test[6] == ProcessingStatus.PARSING_ERROR.name
        await process_article(session, morph, charged_words, 'https://inosmi.ru/20220618/vladimir-254551104.html', 'TEST', list_test, fetch_timeout=0.2)
        assert list_test[11] == ProcessingStatus.TIMEOUT.name
        await process_article(session, morph, charged_words, 'https://inosmi.ru/20220618/vladimir-254551104.html', 'TEST', list_test, words_timeout=0.001)
        assert list_test[16] == ProcessingStatus.TIMEOUT.name


def test_split_by_words():
    # Экземпляры MorphAnalyzer занимают 10-15Мб RAM т.к. загружают в память много данных
    # Старайтесь организовать свой код так, чтоб создавать экземпляр MorphAnalyzer заранее и в единственном числе
    morph = pymorphy2.MorphAnalyzer()
    assert asyncio.run(split_by_words(morph, 'Во-первых, он хочет, чтобы')) == ['во-первых', 'хотеть', 'чтобы']
    assert asyncio.run(split_by_words(morph, '«Удивительно, но это стало началом!»')) == ['удивительно', 'это', 'стать', 'начало']
