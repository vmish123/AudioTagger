import os
from view import ArtistDialog
from PyQt6.QtCore import QUrl


class AppController:
    """Управление взаимодействием между графическим интерфейсом и данными."""
    # Инициализация контроллера и привязка сигналов интерфейса к логике приложения
    def __init__(self, view, db_manager, tag_editor):
        self.view = view
        self.db = db_manager
        self.tag_editor = tag_editor

        # Привязка сигналов главного окна к методам контроллера
        self.view.sig_add_folder.connect(self.scan_folder)
        self.view.sig_track_selected.connect(self.load_track_details)
        self.view.sig_save_tags.connect(self.save_track_tags)
        self.view.sig_delete_track.connect(self.delete_track)
        self.view.sig_manage_artists.connect(self.open_artist_dialog)

        # Первичное заполнение интерфейса данными при запуске
        self.refresh_main_view()

    # Обновление таблицы треков и выпадающего списка исполнителей в главном окне
    def refresh_main_view(self):
        # Извлечение треков из базы и передача в таблицу
        tracks = self.db.get_all_tracks()
        self.view.populate_table(tracks)

        # Извлечение списка исполнителей и передача в интерфейс
        artists = self.db.get_all_artists()
        self.view.populate_artists_combo(artists)

    # Сканирование выбранной директории на наличие аудиофайлов и их загрузка в базу данных
    def scan_folder(self, folder_path: str):
        # Очистка базы данных от старых записей
        self.db.clear_library()

        # Остановка плеера и сброс данных в правой панели
        self.view.player.stop()
        self.view.set_cover_image(None)
        self.view.fill_editor_form({})
        self.view._current_file_path = None

        supported_formats = ('.mp3', '.flac')
        added_count = 0

        # Обход всех вложенных папок и файлов
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Фильтрация файлов по поддерживаемым форматам
                if file.lower().endswith(supported_formats):
                    file_path = os.path.join(root, file)

                    # Извлечение тегов из файла
                    tags = self.tag_editor.read_tags(file_path)

                    # Сохранение данных о треке в базу
                    self.db.add_or_update_track(file_path, tags)
                    added_count += 1

        # Обновление графического интерфейса после завершения сканирования
        self.refresh_main_view()
        self.view.show_message("Успех", f"Загружено треков: {added_count}")

    # Извлечение и передача метаданных выбранного трека в форму редактирования
    def load_track_details(self, file_path: str):
        # Проверка фактического наличия файла на диске
        if not os.path.exists(file_path):
            self.view.show_message(
                "Ошибка",
                "Файл был удален или перемещен."
            )
            # Удаление записи из базы в случае отсутствия файла
            self.db.delete_track(file_path)
            self.refresh_main_view()

            # Очистка формы редактирования
            self.view.fill_editor_form({})
            self.view.set_cover_image(None)
            return

        # Чтение актуальных тегов напрямую из файла
        tags = self.tag_editor.read_tags(file_path)

        # Заполнение полей формы и установка изображения обложки
        self.view.fill_editor_form(tags)
        self.view.set_cover_image(tags.get('cover_data'))

    # Сохранение новых тегов в аудиофайл и синхронизация с базой данных
    def save_track_tags(self, file_path: str, new_tags: dict):
        # Освобождение файла от захвата плеером для предотвращения ошибок доступа
        self.view.player.stop()
        self.view.player.setSource(QUrl())

        # Физическая запись новых данных в файл
        success = self.tag_editor.write_tags(file_path, new_tags)

        if success:
            # Обновление записи в базе данных
            self.db.add_or_update_track(file_path, new_tags)
            self.refresh_main_view()

            # Восстановление визуального выделения строки в таблице
            self.view.restore_selection(file_path)

            self.view.show_message("Успех", "Теги успешно сохранены.")

            # Возврат трека в память плеера
            self.view.player.setSource(QUrl.fromLocalFile(file_path))
        else:
            self.view.show_message(
                "Ошибка",
                "Не удалось сохранить теги.\nВозможно, файл открыт в другом месте."
            )
            # Возврат трека в память плеера даже в случае ошибки
            self.view.player.setSource(QUrl.fromLocalFile(file_path))

    # Удаление записи о треке из базы данных и обновление интерфейса
    def delete_track(self, file_path: str):
        self.db.delete_track(file_path)
        self.refresh_main_view()

    # Отображение окна управления исполнителями и обработка его сигналов
    def open_artist_dialog(self):
        # Создание экземпляра диалогового окна
        dialog = ArtistDialog(self.view)

        # Привязка сигналов диалога к внутренним методам контроллера
        dialog.sig_add_artist.connect(lambda name: self._artist_add(name, dialog))
        dialog.sig_update_artist.connect(lambda a_id, name: self._artist_update(a_id, name, dialog))
        dialog.sig_delete_artist.connect(lambda a_id: self._artist_delete(a_id, dialog))

        # Первичное заполнение списка в диалоговом окне
        dialog.populate_list(self.db.get_all_artists())

        # Запуск окна
        dialog.exec()

        # Обновление главного окна после закрытия диалога
        self.refresh_main_view()

    # Добавление нового исполнителя в базу и обновление списка в диалоге
    def _artist_add(self, name: str, dialog: ArtistDialog):
        self.db.add_artist(name)
        dialog.populate_list(self.db.get_all_artists())

    # Обновление имени исполнителя в базе и обновление списка в диалоге
    def _artist_update(self, artist_id: int, new_name: str, dialog: ArtistDialog):
        self.db.update_artist(artist_id, new_name)
        dialog.populate_list(self.db.get_all_artists())

    # Удаление исполнителя из базы и обновление списка в диалоге
    def _artist_delete(self, artist_id: int, dialog: ArtistDialog):
        self.db.delete_artist(artist_id)
        dialog.populate_list(self.db.get_all_artists())
