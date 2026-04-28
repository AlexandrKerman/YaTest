import asyncio
import re
from os import getenv

import yandex_music as ym
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
TG_API = getenv('TG_API')
PROXY_URL = 'socks5://127.0.0.1:9150'
dp = Dispatcher()


@dp.message(Command('start'))
async def start(message: types.Message):
    start_message = ('Приветствую! Отправь мне ссылку на трек и получи информацию о нём:\n'
                     '1. Название\n'
                     '2. Исполнитель\n'
                     '3. Длительность')
    await message.answer(text=start_message)


def parse_message_for_track(url: str) -> int | None:
    pattern = re.compile(r'/track/(\d+)')
    match = pattern.search(url)
    if not match:
        return None
    track_id = int(match.group(1))
    return track_id


async def get_track_info(client, /, track_id) -> dict | None:
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
    minutes = seconds // 60
    seconds = seconds % 60
    return f'{minutes:02d}:{seconds:02d}'


@dp.message(F.text.contains('/track'))
async def track_id_handle(message: types.Message) -> None:
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
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=TG_API, session=session)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
