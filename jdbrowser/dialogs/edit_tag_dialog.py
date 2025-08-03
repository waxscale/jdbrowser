import os
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QIntValidator
from PySide6.QtCore import Qt, QSettings
from ..constants import *


class EditTagDialog(QDialog):
    def __init__(self, current_label, icon_data, level, jd_area=None, jd_id=None, jd_ext=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tag Label and Icon")
        self.icon_data = icon_data
        self.level = level
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.setStyleSheet(f'''
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
        ''')

        layout = QVBoxLayout(self)

        # Icon preview (clickable to change icon)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(240, 150)
        self.icon_label.setStyleSheet(f'background-color: {SLATE_COLOR}; border-radius: 10px;')
        if icon_data:
            pixmap = QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                rounded_pixmap = QPixmap(240, 150)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(240, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon_label.setPixmap(rounded_pixmap)
        self.icon_label.setCursor(Qt.PointingHandCursor)
        self.icon_label.mousePressEvent = self.change_icon
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Prefix input (below icon, full width)
        default_prefix = [jd_area, jd_id, jd_ext][level]
        placeholder = ["jd_area", "jd_id", "jd_ext"][level]
        self.prefix_input = QLineEdit("" if default_prefix is None else str(default_prefix))
        self.prefix_input.setMinimumWidth(240)
        self.prefix_input.setPlaceholderText(placeholder)
        self.prefix_input.setValidator(QIntValidator())
        self.prefix_input.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addWidget(self.prefix_input, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Label input (below prefix, full width)
        self.input = QLineEdit(current_label)
        self.input.setMinimumWidth(240)  # Match thumbnail width
        self.input.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.input.selectAll()  # Select all text in the input box
        layout.addWidget(self.input, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Buttons (side-by-side, half-width each)
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        # Set buttons to approximately half-width
        button_layout.setStretch(0, 1)
        button_layout.setStretch(1, 1)
        layout.addLayout(button_layout)

        self.setFixedSize(self.sizeHint())

    def change_icon(self, event=None):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png)")
        settings = QSettings("xAI", "jdbrowser")
        last_dir = settings.value("last_thumbnail_dir", "", type=str)
        if last_dir:
            file_dialog.setDirectory(last_dir)
        file_dialog.setStyleSheet(f'''
            QFileDialog {{
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
            QToolButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QToolButton:hover {{
                background-color: {HIGHLIGHT_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
            QTreeView, QListView {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
            }}
            QTreeView::item:selected, QListView::item:selected {{
                background-color: {HIGHLIGHT_COLOR};
                color: {TEXT_COLOR};
            }}
            QTreeView::item:hover, QListView::item:hover {{
                background-color: {HOVER_COLOR};
            }}
            QComboBox {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                selection-background-color: {HIGHLIGHT_COLOR};
            }}
        ''')
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            settings.setValue("last_thumbnail_dir", os.path.dirname(file_path))
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                with open(file_path, 'rb') as f:
                    self.icon_data = f.read()
                rounded_pixmap = QPixmap(240, 150)
                rounded_pixmap.fill(Qt.transparent)
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(240, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon_label.setPixmap(rounded_pixmap)

    def get_label(self):
        return self.input.text().strip()

    def get_icon_data(self):
        return self.icon_data

    def get_path(self):
        try:
            prefix = int(self.prefix_input.text()) if self.prefix_input.text() else None
        except ValueError:
            prefix = None
        if self.level == 0:
            return prefix, None, None
        elif self.level == 1:
            return self.jd_area, prefix, None
        else:
            return self.jd_area, self.jd_id, prefix