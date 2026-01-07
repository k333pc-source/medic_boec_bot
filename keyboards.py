from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from database import Database

db = Database()

# --- ОСНОВНЫЕ КЛАВИАТУРЫ ---
def get_welcome_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура быстрых действий"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        types.KeyboardButton(text="🚀 Начать работу"),
        types.KeyboardButton(text="📚 Открыть справочник"),
    )
    builder.row(
        types.KeyboardButton(text="⭐ Избранное"),
        types.KeyboardButton(text="🔍 Поиск"),
    )
    builder.row(
        types.KeyboardButton(text="📥 Офлайн-версия"),
        types.KeyboardButton(text="ℹ️ О боте"),
    )
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

def get_main_menu(user_id: int, admin_ids: list) -> InlineKeyboardMarkup:
    """Главное инлайн-меню справочника"""
    builder = InlineKeyboardBuilder()
    
    sections = db.get_sections()
    
    for section in sections:
        emoji = section.get('icon', '📄')
        builder.row(types.InlineKeyboardButton(
            text=f"{emoji} {section['title']}",
            callback_data=f"view_section_{section['id']}"
        ))
    
    # Дополнительные кнопки
    builder.row(
        types.InlineKeyboardButton(text="⭐ Избранное", callback_data="favorites"),
        types.InlineKeyboardButton(text="🕜 Недавние", callback_data="recent"),
        width=2
    )
    
    builder.row(
        types.InlineKeyboardButton(text="🔍 Поиск по справочнику", callback_data="search"),
        types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        width=2
    )
    
    # Кнопка быстрого доступа для админов
    if user_id in admin_ids:
        builder.row(types.InlineKeyboardButton(
            text="✚ Админ: Новый раздел", 
            callback_data="admin_add_section_root"
        ))
    
    return builder.as_markup()

def get_section_menu(section_id: int, user_id: int, admin_ids: list, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Улучшенное меню раздела"""
    builder = InlineKeyboardBuilder()
    
    section = db.get_section(section_id)
    if not section:
        return get_main_menu(user_id, admin_ids)
    
    # Кнопка избранного
    star = "★" if is_favorite else "☆"
    builder.row(types.InlineKeyboardButton(
        text=f"{star} В избранное", 
        callback_data=f"toggle_fav_{section_id}"
    ))
    
    # Подразделы
    subsections = db.get_sections(section_id)
    for sub in subsections:
        emoji = sub.get('icon', '📁')
        builder.row(types.InlineKeyboardButton(
            text=f"   {emoji} {sub['title']}",
            callback_data=f"view_section_{sub['id']}"
        ))
    
    # Контент
    content_items = db.get_section_content(section_id)
    for item in content_items:
        btn_text = item['button_text'] or "📄 Открыть"
        emoji = "🎬" if 'видео' in btn_text.lower() else "📖" if 'руковод' in btn_text.lower() else "📋"
        builder.row(types.InlineKeyboardButton(
            text=f"   {emoji} {btn_text}",
            callback_data=f"view_content_{item['id']}"
        ))
    
    # Навигация
    nav_buttons = []
    
    if section['parent_id']:
        nav_buttons.append(types.InlineKeyboardButton(
            text="⬆️ На уровень выше", 
            callback_data=f"view_section_{section['parent_id']}"
        ))
    else:
        nav_buttons.append(types.InlineKeyboardButton(
            text="🏠 В главное меню", 
            callback_data="back_to_main"
        ))
    
    # Кнопки админа (если есть права)
    if user_id in admin_ids:
        builder.row(
            types.InlineKeyboardButton(text="✏️ Редакт.", callback_data=f"admin_edit_section_{section_id}"),
            types.InlineKeyboardButton(text="➕ Подраздел", callback_data=f"admin_add_subsection_{section_id}"),
            types.InlineKeyboardButton(text="➕ Контент", callback_data=f"admin_add_content_{section_id}"),
            width=3
        )
    
    builder.row(*nav_buttons)
    
    # Дополнительные кнопки внизу
    builder.row(
        types.InlineKeyboardButton(text="🔍 Поиск тут", callback_data=f"search_in_{section_id}"),
        types.InlineKeyboardButton(text="📋 Оглавление", callback_data="table_of_contents"),
        width=2
    )
    
    return builder.as_markup()

def get_content_menu(content_id: int, section_id: int, user_id: int, admin_ids: list) -> InlineKeyboardMarkup:
    """Меню контента с улучшенным дизайном"""
    builder = InlineKeyboardBuilder()
    
    # Основные кнопки
    builder.row(
        types.InlineKeyboardButton(text="⬅️ К разделу", callback_data=f"view_section_{section_id}"),
        types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main"),
        width=2
    )
    
    # Админские кнопки
    if user_id in admin_ids:
        builder.row(
            types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_content_{content_id}"),
            types.InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_delete_content_{content_id}"),
            width=2
        )
    
    # Дополнительные функции
    builder.row(
        types.InlineKeyboardButton(text="⭐ В избранное", callback_data=f"toggle_fav_{section_id}"),
        types.InlineKeyboardButton(text="📥 Сохранить", callback_data=f"save_content_{content_id}"),
        width=2
    )
    
    return builder.as_markup()

# --- КЛАВИАТУРЫ ДЛЯ АДМИНА ---
def get_admin_custom_icons_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кастомными иконками для разделов"""
    builder = InlineKeyboardBuilder()
    
    # Кастомные иконки (можно изменить на свои)
    custom_icons = [
        "🩸", "🚑", "🏥", "⚠️", "🆘", "💊", "📋", "📚",
        "🎖️", "⚔️", "🛡️", "🎯", "📍", "📌", "⭐", "🔥",
        "💥", "🎪", "🪖", "🔫", "🧭", "🧰", "🩹", "🚁"
    ]
    
    # Группируем по 4 иконки в ряд
    for i in range(0, len(custom_icons), 4):
        row_icons = custom_icons[i:i+4]
        builder.row(*[
            types.InlineKeyboardButton(text=icon, callback_data=f"custom_icon_{icon}")
            for icon in row_icons
        ])
    
    # Кнопка выбора из стандартных иконок
    builder.row(types.InlineKeyboardButton(
        text="📦 Стандартные иконки", 
        callback_data="show_standard_icons"
    ))
    
    # Кнопка без иконки
    builder.row(types.InlineKeyboardButton(
        text="❌ Без иконки", 
        callback_data="icon_none"
    ))
    
    return builder.as_markup()

def get_admin_icons_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора стандартных иконок"""
    builder = InlineKeyboardBuilder()
    
    icons = [
        "📚", "⚖️", "🎖️", "🆘", "💊", "🏥", "🚑", "⚠️", 
        "📋", "📖", "🎯", "🔴", "🟠", "🟡", "🟢", "🔵",
        "⭐", "📌", "📍", "📝", "📎", "📊", "📈", "📉"
    ]
    
    for i in range(0, len(icons), 4):
        row_icons = icons[i:i+4]
        builder.row(*[
            types.InlineKeyboardButton(text=icon, callback_data=f"icon_{icon}")
            for icon in row_icons
        ])
    
    builder.row(types.InlineKeyboardButton(text="❌ Без иконки", callback_data="icon_none"))
    
    return builder.as_markup()

# --- ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ ---
def get_favorites_keyboard(favorites, admin_ids: list) -> InlineKeyboardMarkup:
    """Клавиатура для избранного"""
    builder = InlineKeyboardBuilder()
    
    for fav in favorites:
        emoji = fav.get('icon', '⭐')
        builder.row(types.InlineKeyboardButton(
            text=f"{emoji} {fav['title']}",
            callback_data=f"view_section_{fav['id']}"
        ))
    
    builder.row(types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main"))
    
    return builder.as_markup()

def get_stats_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """Клавиатура для статистики"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data="stats"))
    
    if is_admin:
        builder.row(types.InlineKeyboardButton(text="📊 Детальная статистика", callback_data="detailed_stats"))
    
    builder.row(types.InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main"))
    
    return builder.as_markup()
