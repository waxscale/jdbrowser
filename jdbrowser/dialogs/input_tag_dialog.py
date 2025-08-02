from PySide6 import QtWidgets, QtGui, QtCore
from ..constants import *

class InputTagDialog(QtWidgets.QDialog):
    def __init__(self, default_jd_area, default_label, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Tag")
        self.setFixedWidth(300)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # jd_area input
        self.jd_area_input = QtWidgets.QLineEdit(str(default_jd_area))
        self.jd_area_input.setPlaceholderText("Enter jd_area (integer)")
        self.jd_area_input.setValidator(QtGui.QIntValidator())
        self.jd_area_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        layout.addWidget(QtWidgets.QLabel("jd_area:"))
        layout.addWidget(self.jd_area_input)

        # jd_id input (hidden for now)
        self.jd_id_input = QtWidgets.QLineEdit()
        self.jd_id_input.setPlaceholderText("Enter jd_id (integer, optional)")
        self.jd_id_input.setValidator(QtGui.QIntValidator())
        self.jd_id_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        # layout.addWidget(QtWidgets.QLabel("jd_id (optional):"))
        # layout.addWidget(self.jd_id_input)

        # jd_ext input (hidden for now)
        self.jd_ext_input = QtWidgets.QLineEdit()
        self.jd_ext_input.setPlaceholderText("Enter jd_ext (integer, optional)")
        self.jd_ext_input.setValidator(QtGui.QIntValidator())
        self.jd_ext_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
            }}
        ''')
        # layout.addWidget(QtWidgets.QLabel("jd_ext (optional):"))
        # layout.addWidget(self.jd_ext_input)

        # Label input
        self.label_input = QtWidgets.QLineEdit(default_label)
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
        layout.addWidget(QtWidgets.QLabel("Label:"))
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

        # Style labels
        self.setStyleSheet(f'''
            QDialog {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {TEXT_COLOR};
            }}
        ''')

        # Focus the label input
        self.label_input.setFocus()

    def get_values(self):
        try:
            jd_area = int(self.jd_area_input.text()) if self.jd_area_input.text() else None
            jd_id = int(self.jd_id_input.text()) if self.jd_id_input.text() else None
            jd_ext = int(self.jd_ext_input.text()) if self.jd_ext_input.text() else None
        except ValueError:
            jd_area, jd_id, jd_ext = None, None, None
        return jd_area, jd_id, jd_ext, self.label_input.text()