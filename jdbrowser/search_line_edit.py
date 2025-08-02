from PySide6 import QtWidgets
from .constants import *

class SearchLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_browser = parent
        self.setStyleSheet(f'''
            QLineEdit {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 5px;
                font-family: 'FiraCode Nerd Font';
            }}
        ''')

    def focusOutEvent(self, event):
        # Exit search mode like Enter when losing focus
        self.parent_browser.exit_search_mode_select()
        super().focusOutEvent(event)