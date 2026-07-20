# gui_qt.py
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QTabWidget, QLabel, QDialog, QLineEdit, QTextEdit,
                             QMessageBox, QComboBox, QHeaderView, QSystemTrayIcon,
                             QMenu, QDesktopWidget, QCheckBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from db import Database
from game import Game

# ------------------------------------------------------------
# Глобальные стили – мягкая тёмная тема
# ------------------------------------------------------------
STYLE = """
QMainWindow {
    background-color: #1c1c1c;
}
QLabel {
    color: #d0d0d0;
    font-family: "Segoe UI", "Ubuntu", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: none;
    background: #1c1c1c;
}
QTabBar::tab {
    background: #2a2a2a;
    color: #a0a0a0;
    padding: 8px 18px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 2px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #3a5a7a;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background: #333333;
}
QTableWidget {
    background-color: #222222;
    color: #d0d0d0;
    gridline-color: #333333;
    alternate-background-color: #282828;
    selection-background-color: #3a5a7a;
    selection-color: #ffffff;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}
QTableWidget::item {
    background-color: #222222;
    color: #d0d0d0;
}
QTableWidget::item:selected {
    background-color: #3a5a7a;
    color: #ffffff;
}
QTableWidget::item:alternate {
    background-color: #282828;
}
QHeaderView::section {
    background-color: #2a2a2a;
    color: #b0b0b0;
    padding: 6px;
    border: none;
    font-weight: bold;
}
QPushButton {
    background-color: #3a5a7a;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 7px 16px;
    font-weight: bold;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #4a6a8a;
}
QPushButton:pressed {
    background-color: #2a4a6a;
}
QPushButton:disabled {
    background-color: #444444;
    color: #777777;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #2a2a2a;
    color: #d0d0d0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 5px;
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #4a7a9a;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: none;
}
QDialog {
    background-color: #1c1c1c;
}
QMenu {
    background-color: #2a2a2a;
    color: #d0d0d0;
    border: 1px solid #3a3a3a;
}
QMenu::item:selected {
    background-color: #3a5a7a;
}
"""

class App(QMainWindow):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.db = self.game.db
        self.setWindowTitle("Life RPG")
        self.setGeometry(100, 100, 950, 650)
        self.center_window()
        self.setStyleSheet(STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.stats_label = QLabel()
        self.stats_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.stats_label.setStyleSheet("background-color: #2a2a2a; border-radius: 6px; padding: 10px;")
        layout.addWidget(self.stats_label)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.quests_tab = QWidget()
        self.tabs.addTab(self.quests_tab, "Квесты")
        self.build_quests_tab()

        self.penalties_tab = QWidget()
        self.tabs.addTab(self.penalties_tab, "Наказания")
        self.build_penalties_tab()

        self.history_tab = QWidget()
        self.tabs.addTab(self.history_tab, "История")
        self.build_history_tab()

        self.create_tray()
        self.update_all()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def create_tray(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(58, 90, 122))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Segoe UI", 26, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "R")
        painter.end()
        icon = QIcon(pixmap)
        self.tray.setIcon(icon)
        self.tray.setToolTip("Life RPG")

        menu = QMenu()
        show_action = menu.addAction("Показать окно")
        show_action.triggered.connect(self.show_window)
        quit_action = menu.addAction("Выйти")
        quit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def update_stats(self):
        p = self.game.player
        text = (f"Уровень: {p['level']}    Опыт: {p['experience']}    "
                f"Сила: {p['strength']}    Интеллект: {p['intelligence']}    "
                f"Энергия: {p['energy']}")
        self.stats_label.setText(text)

    def update_all(self):
        self.game.refresh_player()
        self.update_stats()
        self.update_quests_table()
        self.update_penalties_table()
        self.update_history_table()

    @staticmethod
    def _make_item(text, bg_color="#222222", fg_color="#d0d0d0"):
        item = QTableWidgetItem(str(text))
        item.setBackground(QColor(bg_color))
        item.setForeground(QColor(fg_color))
        return item

    # ------ Квесты ------
    def build_quests_tab(self):
        layout = QVBoxLayout(self.quests_tab)
        layout.setSpacing(10)

        btn_add = QPushButton("Добавить квест")
        btn_add.clicked.connect(self.add_quest_dialog)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        self.quests_table = QTableWidget()
        self.quests_table.setColumnCount(7)
        self.quests_table.setHorizontalHeaderLabels(["ID", "Название", "Тип", "Сложность", "Награда (опыт)", "Штраф", "Повторение"])
        self.quests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.quests_table.setAlternatingRowColors(True)
        self.quests_table.verticalHeader().setVisible(False)
        layout.addWidget(self.quests_table)

        btn_frame = QHBoxLayout()
        btn_complete = QPushButton("Выполнить")
        btn_fail = QPushButton("Провалить")
        btn_delete = QPushButton("Удалить")
        btn_refresh = QPushButton("Обновить")
        btn_complete.clicked.connect(self.complete_quest)
        btn_fail.clicked.connect(self.fail_quest)
        btn_delete.clicked.connect(self.delete_quest)
        btn_refresh.clicked.connect(self.update_quests_table)
        btn_frame.addWidget(btn_complete)
        btn_frame.addWidget(btn_fail)
        btn_frame.addWidget(btn_delete)
        btn_frame.addWidget(btn_refresh)
        btn_frame.addStretch()
        layout.addLayout(btn_frame)

    def update_quests_table(self):
        self.quests_table.setRowCount(0)
        quests = self.db.get_active_quests()
        self.quests_table.setRowCount(len(quests))
        for i, q in enumerate(quests):
            self.quests_table.setItem(i, 0, self._make_item(q['id']))
            self.quests_table.setItem(i, 1, self._make_item(q['title']))
            self.quests_table.setItem(i, 2, self._make_item(q['type']))
            self.quests_table.setItem(i, 3, self._make_item(q['difficulty']))
            self.quests_table.setItem(i, 4, self._make_item(q['reward_exp']))
            self.quests_table.setItem(i, 5, self._make_item(q['penalty_exp']))
            # Формируем текст повторения
            if q['recurring']:
                rule = q['recurrence_rule']
                if not rule or rule == 'daily':
                    text = "Ежедневно"
                elif rule.startswith('weekly:'):
                    days = rule.split(':')[1]
                    day_names = {1:'Пн',2:'Вт',3:'Ср',4:'Чт',5:'Пт',6:'Сб',7:'Вс'}
                    days_list = [day_names.get(int(d.strip()), d) for d in days.split(',') if d.strip().isdigit()]
                    text = "По " + ', '.join(days_list)
                elif rule.startswith('monthly:'):
                    day_num = rule.split(':')[1]
                    text = f"Ежемесячно {day_num}-го числа"
                else:
                    text = rule
            else:
                text = "—"
            self.quests_table.setItem(i, 6, self._make_item(text))

    def delete_quest(self):
        qid = self.get_selected_quest()
        if qid is None:
            return
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот квест безвозвратно?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_quest(qid)
            self.update_all()
            QMessageBox.information(self, "Удалено", "Квест удалён")

    # ---------- ДИАЛОГ ДОБАВЛЕНИЯ КВЕСТА С ПОДДЕРЖКОЙ РЕГУЛЯРНЫХ ----------
    def add_quest_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый квест")
        dialog.setModal(True)
        dialog.setStyleSheet(STYLE)
        layout = QVBoxLayout(dialog)

        fields = {}
        labels = [
            ("Название", "title", QLineEdit),
            ("Описание", "desc", QTextEdit),
            ("Тип (body/brain)", "type", QComboBox),
            ("Сложность (1-10)", "difficulty", QLineEdit),
            ("Награда опыт", "reward_exp", QLineEdit),
            ("Награда сила", "reward_strength", QLineEdit),
            ("Награда интеллект", "reward_intelligence", QLineEdit),
            ("Штраф опыт", "penalty_exp", QLineEdit),
            ("Штраф энергия", "penalty_energy", QLineEdit),
        ]
        for label_text, key, widget_class in labels:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(140)
            row.addWidget(label)
            if widget_class == QComboBox:
                widget = QComboBox()
                widget.addItems(["body", "brain"])
            else:
                widget = widget_class()
            row.addWidget(widget)
            layout.addLayout(row)
            fields[key] = widget

        # ---------- РАЗДЕЛИТЕЛЬ ДЛЯ РЕГУЛЯРНЫХ КВЕСТОВ ----------
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep)

        cb_recurring = QCheckBox("Регулярный (повторяющийся)")
        layout.addWidget(cb_recurring)

        recurring_group = QWidget()
        recurring_group.setVisible(False)
        rec_layout = QVBoxLayout(recurring_group)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Тип повторения:"))
        combo_rec = QComboBox()
        combo_rec.addItems(["Ежедневно", "Еженедельно (дни)", "Ежемесячно (число)"])
        type_row.addWidget(combo_rec)
        rec_layout.addLayout(type_row)

        param_row = QHBoxLayout()
        param_row.addWidget(QLabel("Дни/число:"))
        edit_param = QLineEdit()
        edit_param.setPlaceholderText("1,3,5 или 15")
        param_row.addWidget(edit_param)
        rec_layout.addLayout(param_row)

        layout.addWidget(recurring_group)
        cb_recurring.toggled.connect(recurring_group.setVisible)
        # ------------------------------------------------------------

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        def save():
            try:
                data = {}
                for key, widget in fields.items():
                    if isinstance(widget, QLineEdit):
                        val = widget.text()
                        if key in ("difficulty", "reward_exp", "reward_strength",
                                   "reward_intelligence", "penalty_exp", "penalty_energy"):
                            data[key] = int(val) if val else 0
                        else:
                            data[key] = val
                    elif isinstance(widget, QTextEdit):
                        data[key] = widget.toPlainText()
                    elif isinstance(widget, QComboBox):
                        data[key] = widget.currentText()
                if data['type'] not in ('body','brain'):
                    QMessageBox.warning(dialog, "Ошибка", "Тип должен быть 'body' или 'brain'")
                    return

                # ---------- Сбор данных для регулярного квеста ----------
                recurring = 1 if cb_recurring.isChecked() else 0
                recurrence_rule = ""
                if recurring:
                    rtype = combo_rec.currentIndex()
                    if rtype == 0:
                        recurrence_rule = "daily"
                    elif rtype == 1:
                        days = edit_param.text().strip()
                        if not days or not all(d.strip().isdigit() for d in days.split(',')):
                            QMessageBox.warning(dialog, "Ошибка", "Укажите дни недели (1-7) через запятую")
                            return
                        recurrence_rule = f"weekly:{days}"
                    elif rtype == 2:
                        day_num = edit_param.text().strip()
                        if not day_num.isdigit():
                            QMessageBox.warning(dialog, "Ошибка", "Укажите число месяца (1-31)")
                            return
                        recurrence_rule = f"monthly:{day_num}"
                # ----------------------------------------------------------

                self.db.add_quest(
                    data['title'], data['desc'], data['type'], data['difficulty'],
                    data['reward_exp'], data['reward_strength'], data['reward_intelligence'],
                    data['penalty_exp'], data['penalty_energy'],
                    recurring, recurrence_rule   # <-- передаём новые параметры
                )
                self.update_all()
                dialog.accept()
            except ValueError as e:
                QMessageBox.warning(dialog, "Ошибка", f"Введите корректные числа: {e}")

        btn_save.clicked.connect(save)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()

    # ---------- Остальные методы ----------
    def get_selected_quest(self):
        row = self.quests_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите квест")
            return None
        qid_item = self.quests_table.item(row, 0)
        if qid_item is None:
            return None
        return int(qid_item.text())

    def complete_quest(self):
        qid = self.get_selected_quest()
        if qid is None:
            return
        success, msg = self.game.complete_quest(qid)
        if success:
            if msg:
                QMessageBox.information(self, "Уровень повышен!",
                                        f"Поздравляем! Вы достигли {self.game.player['level']} уровня!")
            self.update_all()
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    def fail_quest(self):
        qid = self.get_selected_quest()
        if qid is None:
            return
        success, msg = self.game.fail_quest(qid)
        if success:
            self.update_all()
            QMessageBox.information(self, "Штраф", msg)
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    # ------ Наказания ------
    def build_penalties_tab(self):
        layout = QVBoxLayout(self.penalties_tab)
        layout.setSpacing(10)

        btn_add = QPushButton("Добавить наказание")
        btn_add.clicked.connect(self.add_penalty_dialog)
        layout.addWidget(btn_add, alignment=Qt.AlignLeft)

        self.penalties_table = QTableWidget()
        self.penalties_table.setColumnCount(4)
        self.penalties_table.setHorizontalHeaderLabels(["ID", "Название", "Штраф опыт", "Штраф энергия"])
        self.penalties_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.penalties_table.setAlternatingRowColors(True)
        self.penalties_table.verticalHeader().setVisible(False)
        layout.addWidget(self.penalties_table)

        btn_frame = QHBoxLayout()
        btn_apply = QPushButton("Применить")
        btn_refresh = QPushButton("Обновить")
        btn_apply.clicked.connect(self.apply_penalty)
        btn_refresh.clicked.connect(self.update_penalties_table)
        btn_frame.addWidget(btn_apply)
        btn_frame.addWidget(btn_refresh)
        btn_frame.addStretch()
        layout.addLayout(btn_frame)

    def update_penalties_table(self):
        self.penalties_table.setRowCount(0)
        penalties = self.db.get_penalties()
        self.penalties_table.setRowCount(len(penalties))
        for i, p in enumerate(penalties):
            self.penalties_table.setItem(i, 0, self._make_item(p['id']))
            self.penalties_table.setItem(i, 1, self._make_item(p['name']))
            self.penalties_table.setItem(i, 2, self._make_item(p['penalty_exp']))
            self.penalties_table.setItem(i, 3, self._make_item(p['penalty_energy']))

    def add_penalty_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Новое наказание")
        dialog.setModal(True)
        dialog.setStyleSheet(STYLE)
        layout = QVBoxLayout(dialog)

        fields = {}
        labels = [
            ("Название", "name", QLineEdit),
            ("Описание", "desc", QTextEdit),
            ("Штраф опыт", "penalty_exp", QLineEdit),
            ("Штраф энергия", "penalty_energy", QLineEdit),
        ]
        for label_text, key, widget_class in labels:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFixedWidth(140)
            row.addWidget(label)
            widget = widget_class()
            row.addWidget(widget)
            layout.addLayout(row)
            fields[key] = widget

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        def save():
            try:
                data = {}
                for key, widget in fields.items():
                    if isinstance(widget, QLineEdit):
                        val = widget.text()
                        if key.startswith("penalty_"):
                            data[key] = int(val) if val else 0
                        else:
                            data[key] = val
                    elif isinstance(widget, QTextEdit):
                        data[key] = widget.toPlainText()
                self.db.add_penalty(data['name'], data['desc'],
                                    data['penalty_exp'], data['penalty_energy'])
                self.update_all()
                dialog.accept()
            except ValueError as e:
                QMessageBox.warning(dialog, "Ошибка", f"Введите корректные числа: {e}")

        btn_save.clicked.connect(save)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec_()

    def get_selected_penalty(self):
        row = self.penalties_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите наказание")
            return None
        pid_item = self.penalties_table.item(row, 0)
        if pid_item is None:
            return None
        return int(pid_item.text())

    def apply_penalty(self):
        pid = self.get_selected_penalty()
        if pid is None:
            return
        success, msg = self.game.apply_penalty(pid)
        if success:
            self.update_all()
            QMessageBox.information(self, "Наказание", msg)
        else:
            QMessageBox.warning(self, "Ошибка", msg)

    # ------ История ------
    def build_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        layout.setSpacing(10)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Время", "Действие", "Детали"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setVisible(False)
        layout.addWidget(self.history_table)

        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self.update_history_table)
        layout.addWidget(btn_refresh, alignment=Qt.AlignLeft)

    def update_history_table(self):
        self.history_table.setRowCount(0)
        history = self.db.get_history(limit=100)
        self.history_table.setRowCount(len(history))
        for i, (ts, action, details) in enumerate(history):
            self.history_table.setItem(i, 0, self._make_item(ts))
            self.history_table.setItem(i, 1, self._make_item(action))
            self.history_table.setItem(i, 2, self._make_item(details))
