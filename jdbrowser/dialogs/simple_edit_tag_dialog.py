from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from ..constants import *

class SimpleEditTagDialog(QDialog):
    def __init__(self, current_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tag Label")
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
                background-color: #e0c58f;
            }}
        ''')

        layout = QVBoxLayout(self)
        self.input = QLineEdit(current_label)
        # Make the rename dialog significantly wider for better usability
        self.input.setMinimumWidth(600)
        self.input.selectAll()  # Select all text in the input box
        layout.addWidget(self.input)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        for b in (self.ok_button, self.cancel_button):
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            button_layout.addWidget(b)
        button_layout.setStretch(0, 1)
        button_layout.setStretch(1, 1)
        layout.addLayout(button_layout)

        self.setFixedSize(self.sizeHint())

    def get_label(self):
        return self.input.text().strip()
