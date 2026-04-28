import asyncio
import re
import sys
from os import getenv

import yandex_music as ym
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
TG_API = getenv('TG_API')

dp = Dispatcher()


@dp.message(Command('start'))
async def start(message: types.Message) -> None:
    '''
    start message if user wrote /start
    :param message: message from Telegram
    :return: None
    '''
    start_message = ('Приветствую! Отправь мне ссылку на трек и получи информацию о нём:\n'
                     '1. Название\n'
                     '2. Исполнитель\n'
                     '3. Длительность')
    await message.answer(text=start_message)


def parse_message_for_track(url: str) -> int | None:
    '''
    Parsing message text for track id
    :param url: track url
    :return: int(track_id)
    '''
    pattern = re.compile(r'/track/(\d+)')
    match = pattern.search(url)
    if not match:
        return None
    track_id = int(match.group(1))
    return track_id


async def get_track_info(client, /, track_id) -> dict | None:
    '''
    Finding track info by id
    :param client: yandex_music-client
    :param track_id: track_id
    :return: dict(track_info)
    '''
    track = await client.tracks([track_id])
    if track:
        track = track[0]
        track_info = {
            'id': track.id,
            'title': track.title,
            'artists': [artist.name for artist in track.artists],
            'duration_seconds': track.duration_ms // 1000,
        }
        return track_info
    return None


def get_duration_in_minutes(seconds: int) -> str:
    '''
    Convert seconds to mm:ss format
    :param seconds: seconds to convert
    :return: str(minutes:seconds)
    '''
    minutes = seconds // 60
    seconds = seconds % 60
    return f'{minutes:02d}:{seconds:02d}'


@dp.message(F.text.contains('/track'))
async def track_id_handle(message: types.Message) -> None:
    '''
    Track url handler
    :param message: message from Telegram
    :return: None
    '''
    client = ym.ClientAsync()
    await client.init()
    track_id = parse_message_for_track(message.text)
    if not track_id:
        await message.answer(text='Не удалось извлечь id трека. Проверьте корректность ссылки и попробуйте снова.')
        return None
    track_info_dict = await get_track_info(client, track_id)
    if not track_info_dict:
        await message.answer(text='Не удалось найти трек по приведённой ссылке.')
        return None
    await message.answer(text=
                         f'Информация о треке \"{track_info_dict.get('id')}\":\n'
                         f'1. Название: {track_info_dict.get('title')}\n'
                         f'2. Исполнители: {''.join([f'\n - {i}' for i in track_info_dict.get('artists')])}\n'
                         f'3. Длительность: {get_duration_in_minutes(track_info_dict.get('duration_seconds'))}'
                         )


async def main():
    print('Bot started')
    bot = None
    for arg in sys.argv:
        if arg.startswith('--proxy='):
            proxy = arg.split('=')[1]
            session = AiohttpSession(proxy=proxy)
            bot = Bot(token=TG_API, session=session)
    if not bot:
        bot = Bot(token=TG_API)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print('Bot stopped')
        return


if __name__ == '__main__':
    asyncio.run(main())
