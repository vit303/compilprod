import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMessageBox, QFileDialog, QApplication,
    QTabWidget, QStatusBar, QLabel, QToolBar, QMenuBar,
    QMenu, QPushButton
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QFont, QKeySequence

from app.editor_tab import EditorTab
from app.output_tab import OutputTab
from app.search_module import SearchModule
from app.automaton_parser import AutomatonParserWidget
from app.dialogs import AboutDialog


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.search_module = None
        self.automaton_parser = None
        self.output_tab = None
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.apply_styles()
    
    def setup_ui(self):
        """Настройка основного интерфейса"""
        self.setWindowTitle("Текстовый редактор с поиском по регулярным выражениям и автоматным парсером")
        self.setGeometry(100, 100, 1400, 800)
        
        # Создаём центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаём горизонтальный сплиттер для левой и правой панели
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ===== ЛЕВАЯ ПАНЕЛЬ =====
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Вкладки редактора
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.add_new_tab()  # Добавляем первую вкладку
        
        left_layout.addWidget(self.tab_widget)
        
        # ===== ПРАВАЯ ПАНЕЛЬ =====
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаём вкладки для правой панели
        self.right_tab_widget = QTabWidget()
        
        # Вкладка 1: Поиск по регулярным выражениям
        self.search_module = SearchModule(self.get_current_editor())
        self.right_tab_widget.addTab(self.search_module, "🔍 Регулярные выражения")
        
        # Вкладка 2: Автоматный парсер имён
        self.automaton_parser = AutomatonParserWidget(self.get_current_editor())
        self.right_tab_widget.addTab(self.automaton_parser, "🤖 Автоматный парсер")
        
        # Вкладка 3: Результаты анализа
        self.output_tab = OutputTab()
        self.right_tab_widget.addTab(self.output_tab, "📊 Результаты")
        
        right_layout.addWidget(self.right_tab_widget)
        
        # Добавляем панели в основной сплиттер
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(right_widget)
        
        # Устанавливаем пропорции (60% редактор, 40% правая панель)
        self.main_splitter.setSizes([800, 600])
        
        main_layout.addWidget(self.main_splitter)
        
        # Подключаем сигналы поиска для обновления вкладки результатов
        self.search_module.matches_found.connect(self.on_search_complete)
        self.automaton_parser.matches_found.connect(self.on_automaton_complete)
    
    def setup_menu(self):
        """Настройка главного меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("Новый", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Открыть...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Сохранить как...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Правка
        edit_menu = menubar.addMenu("Правка")
        
        undo_action = QAction("Отменить", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(lambda: self.get_current_editor().undo())
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Повторить", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(lambda: self.get_current_editor().redo())
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction("Вырезать", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(lambda: self.get_current_editor().cut())
        edit_menu.addAction(cut_action)
        
        copy_action = QAction("Копировать", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(lambda: self.get_current_editor().copy())
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Вставить", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self.get_current_editor().paste())
        edit_menu.addAction(paste_action)
        
        # Меню Поиск
        search_menu = menubar.addMenu("Поиск")
        
        find_action = QAction("Найти (Regex)", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.focus_search)
        search_menu.addAction(find_action)
        
        automaton_action = QAction("Распознать имена (Автомат)", self)
        automaton_action.setShortcut("Ctrl+G")
        automaton_action.triggered.connect(self.run_automaton_parser)
        search_menu.addAction(automaton_action)
        
        search_menu.addSeparator()
        
        clear_action = QAction("Очистить результаты", self)
        clear_action.setShortcut("Ctrl+Shift+F")
        clear_action.triggered.connect(self.clear_search_results)
        search_menu.addAction(clear_action)
        
        search_menu.addSeparator()
        
        # Примеры для тестирования
        examples_menu = search_menu.addMenu("Тестовые примеры")
        
        license_example = QAction("Вставить пример ВУ", self)
        license_example.triggered.connect(self.insert_license_example)
        examples_menu.addAction(license_example)
        
        name_example = QAction("Вставить пример ФИО (Regex)", self)
        name_example.triggered.connect(self.insert_name_example)
        examples_menu.addAction(name_example)
        
        element_example = QAction("Вставить пример элементов", self)
        element_example.triggered.connect(self.insert_element_example)
        examples_menu.addAction(element_example)
        
        examples_menu.addSeparator()
        
        automaton_example = QAction("Вставить пример для автомата", self)
        automaton_example.triggered.connect(self.insert_automaton_example)
        examples_menu.addAction(automaton_example)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Настройка панели инструментов"""
        toolbar = self.addToolBar("Главная")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        
        # Создаём действия для панели инструментов
        new_action = QAction("📄 Новый", self)
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)
        
        open_action = QAction("📂 Открыть", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction("💾 Сохранить", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        undo_action = QAction("↩️ Отменить", self)
        undo_action.triggered.connect(lambda: self.get_current_editor().undo())
        toolbar.addAction(undo_action)
        
        redo_action = QAction("↪️ Повторить", self)
        redo_action.triggered.connect(lambda: self.get_current_editor().redo())
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        cut_action = QAction("✂️ Вырезать", self)
        cut_action.triggered.connect(lambda: self.get_current_editor().cut())
        toolbar.addAction(cut_action)
        
        copy_action = QAction("📋 Копировать", self)
        copy_action.triggered.connect(lambda: self.get_current_editor().copy())
        toolbar.addAction(copy_action)
        
        paste_action = QAction("📌 Вставить", self)
        paste_action.triggered.connect(lambda: self.get_current_editor().paste())
        toolbar.addAction(paste_action)
        
        toolbar.addSeparator()
        
        find_action = QAction("🔍 Найти (Regex)", self)
        find_action.triggered.connect(self.focus_search)
        toolbar.addAction(find_action)
        
        automaton_action = QAction("🤖 Распознать имена", self)
        automaton_action.triggered.connect(self.run_automaton_parser)
        toolbar.addAction(automaton_action)
        
        clear_action = QAction("🗑 Очистить", self)
        clear_action.triggered.connect(self.clear_search_results)
        toolbar.addAction(clear_action)
    
    def setup_statusbar(self):
        """Настройка строки состояния"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.cursor_pos_label = QLabel("Строка: 1, Колонка: 1")
        self.statusbar.addWidget(self.cursor_pos_label)
        
        self.char_count_label = QLabel("Символов: 0")
        self.statusbar.addWidget(self.char_count_label)
        
        self.word_count_label = QLabel("Слов: 0")
        self.statusbar.addWidget(self.word_count_label)
        
        # Обновляем информацию о курсоре при его перемещении
        QTimer.singleShot(100, self.update_status_info)
    
    def apply_styles(self):
        """Применение стилей CSS"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QPlainTextEdit {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border: 1px solid #404040;
                font-family: 'Courier New';
                font-size: 10pt;
                selection-background-color: #404080;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            QTabBar {
                background-color: #1e1e1e;
                border-bottom: 2px solid #404040;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #b0b0b0;
                padding: 6px 15px;
                margin-right: 2px;
                border: 1px solid #404040;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border-bottom: 2px solid #0d7fff;
            }
            QTabBar::tab:hover {
                background-color: #353535;
                color: #e8e8e8;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                spacing: 5px;
                padding: 3px;
            }
            QToolBar QToolButton {
                color: #e8e8e8;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid transparent;
            }
            QToolBar QToolButton:hover {
                background-color: #3a3a3a;
                border: 1px solid #0d7fff;
            }
            QToolBar QToolButton:pressed {
                background-color: #0d7fff;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border-top: 1px solid #404040;
            }
            QStatusBar QLabel {
                color: #e8e8e8;
            }
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #404040;
                alternate-background-color: #353535;
                selection-background-color: #0d7fff;
            }
            QTableWidget::item {
                color: #e8e8e8;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0d7fff;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #e8e8e8;
                padding: 4px;
                border: 1px solid #404040;
            }
            QGroupBox {
                color: #e8e8e8;
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #e8e8e8;
            }
            QComboBox {
                background-color: #3a3a3a;
                color: #e8e8e8;
                border: 1px solid #404040;
                padding: 4px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #e8e8e8;
                selection-background-color: #0d7fff;
                border: 1px solid #404040;
            }
            QCheckBox {
                color: #e8e8e8;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3a3a3a;
                border: 1px solid #404040;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background-color: #0d7fff;
                border: 1px solid #0d7fff;
                border-radius: 2px;
            }
            QMenuBar {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border-bottom: 1px solid #404040;
            }
            QMenuBar::item:selected {
                background-color: #0d7fff;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border: 1px solid #404040;
            }
            QMenu::item:selected {
                background-color: #0d7fff;
                color: #ffffff;
            }
            QMenu::separator {
                background-color: #404040;
                height: 1px;
                margin: 2px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #e8e8e8;
                border: 1px solid #404040;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #777;
            }
        """)
    
    def add_new_tab(self, text=""):
        """Добавляет новую вкладку с редактором"""
        editor = EditorTab()
        editor.setPlainText(text)
        
        # Подключаем сигналы для обновления статуса
        editor.cursorPositionChanged.connect(self.update_status_info)
        editor.textChanged.connect(self.update_status_info)
        
        index = self.tab_widget.addTab(editor, f"Новый документ {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(index)
        
        # Обновляем модули поиска
        self.update_search_modules_editor()
        
        return editor
    
    def get_current_editor(self):
        """Возвращает текущий активный редактор"""
        if self.tab_widget and self.tab_widget.currentWidget():
            return self.tab_widget.currentWidget()
        return None
    
    def update_search_modules_editor(self):
        """Обновляет редактор во всех модулях поиска"""
        editor = self.get_current_editor()
        if self.search_module:
            self.search_module.set_editor(editor)
        if self.automaton_parser:
            self.automaton_parser.set_editor(editor)
    
    def close_tab(self, index):
        """Закрывает вкладку"""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            # Если осталась последняя вкладка, просто очищаем её
            editor = self.get_current_editor()
            if editor:
                editor.clear()
        
        # Обновляем модули поиска
        self.update_search_modules_editor()
    
    def new_file(self):
        """Создаёт новый файл"""
        self.add_new_tab()
    
    def open_file(self):
        """Открывает файл"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                editor = self.add_new_tab(content)
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(file_path))
                editor.current_file = file_path
                
                self.statusbar.showMessage(f"Файл открыт: {file_path}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")
    
    def save_file(self):
        """Сохраняет текущий файл"""
        editor = self.get_current_editor()
        if not editor:
            return
        
        if hasattr(editor, 'current_file') and editor.current_file:
            try:
                with open(editor.current_file, 'w', encoding='utf-8') as file:
                    file.write(editor.toPlainText())
                
                self.statusbar.showMessage(f"Сохранено: {editor.current_file}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Сохраняет файл с новым именем"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл", "", "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if file_path:
            editor = self.get_current_editor()
            if not editor:
                return
                
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(editor.toPlainText())
                
                editor.current_file = file_path
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(file_path))
                self.statusbar.showMessage(f"Сохранено: {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")
    
    def focus_search(self):
        """Фокусирует поле поиска"""
        if self.search_module:
            self.right_tab_widget.setCurrentIndex(0)  # Переключаемся на вкладку Regex
            self.search_module.search_type.setFocus()
    
    def run_automaton_parser(self):
        """Запускает автоматный парсер"""
        if self.automaton_parser:
            self.right_tab_widget.setCurrentIndex(1)  # Переключаемся на вкладку автомата
            self.automaton_parser.parse_names()
    
    def clear_search_results(self):
        """Очищает результаты поиска"""
        if self.search_module:
            self.search_module.clear_results()
        if self.automaton_parser:
            self.automaton_parser.clear_results()
        if self.output_tab:
            self.output_tab.clear_results()
            self.output_tab.clear_errors()
    
    def on_search_complete(self, matches_count):
        """Обработчик завершения поиска по регулярным выражениям"""
        if self.output_tab:
            self.output_tab.add_result(f"[Regex] Поиск завершён. Найдено совпадений: {matches_count}")
            if matches_count > 0:
                self.output_tab.set_current_tab(0)
    
    def on_automaton_complete(self, matches_count):
        """Обработчик завершения автоматного парсера"""
        if self.output_tab:
            self.output_tab.add_result(f"[Автомат] Распознавание завершено. Найдено ФИО: {matches_count}")
            if matches_count > 0:
                self.output_tab.set_current_tab(0)
    
    def insert_license_example(self):
        """Вставляет пример для поиска водительских удостоверений"""
        example = """Примеры номеров водительских удостоверений РФ:

✅ Корректные (должны находиться):
ВА123456
СА 789012
МР456789
НО123456
ТС987654
АА 000000

❌ Некорректные (не должны находиться):
АБ123456 (недопустимые буквы)
ВА12345 (5 цифр)
ВА1234567 (7 цифр)
"""
        self.get_current_editor().insertPlainText(example)
    
    def insert_name_example(self):
        """Вставляет пример для поиска ФИО на английском (Regex)"""
        example = """Примеры ФИО на английском языке (для Regex):

✅ Корректные (должны находиться):
Ivanov Ivan Ivanovich
Petrova Maria Sergeevna
Smith John Robert
Johnson Emily Kate
Williams Michael David

❌ Некорректные (не должны находиться):
ivanov ivan (строчные буквы)
Ivanov Ivan (только 2 слова)
IVANOV IVAN IVANOVICH (все заглавные)
"""
        self.get_current_editor().insertPlainText(example)
    
    def insert_element_example(self):
        """Вставляет пример для поиска химических элементов"""
        example = """Примеры химических элементов (таблица Менделеева):

✅ Корректные (должны находиться):
Hydrogen and Oxygen combine to make Water.
Carbon is the basis of organic chemistry.
Gold (Au) is a precious metal.
Uranium is used in nuclear reactors.
Helium is a noble gas.
Iron and Copper are transition metals.

❌ Некорректные (не должны находиться):
Water (не элемент)
Air (не элемент)
Hydro (неполное название)
"""
        self.get_current_editor().insertPlainText(example)
    
    def insert_automaton_example(self):
        """Вставляет пример для автоматного парсера имён"""
        example = """Примеры для автоматного парсера имён (конечный автомат):

✅ Корректные ФИО (должны распознаваться):
Ivanov Ivan Ivanovich
Petrova Maria Sergeevna
Smith John Robert
Johnson Emily Kate
Williams Michael David
Brown Sarah Elizabeth
Jones James William
Garcia Patricia Ann

❌ Некорректные ФИО (не должны распознаваться):
ivanov ivan ivanovich (все строчные)
IVANOV IVAN IVANOVICH (все заглавные)
Ivanov Ivan (только 2 слова)
Ivanov I Ivanovich (инициал вместо имени)
Ivanov  Ivan  Ivanovich (двойные пробелы)
IvanovIvanIvanovich (без пробелов)

📊 Автомат распознаёт только имена в формате:
Заглавная буква + строчные + пробел + Заглавная + строчные + пробел + Заглавная + строчные
"""
        self.get_current_editor().insertPlainText(example)
    
    def show_about(self):
        """Показывает диалог о программе"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def update_status_info(self):
        """Обновляет информацию в строке состояния"""
        editor = self.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            
            text = editor.toPlainText()
            chars = len(text)
            words = len(text.split()) if text.strip() else 0
            
            self.cursor_pos_label.setText(f"Строка: {line}, Колонка: {col}")
            self.char_count_label.setText(f"Символов: {chars}")
            self.word_count_label.setText(f"Слов: {words}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        reply = QMessageBox.question(
            self, "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()