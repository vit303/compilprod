from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QTextFormat, QFont, QTextCursor, QSyntaxHighlighter
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCharFormat

class LineNumberArea(QWidget):
    """Область для отображения номеров строк"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class SyntaxHighlighter(QSyntaxHighlighter):
    """Подсветка синтаксиса для текста"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # Ключевые слова
        keywords = [
            'struct', 'pub', 'impl', 'trait', 'fn', 'let', 'mut', 
            'if', 'else', 'while', 'for', 'loop', 'match', 'return',
            'break', 'continue', 'type', 'enum', 'use', 'mod'
        ]
        
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))  # Синий цвет для ключевых слов
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        for word in keywords:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Типы данных
        types = [
            'i32', 'i64', 'u32', 'u64', 'f32', 'f64', 'bool', 
            'char', 'String', 'Vec', 'Option', 'Result'
        ]
        
        type_format = QTextCharFormat()
        type_format.setForeground(QColor(78, 201, 176))  # Зелёный цвет для типов
        type_format.setFontWeight(QFont.Weight.Bold)
        
        for word in types:
            pattern = r'\b' + word + r'\b'
            self.highlighting_rules.append((pattern, type_format))
        
        # Числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(181, 206, 168))  # Светло-зелёный для чисел
        self.highlighting_rules.append((r'\b\d+\b', number_format))
        
        # Строки
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(206, 145, 120))  # Оранжевый для строк
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        
        # Комментарии
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(87, 166, 74))  # Зелёный для комментариев
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'//[^\n]*', comment_format))
    
    def highlightBlock(self, text):
        for pattern, format_obj in self.highlighting_rules:
            import re
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class EditorTab(QPlainTextEdit):
    """Вкладка редактора текста с нумерацией строк"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Настройка шрифта
        font = QFont("Courier New", 10)
        self.setFont(font)
        
        # Настройка подсветки синтаксиса
        self.highlighter = SyntaxHighlighter(self.document())
        
        # Настройка номеров строк
        self.line_number_area = LineNumberArea(self)
        
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_line_number_area_width()
        self.highlight_current_line()
        
        # Дополнительные настройки
        self.setTabStopDistance(40)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    
    def line_number_area_width(self):
        """Вычисляет ширину области номеров строк"""
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_area_width(self):
        """Обновляет ширину области номеров строк"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """Обновляет область номеров строк при прокрутке"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    
    def line_number_area_paint_event(self, event):
        """Отрисовка номеров строк"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(41, 41, 41))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(160, 160, 160))
                painter.drawText(0, int(top), self.line_number_area.width() - 2, self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
    
    def highlight_current_line(self):
        """Подсвечивает текущую строку"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(51, 51, 80)  # Тёмный синий для текущей строки
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def get_text(self):
        """Возвращает текст из редактора"""
        return self.toPlainText()
    
    def set_text(self, text):
        """Устанавливает текст в редактор"""
        self.setPlainText(text)