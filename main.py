import sys
from PyQt6.QtWidgets import QApplication

from model import DatabaseManager, AudioTagEditor
from view import MainWindow
from controller import AppController


def main():
    # Создание базового объекта приложения PyQt6
    app = QApplication(sys.argv)

    # Инициализация компонентов слоя данных
    db_manager = DatabaseManager('library.db')
    tag_editor = AudioTagEditor()

    # Создание объекта главного графического окна
    main_window = MainWindow()

    # Инициализация контроллера и связывание логики с интерфейсом
    controller = AppController(
        view=main_window,
        db_manager=db_manager,
        tag_editor=tag_editor
    )

    # Отображение главного окна на экране пользователя
    main_window.show()

    # Запуск бесконечного цикла обработки событий и завершение работы
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
