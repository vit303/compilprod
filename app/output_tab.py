# -*- coding: utf-8 -*-

"""
Компонент для отображения результатов и ошибок
Лабораторные работы 2-3
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class OutputTab(QWidget):
    """Вкладка для отображения результатов работы анализаторов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаём вкладки
        self.tab_widget = QTabWidget()
        
        # Вкладка "Результаты" (текстовый вывод)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        self.tab_widget.addTab(self.results_text, "Результаты")
        
        # Вкладка "Ошибки" (таблица)
        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(3)
        self.errors_table.setHorizontalHeaderLabels(["Строка", "Позиция", "Сообщение"])
        self.errors_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.errors_table.setAlternatingRowColors(True)
        self.tab_widget.addTab(self.errors_table, "Ошибки")
        
        # Вкладка "Поиск" (для совместимости с ЛР4, но результаты поиска теперь в search_module)
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(5)
        self.search_results.setHorizontalHeaderLabels(["№", "Найдено", "Строка", "Позиция", "Длина"])
        self.tab_widget.addTab(self.search_results, "Поиск")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def add_result(self, text):
        """Добавляет текст в результаты"""
        self.results_text.append(text)
    
    def clear_results(self):
        """Очищает результаты"""
        self.results_text.clear()
    
    def add_error(self, line, position, message):
        """Добавляет ошибку в таблицу"""
        row = self.errors_table.rowCount()
        self.errors_table.insertRow(row)
        
        self.errors_table.setItem(row, 0, QTableWidgetItem(str(line)))
        self.errors_table.setItem(row, 1, QTableWidgetItem(str(position)))
        self.errors_table.setItem(row, 2, QTableWidgetItem(message))
    
    def clear_errors(self):
        """Очищает таблицу ошибок"""
        self.errors_table.setRowCount(0)
    
    def get_errors(self):
        """Возвращает список ошибок"""
        errors = []
        for row in range(self.errors_table.rowCount()):
            line = self.errors_table.item(row, 0).text()
            position = self.errors_table.item(row, 1).text()
            message = self.errors_table.item(row, 2).text()
            errors.append({
                'line': int(line),
                'position': int(position),
                'message': message
            })
        return errors
    
    def set_current_tab(self, index):
        """Устанавливает текущую вкладку"""
        self.tab_widget.setCurrentIndex(index)