from PySide6 import QtWidgets, QtGui
from ..constants import *


class InputTagDialog(QtWidgets.QDialog):
    def __init__(self, default_jd_area=None, default_jd_id=None, default_jd_ext=None, default_label="", level=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        self.level = level
        self.fixed_jd_area = default_jd_area if level >= 1 else None
        self.fixed_jd_id = default_jd_id if level >= 2 else None
        default_prefix = [default_jd_area, default_jd_id, default_jd_ext][level]
        placeholder = ["jd_area", "jd_id", "jd_ext"][level]
        self.prefix_input = QtWidgets.QLineEdit("" if default_prefix is None else str(default_prefix))
        self.prefix_input.setPlaceholderText(placeholder)
        self.prefix_input.setValidator(QtGui.QIntValidator())
        self.prefix_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        self.prefix_input.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout.addWidget(self.prefix_input)

        self.label_input = QtWidgets.QLineEdit(default_label)
        self.label_input.setPlaceholderText("Label")
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

        self.setStyleSheet(f'''
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        ''')

        self.label_input.setFocus()

    def get_values(self):
        try:
            prefix = int(self.prefix_input.text()) if self.prefix_input.text() else None
        except ValueError:
            prefix = None
        if self.level == 0:
            jd_area, jd_id, jd_ext = prefix, None, None
        elif self.level == 1:
            jd_area, jd_id, jd_ext = self.fixed_jd_area, prefix, None
        else:
            jd_area, jd_id, jd_ext = self.fixed_jd_area, self.fixed_jd_id, prefix
        return jd_area, jd_id, jd_ext, self.label_input.text()

