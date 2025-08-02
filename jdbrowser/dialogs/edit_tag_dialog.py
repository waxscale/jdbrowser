from PySide6 import QtWidgets, QtGui, QtCore
from ..constants import *

class EditTagDialog(QtWidgets.QDialog):
    def __init__(self, current_label, current_icon, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Icon display (clickable)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setMouseTracking(True)
        self.icon_label.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.new_icon_data = None  # Track new image data
        if current_icon:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(current_icon)
            if not pixmap.isNull():
                rounded_pixmap = QtGui.QPixmap(240, 150)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(240, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.icon_label.setPixmap(rounded_pixmap)
            else:
                self.icon_label = QtWidgets.QFrame()
                self.icon_label.setFixedSize(240, 150)
                self.icon_label.setStyleSheet(f'background-color: {SLATE_COLOR}; border-radius: 10px;')
        else:
            self.icon_label = QtWidgets.QFrame()
            self.icon_label.setFixedSize(240, 150)
            self.icon_label.setStyleSheet(f'background-color: {SLATE_COLOR}; border-radius: 10px;')
        self.icon_label.setMouseTracking(True)
        self.icon_label.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.icon_label.mousePressEvent = self.select_icon
        layout.addWidget(self.icon_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        # Label input
        self.label_input = QtWidgets.QLineEdit(current_label)
        self.label_input.setPlaceholderText("Enter tag label")
        self.label_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        layout.addWidget(self.label_input)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.setStyleSheet(f'''
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #e0c58f;
            }}
        ''')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(f'background-color: {BACKGROUND_COLOR};')

    def select_icon(self, event):
        """Open file dialog to select a new .png image and update the icon display."""
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png)")
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
                background-color: #e0c58f;
            }}
            QToolButton {{
                background-color: {BUTTON_COLOR};
                color: black;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }}
            QToolButton:hover {{
                background-color: #e0c58f;
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
            pixmap = QtGui.QPixmap(file_path)
            if not pixmap.isNull():
                rounded_pixmap = QtGui.QPixmap(240, 150)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 10, 10)
                painter.setClipPath(path)
                scaled_pixmap = pixmap.scaled(240, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                # Replace QFrame with QLabel if necessary
                if isinstance(self.icon_label, QtWidgets.QFrame):
                    layout = self.icon_label.parent().layout()
                    layout.removeWidget(self.icon_label)
                    self.icon_label.deleteLater()
                    self.icon_label = QtWidgets.QLabel()
                    self.icon_label.setFixedSize(240, 150)
                    self.icon_label.setMouseTracking(True)
                    self.icon_label.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
                    self.icon_label.mousePressEvent = self.select_icon
                    layout.insertWidget(0, self.icon_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
                self.icon_label.setPixmap(rounded_pixmap)
                with open(file_path, 'rb') as f:
                    self.new_icon_data = f.read()

    def get_label(self):
        return self.label_input.text()

    def get_icon_data(self):
        return self.new_icon_data