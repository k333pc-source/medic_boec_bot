from aiogram import types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime

from database import Database
from keyboards import (
    get_welcome_keyboard, get_main_menu, get_section_menu, 
    get_content_menu, get_favorites_keyboard, get_stats_keyboard
)
from messages import (
    format_welcome_message, format_section_card, 
    format_user_stats, format_detailed_stats, format_about_message
)

db = Database()

async def setup_handlers(dp, ADMIN_IDS, UserStates):
    """Настройка всех обработчиков"""
    
    # --- ОБРАБОТЧИКИ КОМАНД ---
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        # Обновляем статистику
        db.update_user_stats(user_id)
        
        # Проверяем админские права
        is_admin = user_id in ADMIN_IDS
        
        # Отправляем приветствие с красивой клавиатурой
        await message.answer(
            format_welcome_message(user_name, is_admin),
            reply_markup=get_welcome_keyboard()
        )
    
    # --- ОБРАБОТЧИКИ ТЕКСТОВЫХ КНОПОК ---
    @dp.message(F.text == "🚀 Начать работу")
    async def handle_start_work(message: types.Message):
        """Кнопка 'Начать работу'"""
        user_id = message.from_user.id
        
        await message.answer(
            "<b>📖 ОТКРЫТЬ СПРАВОЧНИК</b>\n\n"
            "Выберите раздел для изучения:",
            reply_markup=get_main_menu(user_id, ADMIN_IDS)
        )
    
    @dp.message(F.text == "📚 Открыть справочник")
    async def handle_open_handbook(message: types.Message):
        """Кнопка 'Открыть справочник'"""
        user_id = message.from_user.id
        
        await message.answer(
            "<b>📚 СПРАВОЧНИК ТАКТИЧЕСКОЙ МЕДИЦИНЫ</b>\n\n"
            "Все материалы структурированы по разделам:",
            reply_markup=get_main_menu(user_id, ADMIN_IDS)
        )
    
    @dp.message(F.text == "⭐ Избранное")
    async def handle_favorites(message: types.Message):
        """Кнопка 'Избранное'"""
        user_id = message.from_user.id
        favorites = db.get_favorites(user_id)
        
        if not favorites:
            await message.answer(
                "⭐ <b>ВАШЕ ИЗБРАННОЕ</b>\n\n"
                "Пока здесь пусто. Добавляйте разделы в избранное, "
                "нажимая на звездочку ★ в меню раздела."
            )
            return
        
        await message.answer(
            f"⭐ <b>ВАШЕ ИЗБРАННОЕ</b>\n\n"
            f"Найдено разделов: <b>{len(favorites)}</b>\n"
            f"Быстрый доступ к сохраненным материалам:",
            reply_markup=get_favorites_keyboard(favorites, ADMIN_IDS)
        )
    
    @dp.message(F.text == "🔍 Поиск")
    async def handle_search(message: types.Message, state: FSMContext):
        """Кнопка 'Поиск'"""
        await message.answer(
            "🔍 <b>ПОИСК ПО СПРАВОЧНИКУ</b>\n\n"
            "Введите поисковый запрос:\n"
            "<i>Например: кровотечение, пневмоторакс, алгоритм</i>",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await state.set_state(UserStates.search_query)
    
    @dp.message(F.text == "📥 Офлайн-версия")
    async def handle_offline(message: types.Message):
        """Кнопка 'Офлайн-версия'"""
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="📱 Скачать на телефон", callback_data="download_mobile"),
                types.InlineKeyboardButton(text="💻 Версия для ПК", callback_data="download_pc"),
            ],
            [types.InlineKeyboardButton(text="📖 Инструкция", callback_data="offline_help")]
        ])
        
        await message.answer(
            "📥 <b>ОФЛАЙН-ВЕРСИЯ СПРАВОЧНИКА</b>\n\n"
            "Скачайте полную версию для работы без интернета:\n\n"
            "✅ <b>Все текстовые материалы</b>\n"
            "✅ <b>Структура разделов</b>\n"
            "✅ <b>HTML-версия для браузера</b>\n"
            "✅ <b>PDF-экспорт (скоро)</b>\n\n"
            "<i>Выберите вариант загрузки:</i>",
            reply_markup=keyboard
        )
    
    @dp.message(F.text == "ℹ️ О боте")
    async def handle_about(message: types.Message):
        """Кнопка 'О боте'"""
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="📞 Связь", callback_data="contact"),
                types.InlineKeyboardButton(text="🔄 Обновления", callback_data="updates"),
            ],
            [types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats")]
        ])
        
        await message.answer(
            format_about_message(),
            reply_markup=keyboard
        )
    
    # --- ОБРАБОТЧИКИ CALLBACK ---
    @dp.callback_query(F.data == "back_to_main")
    async def handle_back_to_main(callback: types.CallbackQuery):
        """Возврат в главное меню"""
        await callback.message.edit_text(
            "<b>📚 ГЛАВНОЕ МЕНЮ СПРАВОЧНИКА</b>\n\n"
            "Выберите раздел для изучения:",
            reply_markup=get_main_menu(callback.from_user.id, ADMIN_IDS)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("view_section_"))
    async def handle_view_section(callback: types.CallbackQuery):
        """Просмотр раздела"""
        section_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        section = db.get_section(section_id)
        if not section:
            await callback.answer("❌ Раздел не найден")
            return
        
        # Обновляем статистику
        db.update_user_stats(user_id, section_viewed=True)
        
        # Проверяем, в избранном ли
        favorites = db.get_favorites(user_id)
        fav_ids = [f['id'] for f in favorites]
        
        await callback.message.edit_text(
            format_section_card(section),
            reply_markup=get_section_menu(section_id, user_id, ADMIN_IDS, section_id in fav_ids)
        )
        await callback.answer("📂 Раздел открыт")
    
    @dp.callback_query(F.data.startswith("view_content_"))
    async def handle_view_content(callback: types.CallbackQuery):
        """Просмотр контента"""
        content_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        item = db.get_content_with_section(content_id)
        
        if not item:
            await callback.answer("❌ Материал не найден")
            return
        
        # Обновляем статистику
        db.update_user_stats(user_id, content_viewed=True)
        
        if item['content_type'] == 'text':
            content_text = f"""
<b>📖 {item['button_text'] or 'МАТЕРИАЛ'}</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

{item['text_content']}

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<i>ID материала: {item['id']}</i>
            """
            
            await callback.message.edit_text(
                content_text.strip(),
                reply_markup=get_content_menu(content_id, item['section_id'], user_id, ADMIN_IDS)
            )
        
        await callback.answer("📄 Материал открыт")
    
    @dp.callback_query(F.data.startswith("toggle_fav_"))
    async def handle_toggle_favorite(callback: types.CallbackQuery):
        """Добавление/удаление из избранного"""
        user_id = callback.from_user.id
        section_id = int(callback.data.split("_")[2])
        
        is_added = db.toggle_favorite(user_id, section_id)
        
        if is_added:
            await callback.answer("✅ Добавлено в избранное")
        else:
            await callback.answer("❌ Удалено из избранного")
        
        # Обновляем меню раздела
        favorites = db.get_favorites(user_id)
        fav_ids = [f['id'] for f in favorites]
        
        await callback.message.edit_reply_markup(
            reply_markup=get_section_menu(section_id, user_id, ADMIN_IDS, section_id in fav_ids)
        )
    
    @dp.callback_query(F.data == "favorites")
    async def handle_show_favorites(callback: types.CallbackQuery):
        """Показать избранное через callback"""
        user_id = callback.from_user.id
        favorites = db.get_favorites(user_id)
        
        if not favorites:
            await callback.message.edit_text(
                "⭐ <b>ВАШЕ ИЗБРАННОЕ</b>\n\n"
                "Пока здесь пусто. Добавляйте разделы в избранное, "
                "нажимая на звездочку ★ в меню раздела.",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")
                ]])
            )
            return
        
        await callback.message.edit_text(
            f"⭐ <b>ВАШЕ ИЗБРАННОЕ</b>\n\n"
            f"Найдено разделов: <b>{len(favorites)}</b>\n"
            f"Быстрый доступ к сохраненным материалам:",
            reply_markup=get_favorites_keyboard(favorites, ADMIN_IDS)
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "stats")
    async def handle_stats(callback: types.CallbackQuery):
        """Показать статистику"""
        user_id = callback.from_user.id
        
        # Проверяем, админ ли
        is_admin = user_id in ADMIN_IDS
        
        if is_admin:
            # Полная статистика для администратора
            stats = db.get_admin_stats()
            stats['user_favorites'] = len(db.get_favorites(user_id))
            stats_text = format_user_stats(stats, is_admin=True)
        else:
            # Простая статистика для обычного пользователя
            sections = db.get_sections()
            total_sections = len(sections)
            
            total_content = 0
            for section in sections:
                content = db.get_section_content(section['id'])
                total_content += len(content)
            
            favorites = db.get_favorites(user_id)
            user_favorites = len(favorites)
            
            stats_text = format_user_stats({
                'total_sections': total_sections,
                'total_content': total_content,
                'user_favorites': user_favorites
            }, is_admin=False)
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_stats_keyboard(is_admin)
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "detailed_stats")
    async def handle_detailed_stats(callback: types.CallbackQuery):
        """Детальная статистика для администратора"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        stats = db.get_admin_stats()
        detailed_text = format_detailed_stats(stats)
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats"),
                types.InlineKeyboardButton(text="🔄 Обновить", callback_data="detailed_stats"),
            ],
            [types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")]
        ])
        
        await callback.message.edit_text(
            detailed_text,
            reply_markup=keyboard
        )
        await callback.answer()
    
    # --- ПОИСК ---
    @dp.message(UserStates.search_query)
    async def process_search_query(message: types.Message, state: FSMContext):
        """Обработка поискового запроса"""
        query = message.text.strip().lower()
        
        if len(query) < 2:
            await message.answer(
                "❌ Слишком короткий запрос. Введите минимум 2 символа.",
                reply_markup=get_welcome_keyboard()
            )
            await state.clear()
            return
        
        # Простой поиск по разделам
        sections = db.get_sections()
        found_sections = []
        
        for section in sections:
            if (query in section['title'].lower() or 
                (section['description'] and query in section['description'].lower())):
                found_sections.append(section)
        
        if not found_sections:
            await message.answer(
                f"🔍 <b>ПОИСК: '{query}'</b>\n\n"
                "Ничего не найдено. Попробуйте другие ключевые слова.",
                reply_markup=get_welcome_keyboard()
            )
            await state.clear()
            return
        
        # Формируем результаты
        result_text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА: '{query}'</b>\n\n"
        result_text += f"<b>📁 Найдено разделов:</b> {len(found_sections)}\n\n"
        
        for i, section in enumerate(found_sections[:5], 1):
            result_text += f"{i}. {section['title']}\n"
            if section['description']:
                result_text += f"   <i>{section['description'][:100]}...</i>\n"
            result_text += "\n"
        
        keyboard = types.InlineKeyboardBuilder()
        
        for section in found_sections[:5]:
            emoji = section.get('icon', '📄')
            keyboard.row(types.InlineKeyboardButton(
                text=f"{emoji} {section['title'][:30]}...",
                callback_data=f"view_section_{section['id']}"
            ))
        
        keyboard.row(types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main"))
        
        await message.answer(
            result_text,
            reply_markup=keyboard.as_markup()
        )
        
        await state.clear()
    
    # --- ПРОСТЫЕ КНОПКИ ---
    @dp.callback_query(F.data == "table_of_contents")
    async def handle_table_of_contents(callback: types.CallbackQuery):
        """Оглавление справочника"""
        sections = db.get_sections()
        
        contents = "<b>📖 ОГЛАВЛЕНИЕ СПРАВОЧНИКА</b>\n<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>\n\n"
        
        for i, section in enumerate(sections, 1):
            emoji = section.get('icon', '📄')
            contents += f"<b>{i}. {emoji} {section['title']}</b>\n"
            
            if section.get('description'):
                contents += f"<i>   {section['description']}</i>\n"
            
            contents += "\n"
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")
        ]])
        
        await callback.message.edit_text(
            contents,
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query(F.data.in_(["download_mobile", "download_pc", "offline_help", "contact", "updates"]))
    async def handle_simple_buttons(callback: types.CallbackQuery):
        """Обработка простых кнопок"""
        button = callback.data
        
        if button == "download_mobile":
            text = "📱 <b>СКАЧАТЬ НА ТЕЛЕФОН</b>\n\nФункция в разработке..."
        elif button == "download_pc":
            text = "💻 <b>ВЕРСИЯ ДЛЯ ПК</b>\n\nФункция в разработке..."
        elif button == "offline_help":
            text = "📖 <b>ИНСТРУКЦИЯ ПО ОФЛАЙН-ИСПОЛЬЗОВАНИЮ</b>\n\nФункция в разработке..."
        elif button == "contact":
            text = "📞 <b>СВЯЗЬ С РАЗРАБОТЧИКОМ</b>\n\nФункция в разработке..."
        elif button == "updates":
            text = "🔄 <b>ОБНОВЛЕНИЯ</b>\n\nФункция в разработке..."
        else:
            text = "Функция в разработке..."
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")
        ]])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "recent")
    async def handle_recent(callback: types.CallbackQuery):
        """Недавние материалы"""
        await callback.message.edit_text(
            "🔄 <b>НЕДАВНИЕ МАТЕРИАЛЫ</b>\n\n"
            "Функция отслеживания недавно просмотренных материалов "
            "будет добавлена в следующем обновлении.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")
            ]])
        )
        await callback.answer()