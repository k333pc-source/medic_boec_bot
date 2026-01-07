from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import Database
import os

db = Database()

class AdminPanel:
    def __init__(self, admin_ids: list):
        self.admin_ids = admin_ids
    
    def is_admin(self, user_id):
        return user_id in self.admin_ids
    
    async def show_admin_menu(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            await message.answer("⛔ Доступ запрещен")
            return
        
        keyboard = InlineKeyboardBuilder()
        keyboard.row(types.InlineKeyboardButton(
            text="📂 Управление разделами", 
            callback_data="admin_sections"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="📝 Редактировать контент", 
            callback_data="admin_content"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="➕ Добавить раздел", 
            callback_data="admin_add_section"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="🔄 Обновить офлайн-данные", 
            callback_data="admin_update_offline"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="📊 Статистика", 
            callback_data="admin_stats"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data="back_to_main"
        ))
        
        await message.answer(
            "⚙️ *Панель администратора*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    
    async def show_sections_management(self, callback: types.CallbackQuery, parent_id=None):
        keyboard = InlineKeyboardBuilder()
        sections = db.get_sections(parent_id)
        
        for section in sections:
            keyboard.row(types.InlineKeyboardButton(
                text=f"📁 {section['title']}", 
                callback_data=f"admin_section_{section['id']}"
            ))
            keyboard.row(
                types.InlineKeyboardButton(
                    text="✏️ Редактировать", 
                    callback_data=f"admin_edit_section_{section['id']}"
                ),
                types.InlineKeyboardButton(
                    text="🗑️ Удалить", 
                    callback_data=f"admin_delete_section_{section['id']}"
                ),
                width=2
            )
        
        if parent_id:
            parent_section = db.get_section(parent_id)
            keyboard.row(types.InlineKeyboardButton(
                text=f"⬅️ Назад к {parent_section['title']}", 
                callback_data=f"admin_sections_{parent_section['parent_id']}"
                if parent_section['parent_id'] else "admin_sections"
            ))
        
        keyboard.row(types.InlineKeyboardButton(
            text="➕ Добавить подраздел", 
            callback_data=f"admin_add_subsection_{parent_id}" if parent_id else "admin_add_section"
        ))
        keyboard.row(types.InlineKeyboardButton(
            text="🔙 В админку", 
            callback_data="admin_menu"
        ))
        
        await callback.message.edit_text(
            "📂 *Управление разделами*\n\n"
            "Выберите раздел для редактирования:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    
    async def show_section_content(self, callback: types.CallbackQuery, section_id):
        section = db.get_section(section_id)
        content_items = db.get_section_content(section_id)
        
        text = f"📝 *Редактирование раздела:* {section['title']}\n\n"
        
        keyboard = InlineKeyboardBuilder()
        
        for item in content_items:
            item_type_emoji = {
                'text': '📄',
                'image': '🖼️',
                'video': '🎬',
                'document': '📎'
            }.get(item['content_type'], '📌')
            
            btn_text = item['button_text'] or f"Элемент #{item['id']}"
            text += f"{item_type_emoji} {btn_text}\n"
            
            keyboard.row(
                types.InlineKeyboardButton(
                    text=f"✏️ {btn_text[:15]}...", 
                    callback_data=f"admin_edit_content_{item['id']}"
                ),
                types.InlineKeyboardButton(
                    text="🗑️", 
                    callback_data=f"admin_delete_content_{item['id']}"
                ),
                width=2
            )
        
        keyboard.row(types.InlineKeyboardButton(
            text="➕ Добавить текст", 
            callback_data=f"admin_add_text_{section_id}"
        ))
        keyboard.row(
            types.InlineKeyboardButton(
                text="➕ Добавить фото", 
                callback_data=f"admin_add_photo_{section_id}"
            ),
            types.InlineKeyboardButton(
                text="➕ Добавить видео", 
                callback_data=f"admin_add_video_{section_id}"
            ),
            width=2
        )
        keyboard.row(types.InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"admin_sections_{section['parent_id']}"
            if section['parent_id'] else "admin_sections"
        ))
        
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    
    async def start_adding_section(self, callback: types.CallbackQuery, parent_id=None):
        await callback.message.edit_text(
            "📝 *Добавление нового раздела*\n\n"
            "Введите название раздела:",
            parse_mode="Markdown"
        )
        # Устанавливаем состояние для ожидания названия
        # В реальной реализации здесь будет FSM (Finite State Machine)
    
    async def start_editing_content(self, callback: types.CallbackQuery, content_id):
        # Здесь будет форма редактирования контента
        await callback.message.answer(
            "Отправьте новый текст для этого элемента:",
            reply_markup=types.ForceReply()
        )