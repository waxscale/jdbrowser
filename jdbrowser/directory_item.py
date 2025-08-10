from PySide6 import QtWidgets, QtGui, QtCore
from .constants import HIGHLIGHT_COLOR, HOVER_COLOR, SLATE_COLOR, TEXT_COLOR


class DirectoryItem(QtWidgets.QWidget):
    def __init__(self, tag_id, label, icon_data, page, index):
        super().__init__()
        self.tag_id = tag_id
        self.label_text = label if label is not None else ""
        self.page = page
        self.index = index
        self.isSelected = False
        self.isHover = False
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        if icon_data:
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(icon_data)
            if not pixmap.isNull():
                self.icon = QtWidgets.QLabel()
                rounded_pixmap = QtGui.QPixmap(240, 150)
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(rounded_pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                path = QtGui.QPainterPath()
                path.addRoundedRect(0, 0, 240, 150, 5, 5)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    240,
                    150,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                self.icon.setPixmap(rounded_pixmap)
                self.icon.setFixedSize(240, 150)
                self.icon.setStyleSheet("background-color: transparent;")
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(240, 150)
                self.icon.setStyleSheet(
                    f"background-color: {SLATE_COLOR}; border-radius: 5px;"
                )
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(240, 150)
            self.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 5px;"
            )
        layout.addWidget(self.icon)

        self.right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(self.right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        self.label = QtWidgets.QLabel(self.label_text)
        self.label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 1.2))
        font.setBold(True)
        self.label.setFont(font)
        # Add a small padding so the text isn't flush against the edges
        self.label.setStyleSheet(f"color: {TEXT_COLOR}; padding: 2px;")
        right_layout.addWidget(self.label)
        right_layout.addStretch(1)
        layout.addWidget(self.right)

        # Ensure clicks and hover on child widgets behave like the parent item
        for widget in (self.icon, self.right, self.label):
            widget.mousePressEvent = self.mousePressEvent  # type: ignore[attr-defined]
            widget.enterEvent = self.enterEvent  # type: ignore[attr-defined]
            widget.leaveEvent = self.leaveEvent  # type: ignore[attr-defined]

        self.updateStyle()

    def updateStyle(self):
        bg = HIGHLIGHT_COLOR if self.isSelected else (
            HOVER_COLOR if self.isHover else "transparent"
        )
        self.setStyleSheet(f"background-color: {bg}; border-radius: 5px;")

    def enterEvent(self, event):
        self.isHover = True
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.isHover = False
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Select on left-click; right-click edits the tag."""
        if self.page:
            if event.button() == QtCore.Qt.LeftButton:
                self.page.set_selection(self.index)
            elif event.button() == QtCore.Qt.RightButton:
                self.page.set_selection(self.index)
                self.page._edit_tag_label_with_icon()
        event.accept()

