from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QHeaderView,
    QGroupBox,
    QTextEdit,
)

from app.expr_core import Parser, Quad, TokenType, build_rpn_and_eval, tokenize


class ExprAnalyzerWidget(QWidget):
    analysis_performed = pyqtSignal(dict)

    def __init__(self, editor_tab=None):
        super().__init__()
        self.editor_tab = editor_tab
        self.last_payload: Optional[Dict[str, Any]] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        control_group = QGroupBox("ЛР6: Лексер + рекурсивный спуск (E→TA)")
        control_layout = QVBoxLayout()

        info = QLabel(
            "Грамматика:\n"
            "E → TA\n"
            "A → ε | + TA | - TA\n"
            "T → FB\n"
            "B → ε | * FB | / FB | % FB\n"
            "F → num | id | (E)\n\n"
            "Тетрады и ПОЛИЗ строятся только для корректных строк.\n"
            "ПОЛИЗ+вычисление: только выражения из целых чисел (без id)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "color: #b0b0b0; font-size: 10px; padding: 6px; background-color: #2d2d2d; border: 1px solid #404040;"
        )
        control_layout.addWidget(info)

        buttons = QHBoxLayout()

        self.analyze_btn = QPushButton("⚙️ Проанализировать")
        self.analyze_btn.clicked.connect(self.analyze)
        self.analyze_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1976D2; }
            """
        )

        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #505050;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 3px;
                border: 1px solid #606060;
            }
            QPushButton:hover { background-color: #5a5a5a; border: 1px solid #707070; }
            QPushButton:pressed { background-color: #404040; }
            """
        )

        buttons.addWidget(self.analyze_btn)
        buttons.addWidget(self.clear_btn)
        buttons.addStretch()
        control_layout.addLayout(buttons)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        results_group = QGroupBox("Результаты")
        results_layout = QVBoxLayout()

        self.status_label = QLabel("Готов к анализу")
        self.status_label.setStyleSheet(
            "padding: 5px; background-color: #3a3a3a; color: #e8e8e8; border-radius: 3px; border: 1px solid #404040;"
        )
        results_layout.addWidget(self.status_label)

        self.quads_table = QTableWidget()
        self.quads_table.setColumnCount(4)
        self.quads_table.setHorizontalHeaderLabels(["op", "result", "arg1", "arg2"])
        self.quads_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.quads_table.setAlternatingRowColors(True)
        results_layout.addWidget(QLabel("Тетрады"))
        results_layout.addWidget(self.quads_table)

        self.rpn_text = QTextEdit()
        self.rpn_text.setReadOnly(True)
        self.rpn_text.setMaximumHeight(90)
        self.rpn_text.setStyleSheet("font-family: 'Courier New'; font-size: 10pt;")
        results_layout.addWidget(QLabel("ПОЛИЗ (RPN) и вычисление"))
        results_layout.addWidget(self.rpn_text)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        layout.addStretch()
        self.setLayout(layout)

    def set_editor(self, editor_tab) -> None:
        self.editor_tab = editor_tab

    def _get_source(self) -> str:
        if not self.editor_tab:
            return ""
        return self.editor_tab.toPlainText()

    def analyze(self) -> None:
        src = self._get_source()
        if not src.strip():
            self.status_label.setText("⚠️ Нет выражения: введите текст в редакторе.")
            return

        self.clear_results()

        tokens, lex_errors = tokenize(src)

        payload: Dict[str, Any] = {
            "source": src,
            "tokens": tokens,
            "lex_errors": lex_errors,
            "syn_errors": [],
            "sem_errors": [],
            "quads": [],
            "rpn": None,
            "rpn_value": None,
        }

        if lex_errors:
            self.status_label.setText(f"❌ Лексических ошибок: {len(lex_errors)}. Тетрады/ПОЛИЗ не строятся.")
            self.last_payload = payload
            self.analysis_performed.emit(payload)
            return

        parser = Parser(tokens)
        place = parser.parse()
        payload["syn_errors"] = parser.errors
        payload["quads"] = parser.quads

        if parser.errors or place is None:
            self.status_label.setText(f"❌ Синтаксических ошибок: {len(parser.errors)}. Тетрады/ПОЛИЗ не строятся.")
            self.last_payload = payload
            self.analysis_performed.emit(payload)
            return

        self._render_quads(parser.quads)

        rpn, rpn_errors, value = build_rpn_and_eval(tokens)
        payload["sem_errors"] = rpn_errors
        payload["rpn"] = rpn
        payload["rpn_value"] = value

        if rpn is None:
            self.rpn_text.setPlainText("ПОЛИЗ не построен (есть id или ошибки скобок).")
        else:
            if value is None:
                self.rpn_text.setPlainText(" ".join(rpn) + "\n\nЗначение: (не вычислено из-за ошибки)")
            else:
                self.rpn_text.setPlainText(" ".join(rpn) + f"\n\nЗначение: {value}")

        ok_msg = "✅ Выражение корректно. Построены тетрады"
        if rpn is not None and value is not None:
            ok_msg += ", ПОЛИЗ и значение."
        elif rpn is not None:
            ok_msg += " и ПОЛИЗ."
        else:
            ok_msg += "."
        self.status_label.setText(ok_msg)

        self.last_payload = payload
        self.analysis_performed.emit(payload)

    def _render_quads(self, quads: List[Quad]) -> None:
        self.quads_table.setRowCount(len(quads))
        for i, q in enumerate(quads):
            self.quads_table.setItem(i, 0, QTableWidgetItem(q.op))
            self.quads_table.setItem(i, 1, QTableWidgetItem(q.result))
            self.quads_table.setItem(i, 2, QTableWidgetItem(q.arg1))
            self.quads_table.setItem(i, 3, QTableWidgetItem(q.arg2))

    def clear_results(self) -> None:
        self.quads_table.setRowCount(0)
        self.rpn_text.clear()
        self.status_label.setText("Результаты очищены")
        self.last_payload = None

