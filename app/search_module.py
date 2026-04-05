import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QLabel, QHeaderView, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor


class SearchModule(QWidget):
    """Модуль поиска с регулярными выражениями"""
    
    # Сигнал для уведомления о найденных совпадениях
    matches_found = pyqtSignal(int)
    
    def __init__(self, editor_tab=None):
        super().__init__()
        self.editor_tab = editor_tab
        self.current_matches = []
        self.current_highlighter = None
        self.setup_ui()
        self.setup_regex_patterns()
    
    def setup_ui(self):
        """Создание интерфейса поиска"""
        layout = QVBoxLayout()
        
        # Группа выбора типа поиска
        search_group = QGroupBox("Параметры поиска")
        search_layout = QVBoxLayout()
        
        # Выпадающий список типов поиска
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип поиска:"))
        self.search_type = QComboBox()
        self.search_type.addItems([
            "Номер водительского удостоверения (РФ)",
            "ФИО на английском языке",
            "Химический элемент (таблица Менделеева)",
            "Пользовательское выражение"
        ])
        type_layout.addWidget(self.search_type)
        type_layout.addStretch()
        search_layout.addLayout(type_layout)
        
        # Поле для пользовательского выражения
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Регулярное выражение:"))
        self.custom_regex = QComboBox()
        self.custom_regex.setEditable(True)
        self.custom_regex.addItems([
            r"\b\d{3}-\d{3}-\d{4}\b",  # Телефон
            r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b",  # Email
            r"\bhttps?://[\w\.-]+/\S*\b",  # URL
            r"\b\d{4}-\d{2}-\d{2}\b",  # Дата
        ])
        custom_layout.addWidget(self.custom_regex)
        search_layout.addLayout(custom_layout)
        
        # Настройки поиска
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Учитывать регистр")
        self.multiline_mode = QCheckBox("Многострочный режим")
        self.multiline_mode.setChecked(True)
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.multiline_mode)
        options_layout.addStretch()
        search_layout.addLayout(options_layout)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.search_btn = QPushButton("🔍 Найти")
        self.search_btn.clicked.connect(self.perform_search)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7fff;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
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
        
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
                border: 1px solid #606060;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
                border: 1px solid #707070;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """)
        
        buttons_layout.addWidget(self.search_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        search_layout.addLayout(buttons_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Группа результатов
        results_group = QGroupBox("Результаты поиска")
        results_layout = QVBoxLayout()
        
        # Статусная метка
        self.status_label = QLabel("Готов к поиску")
        self.status_label.setStyleSheet("padding: 5px; background-color: #3a3a3a; color: #e8e8e8; border-radius: 3px; border: 1px solid #404040;")
        results_layout.addWidget(self.status_label)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "№", "Найденная подстрока", "Строка", "Позиция", "Длина"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
    
    def setup_regex_patterns(self):
        """Определение регулярных выражений для всех типов поиска"""
        
        # 1. Номер водительского удостоверения (Россия)
        # Формат: 2 буквы + 6 цифр (ВА123456, СА 789012)
        # Допустимые буквы: А, В, Е, К, М, Н, О, Р, С, Т, У, Х
        self.license_pattern = r'\b[АВЕКМНОРСТУХ]{2}\s?\d{6}\b'
        
        # 2. ФИО на английском языке
        # Формат: Last Name, First Name Middle Name
        # Каждое слово начинается с заглавной буквы, остальные строчные
        self.fullname_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2}\b'
        
        # 3. Химические элементы (полный список из 118 элементов)
        # Создаём паттерн со всеми названиями элементов
        elements = [
            # Период 1
            'Hydrogen', 'Helium',
            # Период 2
            'Lithium', 'Beryllium', 'Boron', 'Carbon', 'Nitrogen', 'Oxygen', 'Fluorine', 'Neon',
            # Период 3
            'Sodium', 'Magnesium', 'Aluminum', 'Silicon', 'Phosphorus', 'Sulfur', 'Chlorine', 'Argon',
            # Период 4
            'Potassium', 'Calcium', 'Scandium', 'Titanium', 'Vanadium', 'Chromium', 'Manganese',
            'Iron', 'Cobalt', 'Nickel', 'Copper', 'Zinc', 'Gallium', 'Germanium', 'Arsenic',
            'Selenium', 'Bromine', 'Krypton',
            # Период 5
            'Rubidium', 'Strontium', 'Yttrium', 'Zirconium', 'Niobium', 'Molybdenum', 'Technetium',
            'Ruthenium', 'Rhodium', 'Palladium', 'Silver', 'Cadmium', 'Indium', 'Tin', 'Antimony',
            'Tellurium', 'Iodine', 'Xenon',
            # Период 6
            'Cesium', 'Barium', 'Lanthanum', 'Cerium', 'Praseodymium', 'Neodymium', 'Promethium',
            'Samarium', 'Europium', 'Gadolinium', 'Terbium', 'Dysprosium', 'Holmium', 'Erbium',
            'Thulium', 'Ytterbium', 'Lutetium', 'Hafnium', 'Tantalum', 'Tungsten', 'Rhenium',
            'Osmium', 'Iridium', 'Platinum', 'Gold', 'Mercury', 'Thallium', 'Lead', 'Bismuth',
            'Polonium', 'Astatine', 'Radon',
            # Период 7
            'Francium', 'Radium', 'Actinium', 'Thorium', 'Protactinium', 'Uranium', 'Neptunium',
            'Plutonium', 'Americium', 'Curium', 'Berkelium', 'Californium', 'Einsteinium',
            'Fermium', 'Mendelevium', 'Nobelium', 'Lawrencium', 'Rutherfordium', 'Dubnium',
            'Seaborgium', 'Bohrium', 'Hassium', 'Meitnerium', 'Darmstadtium', 'Roentgenium',
            'Copernicium', 'Nihonium', 'Flerovium', 'Moscovium', 'Livermorium', 'Tennessine', 'Oganesson'
        ]
        
        # Сортируем по длине (от длинных к коротким) для корректного поиска
        elements.sort(key=len, reverse=True)
        self.element_pattern = r'\b(?:' + '|'.join(elements) + r')\b'
    
    def get_regex_flags(self):
        """Получение флагов регулярного выражения"""
        flags = 0
        if not self.case_sensitive.isChecked():
            flags |= re.IGNORECASE
        if self.multiline_mode.isChecked():
            flags |= re.MULTILINE
        return flags
    
    def get_current_pattern(self):
        """Возвращает текущее регулярное выражение в зависимости от выбранного типа"""
        search_type = self.search_type.currentText()
        
        if search_type == "Номер водительского удостоверения (РФ)":
            return self.license_pattern
        elif search_type == "ФИО на английском языке":
            return self.fullname_pattern
        elif search_type == "Химический элемент (таблица Менделеева)":
            return self.element_pattern
        elif search_type == "Пользовательское выражение":
            return self.custom_regex.currentText()
        
        return self.license_pattern
    
    def perform_search(self):
        """Выполняет поиск по текущему тексту"""
        if not self.editor_tab:
            self.status_label.setText("❌ Редактор не доступен")
            return
            
        text = self.editor_tab.toPlainText()
        if not text.strip():
            self.status_label.setText("⚠️ Нет данных для поиска. Введите текст в редакторе.")
            return
            
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Получаем паттерн и флаги
        pattern = self.get_current_pattern()
        flags = self.get_regex_flags()
        
        try:
            # Компилируем регулярное выражение
            regex = re.compile(pattern, flags)
            
            # Выполняем поиск
            matches = []
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for match in regex.finditer(line):
                    matches.append({
                        'text': match.group(),
                        'line': line_num,
                        'position': match.start() + 1,  # +1 для человеко-читаемой позиции
                        'length': match.end() - match.start(),
                        'start_pos': self.get_absolute_position(lines, line_num - 1, match.start()),
                        'end_pos': self.get_absolute_position(lines, line_num - 1, match.end()),
                        'line_text': line
                    })
            
            # Отображаем результаты
            self.display_results(matches)
            self.current_matches = matches
            
            # Подсвечиваем все совпадения
            self.highlight_matches(matches)
            
            # Отправляем сигнал о количестве найденных совпадений
            self.matches_found.emit(len(matches))
            
        except re.error as e:
            self.status_label.setText(f"❌ Ошибка в регулярном выражении: {e}")
        except Exception as e:
            self.status_label.setText(f"❌ Ошибка при поиске: {e}")
    
    def get_absolute_position(self, lines, line_num, col_num):
        """Вычисляет абсолютную позицию в тексте по номеру строки и колонки"""
        position = 0
        for i in range(line_num):
            position += len(lines[i]) + 1  # +1 для символа новой строки
        position += col_num
        return position
    
    def display_results(self, matches):
        """Отображает результаты в таблице"""
        self.results_table.setRowCount(len(matches))
        
        for i, match in enumerate(matches):
            # Номер по порядку
            self.results_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            # Найденная подстрока
            item_text = QTableWidgetItem(match['text'])
            item_text.setToolTip(f"Найдено в строке {match['line']}")
            self.results_table.setItem(i, 1, item_text)
            # Строка
            self.results_table.setItem(i, 2, QTableWidgetItem(str(match['line'])))
            # Позиция
            self.results_table.setItem(i, 3, QTableWidgetItem(str(match['position'])))
            # Длина
            self.results_table.setItem(i, 4, QTableWidgetItem(str(match['length'])))
        
        # Обновляем статус
        count = len(matches)
        if count == 0:
            self.status_label.setText("🔍 Совпадений не найдено")
        elif count == 1:
            self.status_label.setText(f"✅ Найдено {count} совпадение")
        elif 2 <= count <= 4:
            self.status_label.setText(f"✅ Найдено {count} совпадения")
        else:
            self.status_label.setText(f"✅ Найдено {count} совпадений")
    
    def highlight_matches(self, matches):
        """Подсвечивает все найденные совпадения в тексте"""
        if not self.editor_tab or not matches:
            return
        
        # Сохраняем текущую позицию курсора
        cursor = self.editor_tab.textCursor()
        saved_position = cursor.position()
        
        # Создаём формат для подсветки
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0, 100))  # Жёлтый с прозрачностью
        highlight_format.setForeground(QColor(0, 0, 0))
        
        # Очищаем предыдущую подсветку
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        # Применяем подсветку к каждому совпадению
        for match in matches:
            cursor.setPosition(match['start_pos'])
            cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(highlight_format)
        
        # Восстанавливаем позицию курсора
        cursor.setPosition(saved_position)
        self.editor_tab.setTextCursor(cursor)
    
    def on_result_selected(self):
        """Обработчик выбора строки в таблице результатов"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        # Получаем индекс выбранной строки
        row = selected_rows[0].row()
        if row < len(self.current_matches):
            match = self.current_matches[row]
            
            # Перемещаем курсор к выбранному совпадению
            cursor = self.editor_tab.textCursor()
            cursor.setPosition(match['start_pos'])
            cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
            self.editor_tab.setTextCursor(cursor)
            self.editor_tab.setFocus()
            
            # Временно подсвечиваем выбранный результат ярче
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(255, 165, 0, 150))  # Оранжевый
            cursor.mergeCharFormat(highlight_format)
            
            # Сбрасываем подсветку через 1 секунду
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.restore_highlight(match))
    
    def restore_highlight(self, match):
        """Восстанавливает обычную подсветку для выбранного элемента"""
        if not self.editor_tab:
            return
        
        cursor = self.editor_tab.textCursor()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(255, 255, 0, 100))
        
        cursor.setPosition(match['start_pos'])
        cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
        cursor.mergeCharFormat(highlight_format)
    
    def clear_results(self):
        """Очищает все результаты и подсветку"""
        self.results_table.setRowCount(0)
        self.status_label.setText("Результаты очищены")
        self.current_matches = []
        
        # Очищаем подсветку
        if self.editor_tab:
            cursor = self.editor_tab.textCursor()
            saved_position = cursor.position()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.setCharFormat(QTextCharFormat())
            cursor.setPosition(saved_position)
            self.editor_tab.setTextCursor(cursor)
    
    def set_editor(self, editor_tab):
        """Устанавливает редактор для поиска"""
        self.editor_tab = editor_tab