from PySide6 import QtWidgets, QtCore, QtGui
from .constants import TEXT_COLOR, SURFACE_COLOR


class HeaderItem(QtWidgets.QWidget):
    def __init__(self, header_id, jd_area, jd_id, jd_ext, label, page, section_idx, text, color):
        super().__init__()
        self.header_id = header_id
        self.jd_area = jd_area
        self.jd_id = jd_id
        self.jd_ext = jd_ext
        self.label = label
        self.page = page
        self.section_idx = section_idx

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(5, 5, 5, 5)

        # Colored dot with soft outer ring using a wrapper
        self.dot_wrapper = QtWidgets.QFrame()
        self.dot_wrapper.setFixedSize(24, 24)
        self.dot_wrapper.setStyleSheet(
            "background-color: rgba(125,207,255,56); border-radius: 12px;"
        )
        self.dot = QtWidgets.QFrame(self.dot_wrapper)
        self.dot.setFixedSize(16, 16)
        self.dot.move(4, 4)
        self.dot.setStyleSheet(f"background-color: {color}; border-radius: 8px;")
        layout.addWidget(self.dot_wrapper)

        # Section title
        self.title = QtWidgets.QLabel(text.upper())
        font = self.title.font()
        font.setPointSize(int(font.pointSize() * 0.75))
        font.setBold(True)
        self.title.setFont(font)
        self.title.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.title)
        layout.addStretch()

        self.setStyleSheet(
            f"background-color: rgba(26,27,38,0.6); border-bottom: 1px solid {SURFACE_COLOR};"
        )
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        fm = self.title.fontMetrics()
        self.setFixedHeight(fm.height() + 20)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and self.page:
            self.page._edit_header(self)
        super().mousePressEvent(event)
