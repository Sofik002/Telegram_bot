import os
import asyncio
import random
import hashlib
import aiohttp
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TOKEN')
TOKEN_WEATHER = os.getenv('TOKEN_WEATHER')

PROXY_URL = "http://proxy.server:3128"
USE_PROXY = True

if not TOKEN:
    logger.error("Не найден TOKEN в файле .env")
    exit(1)

CAT_BREEDS = {
    'beng': 'Бенгальская',
    'siam': 'Сиамская',
    'pers': 'Персидская',
    'mcoo': 'Мейн-кун',
    'rblu': 'Русская голубая',
    'sibe': 'Сибирская',
    'ragd': 'Рэгдолл',
    'birm': 'Бирманская',
    'random': 'Случайная порода'
}

async def get_quote_of_the_day():
    url = 'https://api.forismatic.com/api/1.0/'
    params = {'method': 'getQuote', 'format': 'json', 'lang': 'ru'}

    try:
        async with aiohttp.ClientSession() as session:
            proxy = PROXY_URL if USE_PROXY else None
            async with session.get(url, params=params, proxy=proxy, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get('quoteText', 'Цитата не найдена.').strip()
                    author = data.get('quoteAuthor', 'Неизвестный автор').strip()
                    logger.info("Цитата успешно получена")
                    return {"quote": quote, "author": author}
    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при получении цитаты: {e}")
        return {"quote": "Не удалось загрузить цитату (проблемы с сетью).", "author": "API"}
    except asyncio.TimeoutError:
        logger.warning("Таймаут при получении цитаты")
        return {"quote": "Не удалось загрузить цитату (таймаут).", "author": "API"}
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении цитаты: {e}")
        return {"quote": "Не удалось загрузить цитату.", "author": "API"}

def get_user_info(update):
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user
        user_id = user.id
        message = update.effective_message
        timestamp = int(message.date.timestamp())
        first_name = user.first_name or ''
        last_name = user.last_name or ''
        full_name = f'{first_name} {last_name}'.strip()

        logger.debug(f"Получена информация для пользователя {user_id}")
        return chat_id, first_name, full_name, user_id
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        return None, "Пользователь", "Пользователь", 0

def generate_cat_avatar(user_id: int, username: str = "") -> str:
    try:
        user_data = f"{username}{user_id}{random.randint(1000, 9999)}"
        hash_object = hashlib.md5(user_data.encode())
        hash_str = hash_object.hexdigest()[:10]

        bg_options = ['bg1', 'bg2', 'transparent']
        selected_bg = random.choice(bg_options)

        avatar_url = f'https://robohash.org/{hash_str}.png?set=set4&bgset={selected_bg}&size=400x400'

        logger.debug(f"Сгенерирован аватар-котик для пользователя {user_id}")
        return avatar_url
    except Exception as e:
        logger.error(f"Ошибка при генерации аватара-котика: {e}")
        return "https://robohash.org/error.png?set=set4&bgset=bg1&size=400x400"

def get_breed_name(breed_id):
    return CAT_BREEDS.get(breed_id, 'Неизвестная порода')

async def get_cat_photo_by_breed(breed_id: str):
    try:
        if breed_id == 'random':
            breeds = [b for b in CAT_BREEDS.keys() if b != 'random']
            selected_breed = random.choice(breeds)
        else:
            selected_breed = breed_id

        url = f"https://api.thecatapi.com/v1/images/search?breed_ids={selected_breed}"
        logger.debug(f"Запрос фото котика породы: {selected_breed}")

        async with aiohttp.ClientSession() as session:
            proxy = PROXY_URL if USE_PROXY else None
            async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        cat_image_url = data[0]['url']
                        async with session.get(cat_image_url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as img_response:
                            if img_response.status == 200:
                                image_data = await img_response.read()
                                logger.info(f"Успешно получено фото котика породы {selected_breed}")
                                return image_data, selected_breed

        logger.warning(f"Не удалось получить фото породы {selected_breed}, пробую общий запрос")
        return await get_simple_cat_photo()

    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при получении фото котика: {e}")
        return await get_simple_cat_photo()
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении фото котика: {e}")
        return await get_simple_cat_photo()

async def get_simple_cat_photo():
    try:
        url = "https://api.thecatapi.com/v1/images/search"
        async with aiohttp.ClientSession() as session:
            proxy = PROXY_URL if USE_PROXY else None
            async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    cat_image_url = data[0]['url']
                    async with session.get(cat_image_url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as img_response:
                        if img_response.status == 200:
                            image_data = await img_response.read()
                            logger.info("Успешно получено случайное фото котика")
                            return image_data, "random"
    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при получении случайного фото котика: {e}")
        return None, "unknown"
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении случайного фото котика: {e}")
        return None, "unknown"

async def get_weather(lat: float, lon: float) -> str:
    if not TOKEN_WEATHER:
        logger.warning("Токен для погодного API не настроен")
        return "Токен для погодного API не настроен"

    url = f'https://api.openweathermap.org/data/2.5/weather?APPID={TOKEN_WEATHER}&lang=ru&units=metric&lat={lat}&lon={lon}'

    try:
        logger.debug(f"Запрос погоды для координат: {lat}, {lon}")
        async with aiohttp.ClientSession() as session:
            proxy = PROXY_URL if USE_PROXY else None
            async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.warning(f"Ошибка API погоды, статус: {resp.status}")
                    return 'Ошибка при получении данных о погоде'
                data = await resp.json()
                logger.info(f"Успешно получена погода для {data.get('name', 'неизвестного места')}")
    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при получении погоды: {e}")
        return 'Ошибка подключения к серверу погоды'
    except asyncio.TimeoutError:
        logger.warning("Таймаут при получении погоды")
        return 'Сервер погоды не отвежает'
    except Exception as e:
        logger.error(f"Неизвестная ошибка при получении погоды: {e}")
        return 'Неизвестная ошибка при получении погоды'

    try:
        city = data.get('name', 'Неизвестное место')
        weather = data['weather'][0]['description']

        temp = int(round(data['main']['temp'], 0))
        feels_like = int(round(data['main']['feels_like'], 0))

        wind_speed = data['wind']['speed']

        if wind_speed < 5:
            wind_recom = 'Погода хорошая, ветра почти нет'
        elif wind_speed < 10:
            wind_recom = 'На улице ветрено, оденьтесь чуть теплее'
        elif wind_speed < 20:
            wind_recom = 'Ветер очень сильный, будьте осторожны, выходя из дома'
        else:
            wind_recom = 'На улице шторм, на улицу лучше не выходить'

        return (
            f'Прогноз погоды:\n'
            f'Описание: {weather}\n'
            f'Температура: {temp}°C (ощущается как {feels_like}°C)\n'
            f'Ветер: {wind_speed} м/с\n'
            f'Рекомендация: {wind_recom}'
        )
    except KeyError as e:
        logger.error(f"Отсутствует ключ в данных о погоде: {e}")
        return 'Данные о погоде повреждены'
    except Exception as e:
        logger.error(f"Ошибка обработки данных о погоде: {e}")
        return 'Ошибка обработки данных о погоде'

def get_main_keyboard():
    try:
        from telegram import ReplyKeyboardMarkup
        return ReplyKeyboardMarkup([
            ['Фото котика', 'Сгенерировать аватар-котика'],
            ['Цитата дня', 'Мой ID'],
            ['Прогноз погоды']
        ], resize_keyboard=True)
    except Exception as e:
        logger.error(f"Ошибка при создании клавиатуры: {e}")
        from telegram import ReplyKeyboardMarkup
        return ReplyKeyboardMarkup([['Фото котика'], ['Прогноз погоды']], resize_keyboard=True)