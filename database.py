import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="data/database.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица разделов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER DEFAULT NULL,
                order_index INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                icon TEXT DEFAULT '📄'
            )
        ''')
        
        # Таблица контента
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                section_id INTEGER,
                content_type TEXT NOT NULL,
                text_content TEXT,
                media_file_id TEXT,
                button_text TEXT,
                order_index INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_id) REFERENCES sections (id)
            )
        ''')
        
        # Таблица статистики
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sections_viewed INTEGER DEFAULT 0,
                content_viewed INTEGER DEFAULT 0,
                offline_downloads INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица избранного
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                section_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, section_id)
            )
        ''')
        
        # Проверяем, есть ли данные
        cursor.execute("SELECT COUNT(*) FROM sections")
        if cursor.fetchone()[0] == 0:
            self.create_default_content(cursor)
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
    
    def create_default_content(self, cursor):
        """Создание начальных данных"""
        try:
            # Основные разделы
            sections = [
                ("Правовая база", "Официальные документы", None, 1, 0, '⚖️'),
                ("Перечни и стандарты", "Состояния и мероприятия", None, 2, 0, '📋'),
                ("Алгоритм КУЛАК БАРИН", "Порядок приоритетов действий", None, 3, 0, '🆘'),
                ("Базовая помощь", "Основные приемы", None, 4, 0, '💊'),
            ]
            
            for title, description, parent_id, order_idx, created_by, icon in sections:
                cursor.execute('''
                    INSERT INTO sections (title, description, parent_id, order_index, created_by, icon)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, description, parent_id, order_idx, created_by, icon))
            
            # Получаем ID созданных разделов
            cursor.execute("SELECT id FROM sections WHERE title = ?", ("🆘 Алгоритм КУЛАК БАРИН",))
            section_id = cursor.fetchone()[0]
            
            # Контент для алгоритма КУЛАК БАРИН
            cook_content = '''<b>🆘 АЛГОРИТМ «КУЛАК БАРИН»</b>

<u>Порядок приоритетов действий</u>
Работай строго по буквам! Каждая минута на счету.

<code>━━━━━━━━━━━━━━━━━━━━━━━━</code>

<b>🔴 К – КРОВОТЕЧЕНИЕ (Blood Control)</b>
<i>Поиск и остановка жизнеугрожающего кровотечения</i>
• 🩸 <b>Действие:</b> Турникет (выше раны), тампонада раны, давящая повязка
• ⏱️ <b>Время:</b> Первые 1-2 минуты
• ✅ <b>Признак успеха:</b> Кровь остановлена'''
            
            cursor.execute('''
                INSERT INTO content (section_id, content_type, text_content, button_text, order_index, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (section_id, 'text', cook_content, '📖 Полное руководство', 1, 0))
            
            logger.info("✅ Начальный контент создан")
        except Exception as e:
            logger.error(f"⚠️ Ошибка при создании начального контента: {e}")
    
    # --- МЕТОДЫ ДЛЯ РАЗДЕЛОВ ---
    def get_sections(self, parent_id=None):
        """Получение разделов"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if parent_id is None:
            cursor.execute('''
                SELECT * FROM sections 
                WHERE parent_id IS NULL AND is_active = 1
                ORDER BY order_index
            ''')
        else:
            cursor.execute('''
                SELECT * FROM sections 
                WHERE parent_id = ? AND is_active = 1
                ORDER BY order_index
            ''', (parent_id,))
        
        sections = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sections
    
    def get_section(self, section_id):
        """Получение раздела по ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sections WHERE id = ?', (section_id,))
        section = cursor.fetchone()
        conn.close()
        return dict(section) if section else None
    
    def add_section(self, title, description, parent_id, created_by, icon="📄"):
        """Добавление нового раздела"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(order_index) FROM sections WHERE parent_id = ?', 
                      (parent_id if parent_id else None,))
        max_order = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            INSERT INTO sections (title, description, parent_id, order_index, created_by, icon)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, parent_id, max_order + 1, created_by, icon))
        
        section_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return section_id
    
    def update_section(self, section_id, **kwargs):
        """Обновление раздела"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if kwargs:
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [section_id]
            cursor.execute(f'UPDATE sections SET {set_clause} WHERE id = ?', values)
        
        conn.commit()
        conn.close()
        return True
    
    def delete_section(self, section_id):
        """Удаление раздела"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM content WHERE section_id = ?', (section_id,))
        cursor.execute('DELETE FROM sections WHERE id = ?', (section_id,))
        
        conn.commit()
        conn.close()
        return True
    
    # --- МЕТОДЫ ДЛЯ КОНТЕНТА ---
    def get_section_content(self, section_id):
        """Получение контента раздела"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM content 
            WHERE section_id = ? 
            ORDER BY order_index
        ''', (section_id,))
        content = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return content
    
    def get_content_with_section(self, content_id):
        """Получение контента с информацией о разделе"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.id as section_id, s.title as section_title 
            FROM content c 
            LEFT JOIN sections s ON c.section_id = s.id 
            WHERE c.id = ?
        ''', (content_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def add_content(self, section_id, content_type, text_content, button_text, created_by):
        """Добавление контента"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(order_index) FROM content WHERE section_id = ?', (section_id,))
        max_order = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            INSERT INTO content (section_id, content_type, text_content, button_text, order_index, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (section_id, content_type, text_content, button_text, max_order + 1, created_by))
        
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return content_id
    
    def update_content(self, content_id, **kwargs):
        """Обновление контента"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if kwargs:
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [content_id]
            cursor.execute(f'UPDATE content SET {set_clause} WHERE id = ?', values)
        
        conn.commit()
        conn.close()
        return True
    
    def delete_content(self, content_id):
        """Удаление контента"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM content WHERE id = ?', (content_id,))
        conn.commit()
        conn.close()
        return True
    
    # --- МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ---
    def update_user_stats(self, user_id, section_viewed=False, content_viewed=False):
        """Обновление статистики пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO user_stats (user_id, first_seen, last_seen)
                VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id,))
            is_new_user = True
        else:
            cursor.execute('''
                UPDATE user_stats 
                SET last_seen = CURRENT_TIMESTAMP,
                    sections_viewed = sections_viewed + ?,
                    content_viewed = content_viewed + ?
                WHERE user_id = ?
            ''', (1 if section_viewed else 0, 1 if content_viewed else 0, user_id))
            is_new_user = False
        
        conn.commit()
        conn.close()
        return is_new_user
    
    def toggle_favorite(self, user_id, section_id):
        """Добавление/удаление из избранного"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM favorites WHERE user_id = ? AND section_id = ?', 
                      (user_id, section_id))
        
        if cursor.fetchone():
            cursor.execute('DELETE FROM favorites WHERE user_id = ? AND section_id = ?', 
                          (user_id, section_id))
            result = False  # Удалено
        else:
            cursor.execute('INSERT INTO favorites (user_id, section_id) VALUES (?, ?)', 
                          (user_id, section_id))
            result = True  # Добавлено
        
        conn.commit()
        conn.close()
        return result
    
    def get_favorites(self, user_id):
        """Получение избранного пользователя"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.* FROM sections s
            JOIN favorites f ON s.id = f.section_id
            WHERE f.user_id = ? AND s.is_active = 1
            ORDER BY f.added_at DESC
        ''', (user_id,))
        
        favorites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return favorites
    
    # --- МЕТОДЫ ДЛЯ СТАТИСТИКИ ---
    def get_user_stats_summary(self):
        """Получить сводную статистику по пользователям"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        total_users = cursor.fetchone()[0] or 0
        
        # Пользователи за последние 24 часа
        cursor.execute('''
            SELECT COUNT(*) FROM user_stats 
            WHERE last_seen >= datetime('now', '-1 day')
        ''')
        daily_users = cursor.fetchone()[0] or 0
        
        # Активные пользователи (за последнюю неделю)
        cursor.execute('''
            SELECT COUNT(*) FROM user_stats 
            WHERE last_seen >= datetime('now', '-7 days')
        ''')
        weekly_active = cursor.fetchone()[0] or 0
        
        # Статистика по просмотрам
        cursor.execute("SELECT SUM(sections_viewed) FROM user_stats")
        total_sections_viewed = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(content_viewed) FROM user_stats")
        total_content_viewed = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_users': total_users,
            'daily_users': daily_users,
            'weekly_active': weekly_active,
            'total_sections_viewed': total_sections_viewed,
            'total_content_viewed': total_content_viewed
        }
    
    def get_admin_stats(self):
        """Полная статистика для администратора"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Статистика пользователей
        user_stats = self.get_user_stats_summary()
        
        # Статистика контента
        cursor.execute("SELECT COUNT(*) FROM sections WHERE is_active = 1")
        total_sections = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM content")
        total_content = cursor.fetchone()[0] or 0
        
        # Популярные разделы (по количеству в избранном)
        cursor.execute('''
            SELECT s.title, COUNT(f.section_id) as fav_count 
            FROM sections s 
            LEFT JOIN favorites f ON s.id = f.section_id 
            WHERE s.is_active = 1 
            GROUP BY s.id 
            ORDER BY fav_count DESC 
            LIMIT 5
        ''')
        popular_sections = cursor.fetchall()
        
        # Последние активные пользователи
        cursor.execute('''
            SELECT user_id, last_seen 
            FROM user_stats 
            ORDER BY last_seen DESC 
            LIMIT 10
        ''')
        recent_users = cursor.fetchall()
        
        conn.close()
        
        return {
            **user_stats,
            'total_sections': total_sections,
            'total_content': total_content,
            'popular_sections': popular_sections,
            'recent_users': recent_users
        }
