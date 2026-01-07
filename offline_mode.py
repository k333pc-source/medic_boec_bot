import os
import json
import sqlite3
from datetime import datetime
from aiogram import types
from aiogram.types import FSInputFile
from database import Database

class OfflineMode:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.offline_data_dir = "data/offline_packs"
        os.makedirs(self.offline_data_dir, exist_ok=True)
    
    async def generate_offline_pack(self, user_id):
        """Создание офлайн-пакета для пользователя"""
        pack_dir = os.path.join(self.offline_data_dir, str(user_id))
        os.makedirs(pack_dir, exist_ok=True)
        
        # 1. Экспортируем структуру разделов
        sections = self._get_all_sections()
        with open(os.path.join(pack_dir, 'sections.json'), 'w', encoding='utf-8') as f:
            json.dump(sections, f, ensure_ascii=False, indent=2)
        
        # 2. Экспортируем весь текстовый контент
        content = self._get_all_content()
        with open(os.path.join(pack_dir, 'content.json'), 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        # 3. Копируем медиа-файлы
        media_count = self._copy_media_files(pack_dir)
        
        # 4. Создаем HTML-версию справочника
        self._create_html_version(pack_dir, sections, content)
        
        # 5. Создаем архив
        import zipfile
        zip_path = os.path.join(self.offline_data_dir, f'{user_id}_offline_pack.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(pack_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pack_dir)
                    zipf.write(file_path, arcname)
        
        # Обновляем статус пользователя
        self.db.set_user_offline_mode(user_id, True)
        
        return zip_path, media_count
    
    def _get_all_sections(self):
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sections WHERE is_active = 1')
        sections = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return sections
    
    def _get_all_content(self):
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, s.title as section_title 
            FROM content c 
            LEFT JOIN sections s ON c.section_id = s.id
            WHERE s.is_active = 1
        ''')
        content = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return content
    
    def _copy_media_files(self, pack_dir):
        media_dir = os.path.join(pack_dir, 'media')
        os.makedirs(media_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT local_path, file_type FROM media_cache')
        media_files = cursor.fetchall()
        conn.close()
        
        count = 0
        for local_path, file_type in media_files:
            if os.path.exists(local_path):
                import shutil
                dest_path = os.path.join(media_dir, os.path.basename(local_path))
                shutil.copy2(local_path, dest_path)
                count += 1
        
        return count
    
    def _create_html_version(self, pack_dir, sections, content):
        html_path = os.path.join(pack_dir, 'index.html')
        
        html_content = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Тактическая медицина - Офлайн справочник</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin-bottom: 30px; border-left: 4px solid #007bff; padding-left: 15px; }
                .subsection { margin-left: 20px; margin-top: 15px; }
                .content-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .media { max-width: 100%; height: auto; }
                h1 { color: #dc3545; }
                h2 { color: #007bff; }
                .offline-badge { background: #28a745; color: white; padding: 5px 10px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>📚 Справочник по тактической медицине</h1>
            <p><span class="offline-badge">ОФЛАЙН ВЕРСИЯ</span> Обновлено: """ + datetime.now().strftime("%d.%m.%Y %H:%M") + """</p>
            
            <div id="content">
        """
        
        # Добавляем разделы и контент
        for section in sections:
            if section['parent_id'] is None:
                html_content += f"""
                <div class="section">
                    <h2>{section['title']}</h2>
                    <p>{section['description'] or ''}</p>
                """
                
                # Добавляем подразделы
                for subsection in sections:
                    if subsection['parent_id'] == section['id']:
                        html_content += f"""
                        <div class="subsection">
                            <h3>{subsection['title']}</h3>
                            <p>{subsection['description'] or ''}</p>
                        """
                        
                        # Добавляем контент подраздела
                        for item in content:
                            if item['section_id'] == subsection['id']:
                                html_content += self._content_to_html(item, pack_dir)
                        
                        html_content += "</div>"
                
                html_content += "</div>"
        
        html_content += """
            </div>
            
            <script>
                // Простой поиск по странице
                function searchContent() {
                    var input = document.getElementById('searchInput');
                    var filter = input.value.toUpperCase();
                    var content = document.getElementById('content');
                    var items = content.getElementsByClassName('content-item');
                    
                    for (var i = 0; i < items.length; i++) {
                        var text = items[i].textContent || items[i].innerText;
                        if (text.toUpperCase().indexOf(filter) > -1) {
                            items[i].style.display = "";
                        } else {
                            items[i].style.display = "none";
                        }
                    }
                }
            </script>
            
            <input type="text" id="searchInput" onkeyup="searchContent()" placeholder="Поиск по справочнику...">
            
            <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>Данный справочник предназначен для использования в условиях отсутствия связи.</p>
                <p>Основано на Приказе МО РФ №760 и стандартах тактической медицины.</p>
            </footer>
        </body>
        </html>
        """
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _content_to_html(self, item, pack_dir):
        html = f'<div class="content-item">\n'
        
        if item['content_type'] == 'text':
            html += f"<p>{item['text_content'].replace('*', '<strong>').replace('*', '</strong>')}</p>\n"
        elif item['content_type'] == 'image' and item['media_local_path']:
            rel_path = os.path.relpath(item['media_local_path'], pack_dir)
            html += f'<img src="{rel_path}" class="media" alt="Изображение">\n'
        elif item['content_type'] == 'video' and item['media_local_path']:
            rel_path = os.path.relpath(item['media_local_path'], pack_dir)
            html += f'''
            <video controls class="media">
                <source src="{rel_path}" type="video/mp4">
                Ваш браузер не поддерживает видео.
            </video>\n
            '''
        
        html += '</div>\n'
        return html
    
    async def send_offline_pack(self, user_id):
        """Отправка офлайн-пакета пользователю"""
        try:
            zip_path, media_count = await self.generate_offline_pack(user_id)
            
            # Отправляем архив
            document = FSInputFile(zip_path, filename="Тактическая_медицина_офлайн.zip")
            
            await self.bot.send_document(
                chat_id=user_id,
                document=document,
                caption=(
                    "📦 *Офлайн-пакет справочника*\n\n"
                    f"✅ Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"📁 Медиафайлов: {media_count}\n"
                    f"📄 Форматы: HTML + JSON\n\n"
                    "Распакуйте архив на устройстве. "
                    "Откройте файл index.html в браузере."
                ),
                parse_mode="Markdown"
            )
            
            # Удаляем временный файл
            os.remove(zip_path)
            
        except Exception as e:
            print(f"Error creating offline pack: {e}")
            return False
        
        return True