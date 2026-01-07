from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from database import Database
from keyboards import (
    get_admin_custom_icons_keyboard, get_admin_icons_keyboard,
    get_section_menu, get_main_menu
)

db = Database()

async def setup_admin_handlers(dp, ADMIN_IDS, UserStates):
    """Настройка админских обработчиков"""
    
    # --- СОЗДАНИЕ РАЗДЕЛОВ ---
    # Для корневого раздела
    @dp.callback_query(F.data == "admin_add_section_root")
    async def handle_admin_add_root_section(callback: types.CallbackQuery, state: FSMContext):
        """Создание корневого раздела"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        await state.update_data(
            parent_id=None,
            parent_title="главное меню",
            user_id=user_id,
            step="title"
        )
        
        await state.set_state(UserStates.waiting_for_section_title)
        
        await callback.message.edit_text(
            f"👑 <b>СОЗДАНИЕ НОВОГО РАЗДЕЛА</b>\n\n"
            f"📍 <b>Родитель:</b> главное меню\n"
            f"📝 <b>Шаг 1 из 3</b>\n\n"
            f"Введите название нового раздела:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")
            ]])
        )
        await callback.answer()

    # Для подразделов
    @dp.callback_query(F.data.startswith("admin_add_subsection_"))
    async def handle_admin_add_subsection(callback: types.CallbackQuery, state: FSMContext):
        """Создание подраздела"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        # Извлекаем ID родительского раздела
        try:
            parent_id = int(callback.data.split("_")[3])
        except (IndexError, ValueError):
            await callback.answer("❌ Ошибка в данных")
            return
        
        parent_section = db.get_section(parent_id)
        if not parent_section:
            await callback.answer("❌ Родительский раздел не найден")
            return
        
        await state.update_data(
            parent_id=parent_id,
            parent_title=parent_section['title'],
            user_id=user_id,
            step="title"
        )
        
        await state.set_state(UserStates.waiting_for_section_title)
        
        await callback.message.edit_text(
            f"👑 <b>СОЗДАНИЕ ПОДРАЗДЕЛА</b>\n\n"
            f"📍 <b>Родитель:</b> {parent_section['title']}\n"
            f"📝 <b>Шаг 1 из 3</b>\n\n"
            f"Введите название нового подраздела:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_section_{parent_id}")
            ]])
        )
        await callback.answer()
    
    @dp.message(UserStates.waiting_for_section_title)
    async def process_section_title_enhanced(message: types.Message, state: FSMContext):
        """Обработка названия с выбором иконки"""
        data = await state.get_data()
        
        if len(message.text) > 100:
            await message.answer("❌ Слишком длинное название. Максимум 100 символов.")
            return
        
        await state.update_data(title=message.text)
        
        # Предлагаем выбрать иконку из кастомных
        await message.answer(
            f"✅ <b>Название сохранено:</b> {message.text}\n\n"
            f"📝 <b>Шаг 2 из 3</b>\n\n"
            f"Теперь выберите иконку для раздела:",
            reply_markup=get_admin_custom_icons_keyboard()
        )
    
    @dp.callback_query(F.data.startswith("icon_"))
    async def handle_icon_selection(callback: types.CallbackQuery, state: FSMContext):
        """Выбор иконки для раздела (стандартные)"""
        icon = callback.data.split("_")[1]
        
        if icon == "none":
            icon = "📄"
        
        await state.update_data(icon=icon)
        await state.set_state(UserStates.waiting_for_section_description)
        
        data = await state.get_data()
        title = data.get('title', 'Без названия')
        
        await callback.message.edit_text(
            f"✅ <b>Иконка выбрана:</b> {icon}\n\n"
            f"📝 <b>Шаг 3 из 3</b>\n\n"
            f"Раздел: <b>{icon} {title}</b>\n\n"
            f"Теперь введите описание раздела "
            f"(можно пропустить, отправив '-'):",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")
            ]])
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("custom_icon_"))
    async def handle_custom_icon_selection(callback: types.CallbackQuery, state: FSMContext):
        """Выбор кастомной иконки"""
        icon = callback.data.split("_")[2]  # custom_icon_🩸
        
        await state.update_data(icon=icon)
        await state.set_state(UserStates.waiting_for_section_description)
        
        data = await state.get_data()
        title = data.get('title', 'Без названия')
        
        await callback.message.edit_text(
            f"✅ <b>Кастомная иконка выбрана:</b> {icon}\n\n"
            f"📝 <b>Шаг 3 из 3</b>\n\n"
            f"Раздел: <b>{icon} {title}</b>\n\n"
            f"Теперь введите описание раздела "
            f"(можно пропустить, отправив '-'):",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main")
            ]])
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "show_standard_icons")
    async def handle_show_standard_icons(callback: types.CallbackQuery, state: FSMContext):
        """Показать стандартные иконки"""
        data = await state.get_data()
        title = data.get('title', 'Без названия')
        
        await callback.message.edit_text(
            f"📝 <b>Шаг 2 из 3</b>\n\n"
            f"Раздел: {title}\n\n"
            f"Выберите стандартную иконку:",
            reply_markup=get_admin_icons_keyboard()
        )
        await callback.answer()
    
    @dp.message(UserStates.waiting_for_section_description)
    async def process_section_description(message: types.Message, state: FSMContext):
        """Обработка описания раздела и сохранение"""
        data = await state.get_data()
        
        description = message.text if message.text != '-' else None
        title = data['title']
        parent_id = data['parent_id']
        user_id = data['user_id']
        icon = data.get('icon', '📄')
        
        # Сохраняем раздел в БД
        section_id = db.add_section(title, description, parent_id, user_id, icon)
        
        # Получаем созданный раздел
        section = db.get_section(section_id)
        
        # Формируем сообщение об успехе
        success_text = f"✅ <b>Раздел создан успешно!</b>\n\n"
        success_text += f"📂 <b>Название:</b> {section['title']}\n"
        if section['description']:
            success_text += f"📝 <b>Описание:</b> {section['description']}\n"
        success_text += f"🎨 <b>Иконка:</b> {section.get('icon', '📄')}\n"
        
        if parent_id:
            success_text += f"📍 <b>Родительский раздел:</b> {data['parent_title']}\n"
        
        success_text += f"\nРаздел добавлен в меню."
        
        # Отправляем сообщение
        await message.answer(
            success_text,
            reply_markup=get_section_menu(section_id, user_id, ADMIN_IDS) if parent_id else get_main_menu(user_id, ADMIN_IDS)
        )
        
        # Очищаем состояние
        await state.clear()
    
    # --- ДОБАВЛЕНИЕ КОНТЕНТА ---
    @dp.callback_query(F.data.startswith("admin_add_content_"))
    async def handle_admin_add_content(callback: types.CallbackQuery, state: FSMContext):
        """Добавление контента в раздел"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        section_id = int(callback.data.split("_")[3])
        section = db.get_section(section_id)
        
        if not section:
            await callback.answer("Раздел не найден")
            return
        
        await state.update_data(section_id=section_id, user_id=user_id)
        await state.set_state(UserStates.waiting_for_content_text)
        
        await callback.message.edit_text(
            f"📝 <b>ДОБАВЛЕНИЕ КОНТЕНТА В РАЗДЕЛ:</b> {section['title']}\n\n"
            f"Введите текст контента (поддерживается HTML разметка):",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_section_{section_id}")
            ]])
        )
        await callback.answer()
    
    @dp.message(UserStates.waiting_for_content_text)
    async def process_content_text(message: types.Message, state: FSMContext):
        """Обработка текста контента"""
        data = await state.get_data()
        
        if len(message.text) > 4000:
            await message.answer("❌ Слишком длинный текст. Максимум 4000 символов.")
            return
        
        await state.update_data(text_content=message.text)
        await state.set_state(UserStates.waiting_for_content_button)
        
        await message.answer(
            "Теперь введите текст для кнопки (коротко, что это за контент):",
            reply_markup=ReplyKeyboardRemove()
        )
    
    @dp.message(UserStates.waiting_for_content_button)
    async def process_content_button(message: types.Message, state: FSMContext):
        """Обработка текста кнопки и сохранение контента"""
        data = await state.get_data()
        
        section_id = data['section_id']
        text_content = data['text_content']
        button_text = message.text
        user_id = data['user_id']
        
        # Сохраняем контент в БД
        content_id = db.add_content(section_id, 'text', text_content, button_text, user_id)
        
        await message.answer(
            f"✅ <b>Контент добавлен!</b>\n\n"
            f"📝 <b>Кнопка:</b> {button_text}\n"
            f"📄 <b>Текст добавлен в раздел.</b>",
            reply_markup=get_section_menu(section_id, user_id, ADMIN_IDS)
        )
        
        await state.clear()
    
    # --- УПРОЩЕННЫЕ АДМИНСКИЕ ФУНКЦИИ ---
    @dp.callback_query(F.data.startswith("admin_edit_section_"))
    async def handle_admin_edit_section(callback: types.CallbackQuery):
        """Упрощенное редактирование раздела"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        section_id = int(callback.data.split("_")[3])
        section = db.get_section(section_id)
        
        if not section:
            await callback.answer("Раздел не найден")
            return
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_section_{section_id}")
        ]])
        
        await callback.message.edit_text(
            f"✏️ <b>РЕДАКТИРОВАНИЕ РАЗДЕЛА</b>\n\n"
            f"📂 <b>Раздел:</b> {section['title']}\n\n"
            f"<i>Полное редактирование будет добавлено в следующем обновлении.</i>",
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_add_subsection_"))
    async def handle_admin_add_subsection(callback: types.CallbackQuery, state: FSMContext):
        """Добавление подраздела"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        parent_id = int(callback.data.split("_")[3])
        parent_section = db.get_section(parent_id)
        
        if not parent_section:
            await callback.answer("Родительский раздел не найден")
            return
        
        await state.update_data(parent_id=parent_id, parent_title=parent_section['title'], user_id=user_id)
        await state.set_state(UserStates.waiting_for_section_title)
        
        await callback.message.edit_text(
            f"📝 <b>СОЗДАНИЕ ПОДРАЗДЕЛА</b>\n\n"
            f"📍 <b>Родительский раздел:</b> {parent_section['title']}\n\n"
            f"Введите название нового подраздела:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_section_{parent_id}")
            ]])
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_edit_content_"))
    async def handle_admin_edit_content(callback: types.CallbackQuery):
        """Упрощенное редактирование контента"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        content_id = int(callback.data.split("_")[3])
        
        item = db.get_content_with_section(content_id)
        
        if not item:
            await callback.answer("Контент не найден")
            return
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"view_content_{content_id}")
        ]])
        
        await callback.message.edit_text(
            f"✏️ <b>РЕДАКТИРОВАНИЕ КОНТЕНТА</b>\n\n"
            f"📝 <b>Контент:</b> {item['button_text']}\n\n"
            f"<i>Полное редактирование будет добавлено в следующем обновлении.</i>",
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_delete_content_"))
    async def handle_admin_delete_content(callback: types.CallbackQuery):
        """Удаление контента"""
        user_id = callback.from_user.id
        
        if user_id not in ADMIN_IDS:
            await callback.answer("⛔ Доступ запрещен")
            return
        
        content_id = int(callback.data.split("_")[3])
        
        item = db.get_content_with_section(content_id)
        
        if not item:
            await callback.answer("Контент не найден")
            return
        
        section_id = item['section_id']
        
        # Удаляем контент
        db.delete_content(content_id)
        
        await callback.message.edit_text(
            "✅ Контент удален.",
            reply_markup=get_section_menu(section_id, user_id, ADMIN_IDS)
        )
        
        await callback.answer()
