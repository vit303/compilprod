import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale
from app.main_window import MainWindow

def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    
    # Устанавливаем русскую локаль для корректного отображения
    locale = QLocale(QLocale.Language.Russian)
    QLocale.setDefault(locale)
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()