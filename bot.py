import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database import Database
import handlers
import admin_handlers

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8518838603:AAEL9kM5eeiQDnf_NWFhigAQV6HICNc7Leg'  # Токен от @BotFather
ADMIN_IDS = [5856589785]  # Только цифры, например: [123456789]

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание бота
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode='HTML')
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- FSM СОСТОЯНИЯ ---
class UserStates(StatesGroup):
    waiting_for_section_title = State()
    waiting_for_section_description = State()
    waiting_for_content_text = State()
    waiting_for_content_button = State()
    editing_section = State()
    editing_content = State()
    search_query = State()

# --- НАСТРОЙКА КОМАНД БОТА ---
async def set_bot_commands():
    """Установка команд меню бота"""
    from aiogram.types import BotCommand
    
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="help", description="❓ Помощь по использованию"),
        BotCommand(command="menu", description="📚 Открыть справочник"),
        BotCommand(command="favorites", description="⭐ Избранное"),
        BotCommand(command="search", description="🔍 Поиск по справочнику"),
        BotCommand(command="stats", description="📊 Статистика"),
        BotCommand(command="admin", description="👑 Админ-панель"),
    ]
    
    await bot.set_my_commands(commands)

# --- ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА ---
async def main():
    """Основная функция запуска"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ТАКТИЧЕСКОГО МЕДИКА")
    logger.info(f"✨ Админов: {len(ADMIN_IDS)}")
    logger.info("=" * 60)
    
    # Устанавливаем команды меню (можно закомментировать при проблемах с сетью)
    try:
        await set_bot_commands()
        logger.info("✅ Команды бота установлены")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось установить команды: {e}")
        logger.info("Бот будет работать, но команды меню могут не отображаться")
    
    # Проверяем конфигурацию
    if API_TOKEN != '8518838603:AAEL9kM5eeiQDnf_NWFhigAQV6HICNc7Leg':
        print("\n" + "❌" * 30)
        print("КРИТИЧЕСКАЯ ОШИБКА: Не установлен токен бота!")
        print("Замените 'ВАШ_ТОКЕН_ЗДЕСЬ' на ваш токен от @BotFather")
        print("❌" * 30)
        return
    
    if ADMIN_IDS != [5856589785]:
        print("\n" + "⚠️" * 30)
        print("ПРЕДУПРЕЖДЕНИЕ: Не установлен ID администратора!")
        print("Замените 'ВАШ_ID_ЗДЕСЬ' на ваш Telegram ID")
        print("⚠️" * 30)
    
    # Создаем необходимые папки
    os.makedirs("data", exist_ok=True)
    
    # Настраиваем обработчики
    await handlers.setup_handlers(dp, ADMIN_IDS, UserStates)
    await admin_handlers.setup_admin_handlers(dp, ADMIN_IDS, UserStates)
    
    print("\n" + "✅" * 30)
    print("Бот успешно запущен!")
    print("Теперь можно открыть Telegram и написать боту:")
    print("1. /start - для запуска")
    print("2. Нажать '🚀 Начать работу'")
    print("3. Или '📚 Открыть справочник'")
    print("✅" * 30 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
        print("\n🛑 Бот остановлен (Ctrl+C)")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("\n" + "🔧" * 30)
        print("ВОЗМОЖНЫЕ ПРИЧИНЫ:")
        print("1. Проблемы с интернет-соединением")
        print("2. Неправильный токен бота")
        print("3. Telegram API временно недоступен")
        print("🔧" * 30)

if __name__ == '__main__':
    # Замените токен и ID перед запуском!
    if API_TOKEN == 'ВАШ_ТОКЕН_ЗДЕСЬ':
        print("\n⚠️ Замените API_TOKEN и ADMIN_IDS в коде на ваши значения!")
        print("1. Получите токен у @BotFather")
        print("2. Узнайте свой ID у @userinfobot")
        print("3. Замените строки 14-15 в bot.py")
    else:
        asyncio.run(main())
