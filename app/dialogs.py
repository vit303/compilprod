from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):
    """Диалоговое окно "О программе" """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title_label = QLabel("Текстовый редактор с поиском по регулярным выражениям")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #e8e8e8;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Информация
        info_text = QTextBrowser()
        info_text.setHtml("""
        <h3 style="color: #e8e8e8;">Лабораторные работы 1-4</h3>
        <p style="color: #e8e8e8;"><b>Версия:</b> 1.0.0</p>
        <p style="color: #e8e8e8;"><b>Разработчик:</b> Студент</p>
        <p style="color: #e8e8e8;"><b>Описание:</b></p>
        <ul style="color: #e8e8e8;">
            <li>ЛР1: Разработка текстового редактора с GUI</li>
            <li>ЛР2: Лексический анализатор</li>
            <li>ЛР3: Синтаксический анализатор</li>
            <li>ЛР4: Поиск по регулярным выражениям</li>
        </ul>
        
        <h3 style="color: #e8e8e8;">Регулярные выражения (ЛР4)</h3>
        <p style="color: #e8e8e8;"><b>1. Номер водительского удостоверения (РФ)</b><br>
        <code style="color: #0d7fff;">\\b[АВЕКМНОРСТУХ]{2}\\s?\\d{6}\\b</code><br>
        Примеры: ВА123456, СА 789012</p>
        
        <p style="color: #e8e8e8;"><b>2. ФИО на английском языке</b><br>
        <code style="color: #0d7fff;">\\b[A-Z][a-z]+(?:\\s+[A-Z][a-z]+){2}\\b</code><br>
        Примеры: Ivanov Ivan Ivanovich, Smith John Robert</p>
        
        <p style="color: #e8e8e8;"><b>3. Химический элемент (таблица Менделеева)</b><br>
        <code style="color: #0d7fff;">\\b(?:Hydrogen|Helium|...|Oganesson)\\b</code><br>
        Все 118 химических элементов</p>
        
        <h3 style="color: #e8e8e8;">Технологии</h3>
        <p style="color: #e8e8e8;">Python 3.8+, PyQt6, регулярные выражения</p>
        """)
        info_text.setStyleSheet("""
            QTextBrowser {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border: 1px solid #404040;
            }
        """)
        info_text.setOpenExternalLinks(True)
        layout.addWidget(info_text)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7fff;
                color: white;
                font-weight: bold;
                padding: 6px 15px;
                border-radius: 3px;
                border: 1px solid #0d7fff;
            }
            QPushButton:hover {
                background-color: #1084ff;
                border: 1px solid #1084ff;
            }
            QPushButton:pressed {
                background-color: #0a5fcf;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Стиль диалога
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
        """)