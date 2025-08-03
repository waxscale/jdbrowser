import os
from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QIntValidator
from PySide6.QtCore import Qt, QSettings, QTimer
from ..constants import *


class EditTagDialog(QDialog):
    """Dialog to edit tag label/icon and order."""

    def __init__(self, current_label, icon_data, order, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tag")
        self.icon_data = icon_data

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
            }}
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {HIGHLIGHT_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        """)

        layout = QVBoxLayout(self)

        # Icon preview
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(240, 150)
        self.icon_label.setStyleSheet(f"background-color: {SLATE_COLOR}; border-radius: 10px;")
        if icon_data:
            pixmap = QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                rounded = QPixmap(240, 150)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled = pixmap.scaled(240, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.icon_label.setPixmap(rounded)
        self.icon_label.setCursor(Qt.PointingHandCursor)
        self.icon_label.mousePressEvent = self.change_icon
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # order input
        self.order_input = QLineEdit("" if order is None else str(order))
        self.order_input.setValidator(QIntValidator())
        self.order_input.setPlaceholderText("order")
        layout.addWidget(self.order_input)

        # label input
        self.input = QLineEdit(current_label)
        layout.addWidget(self.input)

        # buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setFixedSize(self.sizeHint())
        QTimer.singleShot(0, self._focus_label)

    def _focus_label(self):
        self.input.setFocus()
        self.input.selectAll()

    def change_icon(self, event=None):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png)")
        settings = QSettings("xAI", "jdbrowser")
        last_dir = settings.value("last_thumbnail_dir", "", type=str)
        if last_dir:
            file_dialog.setDirectory(last_dir)
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            settings.setValue("last_thumbnail_dir", os.path.dirname(file_path))
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                with open(file_path, "rb") as f:
                    self.icon_data = f.read()
                rounded = QPixmap(240, 150)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled = pixmap.scaled(240, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.icon_label.setPixmap(rounded)

    def get_label(self):
        return self.input.text().strip()

    def get_icon_data(self):
        return self.icon_data

    def get_order(self):
        try:
            return int(self.order_input.text()) if self.order_input.text() else None
        except ValueError:
            return None

