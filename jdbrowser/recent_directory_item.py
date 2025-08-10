import os
from PySide6 import QtWidgets, QtGui, QtCore
from .constants import SLATE_COLOR, BREADCRUMB_INACTIVE_COLOR


class RecentDirectoryItem(QtWidgets.QWidget):
    def __init__(self, directory_id, label, order, icon_data, page):
        super().__init__()
        self.directory_id = directory_id
        self.label_text = label if label is not None else ""
        self.order = order
        self.page = page

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        if icon_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                self.icon = QtWidgets.QLabel()
                rounded_pixmap = QtGui.QPixmap(120, 75)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 120, 75, 3, 3)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    120,
                    75,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.icon.setPixmap(rounded_pixmap)
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet("background-color: transparent;")
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(120, 75)
                self.icon.setStyleSheet(
                    f"background-color: {SLATE_COLOR}; border-radius: 3px;"
                )
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(120, 75)
            self.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 3px;"
            )
        layout.addWidget(self.icon)

        self.label = QtWidgets.QLabel(self.label_text)
        self.label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 0.9))
        self.label.setFont(font)
        self.label.setStyleSheet(
            f"color: {BREADCRUMB_INACTIVE_COLOR}; padding-left: 5px;"
        )
        layout.addWidget(self.label)
        layout.addStretch(1)

    def updateLabel(self, show_prefix):
        if show_prefix:
            formatted = f"{self.order:016d}"
            formatted = "_".join(
                formatted[i : i + 4] for i in range(0, 16, 4)
            )
            text = os.path.join(self.page.repository_path, formatted)
        else:
            text = self.label_text
        self.label.setText(text)
