from PySide6 import QtWidgets
from ..constants import *

class DeleteTagDialog(QtWidgets.QDialog):
    def __init__(self, tag_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Delete")
        self.setFixedWidth(600)  # User-specified width
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Confirmation message
        self.message = QtWidgets.QLabel(f"Are you sure you want to delete the tag '{tag_name}'?")
        self.message.setStyleSheet(f'color: {TEXT_COLOR};')
        layout.addWidget(self.message)

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