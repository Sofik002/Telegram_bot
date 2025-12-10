"""Запуск и настройка Telegram бота"""

import os
import asyncio
import logging
from telegram.ext import Application, MessageHandler, CommandHandler, filters

from utils import TOKEN
from handlers import (
    wake_up, say_hi, handle_location, 
    quote_command, request_location
)

# Создаем логгер для этого модуля
logger = logging.getLogger(__name__)

def run_bot():
    """Главная функция запуска бота с обработкой критических ошибок"""
    try:
        # Для Windows систем
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        logger.info("Запуск бота...")
        
        # Создание приложения бота
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация обработчиков команд
        application.add_handler(CommandHandler('start', wake_up))
        application.add_handler(CommandHandler('quote', quote_command))
        application.add_handler(MessageHandler(filters.TEXT, say_hi)) 
        application.add_handler(MessageHandler(filters.LOCATION, handle_location)) 
        
        # Запуск бота
        logger.info("Бот успешно запущен и готов к работе!")
        print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
        
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка при запуске бота: {e}")