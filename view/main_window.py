from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QHeaderView, QAbstractItemView, QMenu
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QKeyEvent
from PyQt6.QtCore import pyqtSignal, Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from ui.ui_main_window import Ui_MainWindow


class MainWindow(QMainWindow):
    """Отображение главного окна приложения и обработка действий пользователя."""
    # Объявление пользовательских сигналов для связи с контроллером
    sig_add_folder = pyqtSignal(str)
    sig_manage_artists = pyqtSignal()
    sig_track_selected = pyqtSignal(str)
    sig_save_tags = pyqtSignal(str, dict)
    sig_delete_track = pyqtSignal(str)

    # Инициализация главного окна и настройка компонентов интерфейса
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Фиксация размера окна
        self.setFixedSize(850, 600)

        # Инициализация внутренних переменных состояния
        self._current_file_path = None
        self._current_cover_data = None

        # Установка значения по умолчанию для года
        self.ui.spin_year.setValue(1970)

        # Настройка модели таблицы для отображения списка треков
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(['Путь', 'Название', 'Исполнитель', 'Альбом', 'Год'])
        self.ui.tableView_tracks.setModel(self.table_model)

        # Скрытие технической колонки с путем к файлу
        self.ui.tableView_tracks.setColumnHidden(0, True)
        self.ui.tableView_tracks.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Инициализация аудиоплеера
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        # Привязка кнопок к локальным методам-обработчикам
        self.ui.btn_add_folder.clicked.connect(self._on_add_folder_clicked)
        self.ui.btn_manage_artists.clicked.connect(self._on_manage_artists_clicked)
        self.ui.btn_save_tags.clicked.connect(self._on_save_tags_clicked)

        # Привязка кнопок управления плеером
        self.ui.btn_play.clicked.connect(self.player.play)
        self.ui.btn_stop.clicked.connect(self.player.pause)

        # Привязка событий мыши
        self.ui.tableView_tracks.clicked.connect(self._on_table_row_clicked)
        self.ui.tableView_tracks.doubleClicked.connect(self._on_table_double_clicked)
        self.ui.label_cover_2.mouseDoubleClickEvent = self._on_cover_double_clicked

        # Блокировка редактирования ячеек таблицы
        self.ui.tableView_tracks.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Привязка событий плеера к ползунку времени
        self.player.positionChanged.connect(self._update_slider_position)
        self.player.durationChanged.connect(self._update_slider_duration)
        self.ui.slider_progress.sliderMoved.connect(self.player.setPosition)

        # Настройка вызова контекстного меню
        self.ui.tableView_tracks.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableView_tracks.customContextMenuRequested.connect(self._show_context_menu)

    # Вызов диалога выбора директории с аудиофайлами
    def _on_add_folder_clicked(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку")
        if folder_path:
            self.sig_add_folder.emit(folder_path)

    # Инициация открытия окна управления исполнителями
    def _on_manage_artists_clicked(self):
        self.sig_manage_artists.emit()

    # Обработка одинарного клика по треку
    def _on_table_row_clicked(self, index):
        file_path_index = self.table_model.index(index.row(), 0)
        file_path = self.table_model.data(file_path_index)

        # Проверка на совпадение с текущим треком во избежание лишних загрузок
        if self._current_file_path != file_path:
            self._current_file_path = file_path

            # Остановка старого трека и загрузка нового в память плеера
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(file_path))

            self.sig_track_selected.emit(file_path)

    # Обработка двойного клика по треку
    def _on_table_double_clicked(self, index):
        if self._current_file_path:
            self.player.play()

    # Сбор данных из формы и инициация их сохранения
    def _on_save_tags_clicked(self):
        if not self._current_file_path:
            QMessageBox.warning(self, "Ошибка", "Выберите трек для сохранения.")
            return

        # Формирование словаря с новыми метаданными
        new_tags = {
            'title': self.ui.edit_title.text(),
            'artist': self.ui.combo_artist.currentText(),
            'album': self.ui.edit_album.text(),
            'year': self.ui.spin_year.value(),
            'cover_data': self._current_cover_data
        }
        self.sig_save_tags.emit(self._current_file_path, new_tags)

    # Вызов диалога выбора нового изображения для обложки
    def _on_cover_double_clicked(self, event):
        if not self._current_file_path:
            return

        # Открытие стандартного диалога выбора файла
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите обложку", "", "Images (*.png *.jpg *.jpeg)")

        if file_path:
            # Чтение изображения в бинарном формате
            with open(file_path, 'rb') as f:
                self._current_cover_data = f.read()

            # Обновление изображения в интерфейсе
            self.set_cover_image(self._current_cover_data)

    # Формирование и отображение контекстного меню при клике правой кнопкой мыши
    def _show_context_menu(self, position):
        index = self.ui.tableView_tracks.indexAt(position)
        if not index.isValid():
            return

        # Создание меню и добавление действий
        menu = QMenu()
        delete_action = menu.addAction("Удалить")

        # Отображение меню по координатам курсора
        action = menu.exec(self.ui.tableView_tracks.viewport().mapToGlobal(position))

        # Обработка выбора пункта удаления
        if action == delete_action:
            file_path_index = self.table_model.index(index.row(), 0)
            file_path = self.table_model.data(file_path_index)

            reply = QMessageBox.question(self, 'Удаление', 'Удалить этот трек из библиотеки?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.sig_delete_track.emit(file_path)

    # Перехват и обработка нажатий клавиш на клавиатуре
    def keyPressEvent(self, event: QKeyEvent):
        # Обработка нажатия клавиши Delete
        if event.key() == Qt.Key.Key_Delete:
            selected_indexes = self.ui.tableView_tracks.selectionModel().selectedRows()
            if selected_indexes:
                row = selected_indexes[0].row()
                file_path = self.table_model.data(self.table_model.index(row, 0))

                # Запрос подтверждения перед удалением
                reply = QMessageBox.question(self, 'Удаление', 'Удалить этот трек из библиотеки?',
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.sig_delete_track.emit(file_path)
        else:
            # Передача остальных нажатий базовому классу
            super().keyPressEvent(event)

    # Заполнение таблицы треков данными из базы
    def populate_table(self, tracks_data: list):
        # Очистка старых данных
        self.table_model.removeRows(0, self.table_model.rowCount())

        # Добавление новых строк
        for row_data in tracks_data:
            items = [QStandardItem(str(field)) for field in row_data]
            self.table_model.appendRow(items)

    # Заполнение выпадающего списка доступными исполнителями
    def populate_artists_combo(self, artists_list: list):
        self.ui.combo_artist.clear()
        self.ui.combo_artist.addItems([artist[1] for artist in artists_list])  # artist[1] это name

    # Распределение данных выбранного трека по полям редактирования
    def fill_editor_form(self, tags: dict):
        self.ui.edit_title.setText(tags.get('title', ''))
        self.ui.combo_artist.setCurrentText(tags.get('artist', ''))
        self.ui.edit_album.setText(tags.get('album', ''))

        year = tags.get('year')
        self.ui.spin_year.setValue(year if year else 1970)

    # Отображение обложки альбома в соответствующем элементе интерфейса
    def set_cover_image(self, cover_data: bytes):
        self._current_cover_data = cover_data

        if cover_data:
            # Преобразование байтов в изображение и масштабирование
            pixmap = QPixmap()
            pixmap.loadFromData(cover_data)
            pixmap = pixmap.scaled(self.ui.label_cover_2.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.ui.label_cover_2.setPixmap(pixmap)
        else:
            # Сброс изображения
            self.ui.label_cover_2.clear()
            self.ui.label_cover_2.setText("Нет обложки")

    # Отображение всплывающего информационного окна
    def show_message(self, title: str, text: str):
        QMessageBox.information(self, title, text)

    # Обновление позиции ползунка плеера и таймера текущего времени
    def _update_slider_position(self, position):
        self.ui.slider_progress.setValue(position)
        self.ui.lbl_time_current.setText(self._format_time(position))

    # Установка максимального значения ползунка и таймера общей длительности
    def _update_slider_duration(self, duration):
        self.ui.slider_progress.setRange(0, duration)
        self.ui.lbl_time_total.setText(self._format_time(duration))

    # Форматирование времени из миллисекунд в строку формата ММ:СС
    def _format_time(self, ms: int) -> str:
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000) % 60
        return f"{minutes:02}:{seconds:02}"

    # Восстановление визуального выделения трека в таблице после обновления данных
    def restore_selection(self, target_file_path: str):
        for row in range(self.table_model.rowCount()):
            index = self.table_model.index(row, 0)
            file_path = self.table_model.data(index)

            if file_path == target_file_path:
                self.ui.tableView_tracks.selectRow(row)
                self.ui.tableView_tracks.scrollTo(index)
                break
