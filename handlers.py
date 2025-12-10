"""Обработчики команд Telegram бота"""

import random
import aiohttp
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from utils import (
    get_user_info, get_quote_of_the_day, get_cat_photo_by_breed,
    get_simple_cat_photo, get_breed_name, get_weather,
    get_main_keyboard, CAT_BREEDS, generate_cat_avatar
)

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)

async def wake_up(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Обработка команды /start с обработкой ошибок"""
    try:
        user_info = get_user_info(update)
        user_id = user_info[3]  # user_id теперь на 3-й позиции
        logger.info(f"Пользователь {user_id} запустил бота командой /start")
        
        await update.message.reply_text(
            text=f'Привет {user_info[2]}, спасибо, что присоединился!', 
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        await update.message.reply_text(
            text='Привет! Добро пожаловать!', 
            reply_markup=get_main_keyboard()
        )

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /quote"""
    logger.info(f"Пользователь {update.effective_user.id} запросил цитату дня")
    await send_quote_of_the_day(update, context)

async def send_quote_of_the_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка цитаты дня пользователю с обработкой ошибок"""
    try:
        temp_message = await update.message.reply_text("Ищу цитату дня...")
        quote_data = await get_quote_of_the_day()
        final_message = f"Цитата дня:\n\n«{quote_data['quote']}»\n— {quote_data['author']}"
        await temp_message.delete()
        await update.message.reply_text(final_message)
        logger.info(f"Цитата отправлена пользователю {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке цитаты: {e}")
        await update.message.reply_text("Не удалось загрузить цитату. Попробуйте позже.")

async def show_breed_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ меню выбора породы котика с обработкой ошибок"""
    try:
        breed_buttons = []
        breeds_list = list(CAT_BREEDS.items())
        
        for i in range(0, len(breeds_list), 2):
            row = []
            if i < len(breeds_list):
                row.append(breeds_list[i][1])
            if i + 1 < len(breeds_list):
                row.append(breeds_list[i + 1][1])
            breed_buttons.append(row)
        
        breed_buttons.append(['Назад'])
        
        breed_keyboard = ReplyKeyboardMarkup(breed_buttons, resize_keyboard=True)
        
        await update.message.reply_text(
            "Выберите породу кошки:",
            reply_markup=breed_keyboard
        )
        logger.info(f"Пользователь {update.effective_user.id} выбрал меню пород котиков")
    except Exception as e:
        logger.error(f"Ошибка при показе меню выбора породы: {e}")
        await update.message.reply_text("Не удалось показать меню выбора породы")

async def send_cat_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, breed_id: str = None):
    """Отправка фото котика пользователю с обработкой ошибок"""
    try:
        user_info = get_user_info(update)
        user_name = user_info[1]
        user_id = user_info[3]  # user_id теперь на 3-й позиции
        
        if breed_id is None:
            breeds = [b for b in CAT_BREEDS.keys() if b != 'random']
            breed_id = random.choice(breeds)
        
        logger.info(f"Пользователь {user_id} запросил фото котика породы {breed_id}")
        searching_message = await update.message.reply_text("Ищем самого милого котика для вас...")
        cat_photo, actual_breed_id = await get_cat_photo_by_breed(breed_id)
        
        if cat_photo:
            await searching_message.delete()
            breed_name = get_breed_name(actual_breed_id)
            await update.message.reply_photo(
                photo=cat_photo,
                caption=f"Вот специально для тебя, {user_name}! 🐱\nПорода: {breed_name}"
            )
            logger.info(f"Фото котика породы {actual_breed_id} отправлено пользователю {user_id}")
        else:
            await searching_message.edit_text("Не удалось найти котика. Попробуйте позже!")
            logger.warning(f"Не удалось найти фото котика для пользователя {user_id}")
            
    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при отправке фото котика: {e}")
        await update.message.reply_text("Проблемы с подключением к серверу котиков")
    except Exception as e:
        logger.error(f"Ошибка при отправке фото котика: {e}")
        await update.message.reply_text("Произошла ошибка при поиске котика")

async def send_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка сгенерированного аватара-котика с обработкой ошибок"""
    try:
        user = update.effective_user
        user_id = user.id
        user_name = user.first_name or "Пользователь"
        username = user.username or ""
        
        logger.info(f"Пользователь {user_id} запросил аватар-котика")
        
        # Генерируем URL для аватара-котика
        avatar_url = generate_cat_avatar(user_id, username)
        
        # Отправляем аватар-котика пользователю
        await update.message.reply_photo(
            photo=avatar_url,
            caption=f"Ваш уникальный аватар-котик, {user_name}! 🐱\nСгенерирован на основе вашего ID: {user_id}"
        )
        
        logger.info(f"Аватар-котик отправлен пользователю {user_id}")
    except aiohttp.ClientError as e:
        logger.warning(f"Ошибка сети при отправке аватара-котика: {e}")
        await update.message.reply_text("Проблемы с подключением к серверу аватаров-котиков")
    except Exception as e:
        logger.error(f"Ошибка при отправке аватара-котика: {e}")
        await update.message.reply_text("Не удалось сгенерировать аватар-котика")

async def say_hi(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Обработка всех текстовых сообщений с обработкой ошибок"""
    try:
        user_info = get_user_info(update) 
        user_id = user_info[3]  # user_id теперь на 3-й позиции
        text = update.message.text
        
        logger.info(f"Пользователь {user_id} отправил текст: '{text}'")
        
        if text == 'Назад':
            await update.message.reply_text(
                "Возвращаюсь в главное меню...",
                reply_markup=get_main_keyboard()
            )
            return
        
        elif text == 'Сгенерировать аватар-котика':
            await send_avatar(update, context)
        elif text == 'Мой ID': 
            await update.message.reply_text(text=f'Твой ID: {user_info[3]}')  # user_id теперь на 3-й позиции
        elif text == 'Прогноз погоды': 
            await request_location(update, context)
        elif text == 'Цитата дня':
            await send_quote_of_the_day(update, context)
        elif text == 'Фото котика':
            await show_breed_selection(update, context)
        elif text in CAT_BREEDS.values():
            breed_id = None
            for breed_key, breed_name in CAT_BREEDS.items():
                if breed_name == text:
                    breed_id = breed_key
                    break
            await send_cat_photo(update, context, breed_id if breed_id else None)
        else: 
            await update.message.reply_text(text=f'{user_info[1]}, как твои дела?')
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")
        await update.message.reply_text("Произошла ошибка обработки команды")

async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Запрос местоположения у пользователя с обработкой ошибок"""
    try:
        user_id = update.effective_user.id
        logger.info(f"Пользователь {user_id} запросил прогноз погоды")
        
        location_keyboard = ReplyKeyboardMarkup( 
            [[KeyboardButton('Отправить координаты', request_location=True)]], 
            resize_keyboard=True,
            one_time_keyboard=True
        ) 
        await update.message.reply_text(
            text='Пожалуйста, поделитесь своей геолокацией для получения прогноза погоды:',
            reply_markup=location_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе местоположения: {e}")
        await update.message.reply_text("Не удалось запросить местоположение")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка полученного местоположения с обработкой ошибок"""
    try:
        user_id = update.effective_user.id
        location = update.message.location
        if not location:
            logger.warning(f"Пользователь {user_id} не предоставил местоположение")
            await update.message.reply_text("Не удалось получить координаты", reply_markup=get_main_keyboard())
            return
            
        latitude = location.latitude 
        longitude = location.longitude 
        context.user_data['location'] = (latitude, longitude)
        
        logger.info(f"Пользователь {user_id} отправил координаты: {latitude}, {longitude}")
        weather_info = await get_weather(latitude, longitude)
        
        await update.message.reply_text(weather_info, reply_markup=get_main_keyboard())
        logger.info(f"Погода отправлена пользователю {user_id}")
    except AttributeError as e:
        logger.error(f"Неверный формат местоположения: {e}")
        await update.message.reply_text("Неверный формат местоположения", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при обработке местоположения: {e}")
        await update.message.reply_text("Ошибка обработки местоположения", reply_markup=get_main_keyboard())