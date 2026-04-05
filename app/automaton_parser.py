import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QLabel, QHeaderView,
    QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor


class State:
    START = 0
    FIRST_NAME_START = 1      # Начало первого слова (фамилия)
    FIRST_NAME_BODY = 2       # Тело первого слова
    SPACE_AFTER_FIRST = 3     # Пробел после первого слова
    SECOND_NAME_START = 4     # Начало второго слова (имя)
    SECOND_NAME_BODY = 5      # Тело второго слова
    SPACE_AFTER_SECOND = 6    # Пробел после второго слова
    THIRD_NAME_START = 7      # Начало третьего слова (отчество)
    THIRD_NAME_BODY = 8       # Тело третьего слова
    ACCEPT = 9                # Принимающее состояние
    ERROR = 10                # Состояние ошибки


class AutomatonParser:
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.current_state = State.START
        self.current_match_start = -1
        self.current_match_end = -1
        self.current_line = 0
        self.current_pos = 0
    
    def is_letter_uppercase(self, char):
        return 'A' <= char <= 'Z'
    
    def is_letter_lowercase(self, char):
        return 'a' <= char <= 'z'
    
    def is_letter(self, char):
        return self.is_letter_uppercase(char) or self.is_letter_lowercase(char)
    
    def is_space(self, char):
        return char == ' ' or char == '\t'
    
    def transition(self, char):
        if self.current_state == State.START:
            if self.is_letter_uppercase(char):
                self.current_match_start = self.current_pos
                return State.FIRST_NAME_START
            return State.START
        
        elif self.current_state == State.FIRST_NAME_START:
            if self.is_letter_lowercase(char):
                return State.FIRST_NAME_BODY
            return State.ERROR
        
        elif self.current_state == State.FIRST_NAME_BODY:
            if self.is_letter_lowercase(char):
                return State.FIRST_NAME_BODY
            elif self.is_space(char):
                return State.SPACE_AFTER_FIRST
            return State.ERROR
        
        elif self.current_state == State.SPACE_AFTER_FIRST:
            if self.is_letter_uppercase(char):
                return State.SECOND_NAME_START
            return State.ERROR
        
        elif self.current_state == State.SECOND_NAME_START:
            if self.is_letter_lowercase(char):
                return State.SECOND_NAME_BODY
            return State.ERROR
        
        elif self.current_state == State.SECOND_NAME_BODY:
            if self.is_letter_lowercase(char):
                return State.SECOND_NAME_BODY
            elif self.is_space(char):
                return State.SPACE_AFTER_SECOND
            return State.ERROR
        
        elif self.current_state == State.SPACE_AFTER_SECOND:
            if self.is_letter_uppercase(char):
                return State.THIRD_NAME_START
            return State.ERROR
        
        elif self.current_state == State.THIRD_NAME_START:
            if self.is_letter_lowercase(char):
                return State.THIRD_NAME_BODY
            return State.ERROR
        
        elif self.current_state == State.THIRD_NAME_BODY:
            if self.is_letter_lowercase(char):
                return State.THIRD_NAME_BODY
            elif self.is_space(char) or char == '\n' or char == '\0':
                self.current_match_end = self.current_pos
                return State.ACCEPT
            return State.ERROR
        
        return State.ERROR
    
    def parse(self, text):
        matches = []
        self.reset()
        
        text_with_end = text + '\0'
        
        for i, char in enumerate(text_with_end):
            self.current_pos = i
            
            if self.current_state == State.ACCEPT:
                matches.append({
                    'start': self.current_match_start,
                    'end': self.current_match_end,
                    'text': text[self.current_match_start:self.current_match_end]
                })
                self.reset()
                if char != '\0':
                    self.current_pos = i
                    self.current_state = self.transition(char)
                continue
            
            new_state = self.transition(char)
            
            if new_state == State.ERROR:
                self.reset()
                if self.is_letter_uppercase(char):
                    self.current_pos = i
                    self.current_state = self.transition(char)
            else:
                self.current_state = new_state
        
        return matches


class AutomatonParserWidget(QWidget):
    
    matches_found = pyqtSignal(int)
    
    def __init__(self, editor_tab=None):
        super().__init__()
        self.editor_tab = editor_tab
        self.automaton = AutomatonParser()
        self.current_matches = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        

        control_group = QGroupBox("Автоматный парсер имён")
        control_layout = QVBoxLayout()
        
        info_label = QLabel(
            "Конечный автомат для распознавания ФИО (Last First Middle)\n"
            "Формат: Заглавная буква + строчные, пробел, заглавная + строчные, пробел, заглавная + строчные"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        control_layout.addWidget(info_label)
        
        buttons_layout = QHBoxLayout()
        
        self.parse_btn = QPushButton("🔍 Распознать имена")
        self.parse_btn.clicked.connect(self.parse_names)
        self.parse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.clicked.connect(self.clear_results)
        
        buttons_layout.addWidget(self.parse_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        control_layout.addLayout(buttons_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        

        results_group = QGroupBox("Результаты распознавания")
        results_layout = QVBoxLayout()

        self.status_label = QLabel("Готов к распознаванию")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        results_layout.addWidget(self.status_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "№", "Найденное ФИО", "Строка", "Позиция", "Длина"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        viz_group = QGroupBox("Визуализация автомата")
        viz_layout = QVBoxLayout()
        
        self.viz_text = QTextEdit()
        self.viz_text.setReadOnly(True)
        self.viz_text.setMaximumHeight(150)
        self.viz_text.setPlainText(self.get_automaton_visualization())
        self.viz_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        viz_layout.addWidget(self.viz_text)
        
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        self.setLayout(layout)
    
    def get_automaton_visualization(self):

        return """
        Конечный автомат для распознавания ФИО:
        
        START --(Заглавная буква)--> FIRST_NAME_START --(Строчная буква)--> FIRST_NAME_BODY
        FIRST_NAME_BODY --(Строчная буква)--> FIRST_NAME_BODY
        FIRST_NAME_BODY --(Пробел)--> SPACE_AFTER_FIRST
        
        SPACE_AFTER_FIRST --(Заглавная буква)--> SECOND_NAME_START --(Строчная буква)--> SECOND_NAME_BODY
        SECOND_NAME_BODY --(Строчная буква)--> SECOND_NAME_BODY
        SECOND_NAME_BODY --(Пробел)--> SPACE_AFTER_SECOND
        
        SPACE_AFTER_SECOND --(Заглавная буква)--> THIRD_NAME_START --(Строчная буква)--> THIRD_NAME_BODY
        THIRD_NAME_BODY --(Строчная буква)--> THIRD_NAME_BODY
        THIRD_NAME_BODY --(Пробел/Конец строки)--> ACCEPT ✓
        
        Состояния: START (начало), ACCEPT (принято), ERROR (ошибка)
        """
    
    def get_absolute_position(self, lines, line_num, col_num):
        position = 0
        for i in range(line_num):
            position += len(lines[i]) + 1
        position += col_num
        return position
    
    def parse_names(self):
        if not self.editor_tab:
            self.status_label.setText("Редактор не доступен")
            return
        
        text = self.editor_tab.toPlainText()
        if not text.strip():
            self.status_label.setText("⚠️ Нет данных для распознавания. Введите текст в редакторе.")
            return
        

        self.clear_results()
        

        matches = self.automaton.parse(text)
        

        lines = text.split('\n')
        enriched_matches = []
        
        for match in matches:
            start_pos = match['start']
            line_num = 0
            col_num = start_pos
            
            for i, line in enumerate(lines):
                if col_num <= len(line):
                    line_num = i + 1
                    break
                col_num -= len(line) + 1
            
            enriched_matches.append({
                'text': match['text'],
                'line': line_num,
                'position': col_num + 1,
                'length': match['end'] - match['start'],
                'start_pos': match['start'],
                'end_pos': match['end']
            })
        
        self.display_results(enriched_matches)
        self.current_matches = enriched_matches

        self.highlight_matches(enriched_matches)
    
        self.matches_found.emit(len(enriched_matches))
    
    def display_results(self, matches):
        self.results_table.setRowCount(len(matches))
        
        for i, match in enumerate(matches):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            item_text = QTableWidgetItem(match['text'])
            item_text.setToolTip(f"Строка {match['line']}, позиция {match['position']}")
            self.results_table.setItem(i, 1, item_text)

            self.results_table.setItem(i, 2, QTableWidgetItem(str(match['line'])))
 
            self.results_table.setItem(i, 3, QTableWidgetItem(str(match['position'])))
     
            self.results_table.setItem(i, 4, QTableWidgetItem(str(match['length'])))

        count = len(matches)
        if count == 0:
            self.status_label.setText("🔍 Имена не найдены")
        elif count == 1:
            self.status_label.setText(f" Найдено {count} ФИО")
        elif 2 <= count <= 4:
            self.status_label.setText(f" Найдено {count} ФИО")
        else:
            self.status_label.setText(f"Найдено {count} ФИО")
    
    def highlight_matches(self, matches):
        if not self.editor_tab or not matches:
            return
        
        cursor = self.editor_tab.textCursor()
        saved_position = cursor.position()
        
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(144, 238, 144, 100)) 
        highlight_format.setForeground(QColor(0, 0, 0))
        
        cursor.select(QTextCursor.SelectionType.Document)
        
        # Применяем подсветку
        for match in matches:
            cursor.setPosition(match['start_pos'])
            cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
            cursor.mergeCharFormat(highlight_format)
        
        cursor.setPosition(saved_position)
        self.editor_tab.setTextCursor(cursor)
    
    def on_result_selected(self):
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_matches):
            match = self.current_matches[row]
            
            cursor = self.editor_tab.textCursor()
            cursor.setPosition(match['start_pos'])
            cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
            self.editor_tab.setTextCursor(cursor)
            self.editor_tab.setFocus()
            
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(50, 205, 50, 150))  # Ярко-зелёный
            cursor.mergeCharFormat(highlight_format)
            
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self.restore_highlight(match))
    
    def restore_highlight(self, match):
        if not self.editor_tab:
            return
        
        cursor = self.editor_tab.textCursor()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(144, 238, 144, 100))
        
        cursor.setPosition(match['start_pos'])
        cursor.setPosition(match['end_pos'], QTextCursor.MoveMode.KeepAnchor)
        cursor.mergeCharFormat(highlight_format)
    
    def clear_results(self):
        """Очищает результаты"""
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
        """Устанавливает редактор"""
        self.editor_tab = editor_tab