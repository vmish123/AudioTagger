from PyQt6.QtWidgets import QDialog, QMessageBox, QListWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt

from ui.ui_artist_dialog import Ui_ArtistDialog


class ArtistDialog(QDialog):
    """Управление списком исполнителей через диалоговое окно."""
    # Объявление сигналов для передачи команд контроллеру
    sig_add_artist = pyqtSignal(str)
    sig_update_artist = pyqtSignal(int, str)
    sig_delete_artist = pyqtSignal(int)

    def __init__(self, parent=None):
        # Инициализация диалогового окна и настройка компонентов интерфейса
        super().__init__(parent)
        self.ui = Ui_ArtistDialog()
        self.ui.setupUi(self)

        # Блокировка главного окна до закрытия текущего диалога
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Привязка кнопок к локальным методам-обработчикам
        self.ui.btn_add.clicked.connect(self._on_add_clicked)
        self.ui.btn_update.clicked.connect(self._on_update_clicked)
        self.ui.btn_delete.clicked.connect(self._on_delete_clicked)
        self.ui.btn_close.clicked.connect(self.accept)

        # Привязка события клика по элементу списка
        self.ui.listWidget_artists.itemClicked.connect(self._on_item_clicked)

    # Перенос имени выбранного исполнителя из списка в поле ввода
    def _on_item_clicked(self, item: QListWidgetItem):
        self.ui.edit_artist_name.setText(item.text())

    # Извлечение скрытого идентификатора исполнителя из выбранного элемента списка
    def _get_selected_id(self):
        current_item = self.ui.listWidget_artists.currentItem()
        if current_item:
            # Получение данных из пользовательской роли
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    # Инициация добавления нового исполнителя
    def _on_add_clicked(self):
        name = self.ui.edit_artist_name.text().strip()

        # Проверка заполненности поля ввода
        if not name:
            QMessageBox.warning(self, "Ошибка", "Имя исполнителя не может быть пустым.")
            return

        # Отправка сигнала контроллеру и очистка поля
        self.sig_add_artist.emit(name)
        self.ui.edit_artist_name.clear()

    # Инициация обновления данных существующего исполнителя
    def _on_update_clicked(self):
        artist_id = self._get_selected_id()

        # Проверка наличия выбранного элемента в списке
        if not artist_id:
            QMessageBox.warning(self, "Ошибка", "Выберите исполнителя из списка.")
            return

        new_name = self.ui.edit_artist_name.text().strip()

        # Проверка заполненности поля ввода
        if not new_name:
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым.")
            return

        # Отправка сигнала контроллеру
        self.sig_update_artist.emit(artist_id, new_name)

    # Инициация удаления исполнителя с запросом подтверждения
    def _on_delete_clicked(self):
        artist_id = self._get_selected_id()
        # Проверка наличия выбранного элемента в списке
        if not artist_id:
            QMessageBox.warning(self, "Ошибка", "Выберите исполнителя из списка.")
            return

        artist_name = self.ui.listWidget_artists.currentItem().text()

        # Вызов диалогового окна для подтверждения действия
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            f'Вы уверены, что хотите удалить "{artist_name}"?\nЭто удалит исполнителя из всех связанных треков.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        # Проверка результата и отправка сигнала контроллеру
        if reply == QMessageBox.StandardButton.Yes:
            self.sig_delete_artist.emit(artist_id)
            self.ui.edit_artist_name.clear()

    # Заполнение визуального списка исполнителей данными из базы
    def populate_list(self, artists: list):
        # Очистка старых элементов списка
        self.ui.listWidget_artists.clear()

        # Добавление новых элементов
        for artist_id, artist_name in artists:
            item = QListWidgetItem(artist_name)
            # Сохранение числового идентификатора внутри элемента списка
            item.setData(Qt.ItemDataRole.UserRole, artist_id)

            self.ui.listWidget_artists.addItem(item)
