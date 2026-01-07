from datetime import datetime

def format_welcome_message(user_name: str, is_admin: bool) -> str:
    """Форматированное приветственное сообщение"""
    current_time = datetime.now().strftime("%H:%M")
    
    message = f"""
<b>🩸 ТАКТИЧЕСКИЙ МЕДИК</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

Приветствую, <b>{user_name}</b>!
Сейчас <b>{current_time}</b>

<u>Профессиональный справочник первой помощи</u>
• Актуальные методики и алгоритмы
• Работает полностью офлайн
• Постоянные обновления

{"👑 <b>СТАТУС:</b> <code>АДМИНИСТРАТОР</code> (доступно редактирование)" if is_admin else "👤 <b>СТАТУС:</b> <code>ПОЛЬЗОВАТЕЛЬ</code>"}

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<i>Используйте кнопки ниже для навигации</i>
    """
    
    return message.strip()

def format_section_card(section: dict) -> str:
    """Красивая карточка раздела без лишней информации"""
    emoji = section.get('icon', '📄')
    
    card = f"""
<b>{emoji} {section['title']}</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

{section.get('description', '📝 Описание отсутствует')}
    """
    
    return card.strip()

def format_user_stats(stats: dict, is_admin: bool = False) -> str:
    """Форматирование статистики для пользователя"""
    if is_admin:
        # Статистика для администратора
        stats_text = f"""
📊 <b>СТАТИСТИКА АДМИНИСТРАТОРА</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

<b>👥 ПОЛЬЗОВАТЕЛИ:</b>
• Всего пользователей: <b>{stats['total_users']}</b>
• За сутки: <b>{stats['daily_users']}</b>
• Активных (7 дней): <b>{stats['weekly_active']}</b>

<b>📚 КОНТЕНТ:</b>
• Разделов: <b>{stats['total_sections']}</b>
• Материалов: <b>{stats['total_content']}</b>

<b>📈 АКТИВНОСТЬ:</b>
• Просмотров разделов: <b>{stats['total_sections_viewed']}</b>
• Просмотров материалов: <b>{stats['total_content_viewed']}</b>

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<b>⭐ ПОПУЛЯРНЫЕ РАЗДЕЛЫ:</b>
"""
        
        for i, (title, fav_count) in enumerate(stats['popular_sections'], 1):
            stats_text += f"{i}. {title}: <b>{fav_count}</b> в избранном\n"
        
        stats_text += f"""
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>
        """
        
    else:
        # Статистика для обычного пользователя
        stats_text = f"""
📊 <b>СТАТИСТИКА СПРАВОЧНИКА</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

<b>📚 БАЗА ЗНАНИЙ:</b>
• Разделов: <b>{stats['total_sections']}</b>
• Материалов: <b>{stats['total_content']}</b>

<b>⭐ ВАША АКТИВНОСТЬ:</b>
• В избранном: <b>{stats['user_favorites']}</b>

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<i>Продолжайте изучать материалы!</i>
        """
    
    return stats_text.strip()

def format_detailed_stats(stats: dict) -> str:
    """Детальная статистика для администратора"""
    detailed_text = f"""
📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

<b>👥 ПОЛЬЗОВАТЕЛЬСКАЯ АНАЛИТИКА:</b>
• Всего уникальных пользователей: <b>{stats['total_users']}</b>
• Активность за 24ч: <b>{stats['daily_users']}</b> пользователей
• Активность за неделю: <b>{stats['weekly_active']}</b> пользователей

<b>📊 ЭФФЕКТИВНОСТЬ КОНТЕНТА:</b>
• Контент/пользователь: <b>{stats['total_content'] / max(stats['total_users'], 1):.1f}</b>
• Просмотров/пользователь: <b>{(stats['total_sections_viewed'] + stats['total_content_viewed']) / max(stats['total_users'], 1):.1f}</b>

<b>📈 ПОКАЗАТЕЛИ ВОВЛЕЧЕННОСТИ:</b>
• Всего просмотров: <b>{stats['total_sections_viewed'] + stats['total_content_viewed']}</b>
• Из них разделов: <b>{stats['total_sections_viewed']}</b>
• Из них материалов: <b>{stats['total_content_viewed']}</b>

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<b>📋 ПОСЛЕДНИЕ АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ:</b>
"""
    
    # Форматируем время для последних пользователей
    for user_id, last_seen in stats['recent_users'][:5]:
        if last_seen:
            try:
                last_seen_dt = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S')
                time_ago = datetime.now() - last_seen_dt
                hours_ago = int(time_ago.total_seconds() / 3600)
                
                if hours_ago < 1:
                    time_text = "только что"
                elif hours_ago < 24:
                    time_text = f"{hours_ago} ч. назад"
                else:
                    days = hours_ago // 24
                    time_text = f"{days} д. назад"
            except:
                time_text = "неизвестно"
        else:
            time_text = "никогда"
        
        detailed_text += f"• ID {user_id}: <i>{time_text}</i>\n"
    
    detailed_text += f"""
<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>
<i>Собрано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>
    """
    
    return detailed_text.strip()

def format_about_message() -> str:
    """Сообщение 'О боте'"""
    return f"""ℹ️ <b>О БОТЕ «ТАКТИЧЕСКИЙ МЕДИК»</b>

<b>Версия:</b> 2.0 Pro
<b>Обновлено:</b> {datetime.now().strftime('%d.%m.%Y')}

<u>Возможности:</u>
• 📚 Полный справочник тактической медицины
• 🆘 Алгоритмы первой помощи (КУЛАК БАРИН)
• 📋 Актуальные методики и стандарты
• 📥 Работа в офлайн-режиме
• ⭐ Система избранного
• 🔍 Умный поиск

<u>Для администраторов:</u>
• ✏️ Редактирование контента
• ➕ Добавление новых разделов
• 🗂️ Управление структурой

<i>Для учебных и справочных целей</i>"""