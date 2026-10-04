import sqlite3


class DatabaseManager:
    """Управление локальной базой данных SQLite для хранения библиотеки треков и исполнителей."""
    def __init__(self, db_name="library.db"):
        # Инициализация подключения к базе данных и запуск создания таблиц
        self.db_name = db_name
        self.create_tables()

    # Выполнение SQL-запроса с безопасной подстановкой параметров и обработкой результата
    def _execute_query(self, query: str, parameters: tuple = (), fetch: str = None, _is_retry: bool = False):
        try:
            with sqlite3.connect(self.db_name) as conn:
                # Включение поддержки внешних ключей
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()

                # Выполнение переданного запроса
                cursor.execute(query, parameters)

                # Извлечение всех найденных записей
                if fetch == 'all':
                    return cursor.fetchall()
                # Извлечение только первой найденной записи
                elif fetch == 'one':
                    return cursor.fetchone()

                # Фиксация изменений в базе данных
                conn.commit()

        # Проверка на отсутствие таблиц
        except sqlite3.OperationalError as error:
            if "no such table" in str(error).lower() and not _is_retry:
                # Воссоздание структуры таблиц в новом пустом файле
                self.create_tables()
                # Повторное выполнение упавшего запроса
                return self._execute_query(query, parameters, fetch, _is_retry=True)

            # Если это другая ошибка или повторная попытка не удалась
            raise error

    # Создание необходимых таблиц в базе данных при их отсутствии
    def create_tables(self):
        # Создание таблицы исполнителей
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # Создание таблицы треков со связью с таблицей исполнителей
        self._execute_query('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                title TEXT,
                album TEXT,
                year INTEGER,
                artist_id INTEGER,
                FOREIGN KEY(artist_id) REFERENCES artists(id) ON DELETE SET NULL
            )
        ''')

    # Извлечение списка всех исполнителей с сортировкой по алфавиту
    def get_all_artists(self) -> list:
        query = "SELECT id, name FROM artists ORDER BY name"
        return self._execute_query(query, fetch='all')

    # Добавление нового исполнителя в базу данных или возврат ID существующего
    def add_artist(self, name: str) -> int:
        if not name.strip():
            return None

        # Поиск исполнителя на предмет его существования в базе
        query_check = "SELECT id FROM artists WHERE name = ?"
        result = self._execute_query(query_check, (name,), fetch='one')
        if result:
            return result[0]

        # Добавление новой записи при отсутствии совпадений
        query_insert = "INSERT INTO artists (name) VALUES (?)"
        self._execute_query(query_insert, (name,))

        # Извлечение и возврат ID только что созданного исполнителя
        return self._execute_query(query_check, (name,), fetch='one')[0]

    # Обновление имени исполнителя по его идентификатору
    def update_artist(self, artist_id: int, new_name: str):
        query = "UPDATE artists SET name = ? WHERE id = ?"
        try:
            # Применение нового имени
            self._execute_query(query, (new_name, artist_id))
        except sqlite3.IntegrityError:
            # Перехват ошибки нарушения уникальности
            print("Исполнитель с таким именем уже существует")

    # Удаление исполнителя из базы данных по его идентификатору
    def delete_artist(self, artist_id: int):
        query = "DELETE FROM artists WHERE id = ?"
        self._execute_query(query, (artist_id,))

    # Извлечение списка всех треков с присоединением имен исполнителей
    def get_all_tracks(self) -> list:
        query = '''
            SELECT t.file_path, t.title, a.name, t.album, t.year
            FROM tracks t
            LEFT JOIN artists a ON t.artist_id = a.id
            ORDER BY t.file_path
        '''
        return self._execute_query(query, fetch='all')

    # Добавление нового трека в библиотеку или обновление существующего
    def add_or_update_track(self, file_path: str, tags: dict):
        # Получение имени исполнителя и его идентификатора
        artist_name = tags.get('artist', 'Неизвестен')
        artist_id = self.add_artist(artist_name)

        # Вставка новой записи или замена существующей при совпадении file_path
        query = '''
            INSERT OR REPLACE INTO tracks (file_path, title, album, year, artist_id)
            VALUES (?, ?, ?, ?, ?)
        '''
        self._execute_query(query, (
            file_path,
            tags.get('title', ''),
            tags.get('album', ''),
            tags.get('year', 0),
            artist_id
        ))

    # Удаление конкретного файла трека из библиотеки
    def delete_track(self, file_path: str):
        query = "DELETE FROM tracks WHERE file_path = ?"
        self._execute_query(query, (file_path,))

    # Очистка всей таблицы треков
    def clear_library(self):
        self._execute_query("DELETE FROM tracks")
