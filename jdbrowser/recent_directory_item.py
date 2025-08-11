import os
from PySide6 import QtWidgets, QtGui, QtCore
from .constants import (
    SLATE_COLOR,
    BREADCRUMB_INACTIVE_COLOR,
    BREADCRUMB_ACTIVE_COLOR,
    HIGHLIGHT_COLOR,
    HOVER_COLOR,
    TEXT_COLOR,
)
from .flow_layout import FlowLayout


class RecentDirectoryItem(QtWidgets.QWidget):
    def __init__(self, directory_id, label, order, icon_data, page, index, tags=None):
        super().__init__()
        self.directory_id = directory_id
        self.label_text = label if label is not None else ""
        self.order = order
        self.page = page
        self.index = index
        self.tags = tags or []
        self.isSelected = False
        self.isHover = False
        self.isDimmed = False
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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
                self.icon.setContentsMargins(0, 0, 0, 0)
                self.icon.setMargin(0)
                self.icon.setStyleSheet(
                    "background-color: transparent; padding: 0; margin: 0; border: none;"
                )
            else:
                self.icon = QtWidgets.QFrame()
                self.icon.setFixedSize(120, 75)
                self.icon.setContentsMargins(0, 0, 0, 0)
                self.icon.setStyleSheet(
                    f"background-color: {SLATE_COLOR}; border-radius: 3px; padding: 0; margin: 0;"
                )
        else:
            self.icon = QtWidgets.QFrame()
            self.icon.setFixedSize(120, 75)
            self.icon.setContentsMargins(0, 0, 0, 0)
            self.icon.setStyleSheet(
                f"background-color: {SLATE_COLOR}; border-radius: 3px; padding: 0; margin: 0;"
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
        font.setPointSize(int(font.pointSize() * 0.9))
        self.label.setFont(font)
        self.label.setStyleSheet("padding-left: 5px; border: none;")
        right_layout.addWidget(self.label)

        self.tags_widget = QtWidgets.QWidget()
        self.tags_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        self.tags_layout = FlowLayout(self.tags_widget, margin=0, spacing=5)
        self.tags_layout.setContentsMargins(5, 2, 0, 0)
        right_layout.addWidget(self.tags_widget)
        right_layout.addStretch(1)

        layout.addWidget(self.right, 1)

        for widget in (self.icon, self.right, self.label, self.tags_widget):
            widget.mousePressEvent = self.mousePressEvent  # type: ignore[attr-defined]
            widget.installEventFilter(self)

        self._build_tag_pills()
        self.updateStyle()

    def updateLabel(self, show_prefix):
        if show_prefix:
            formatted = f"{self.order:016d}"
            formatted = "_".join(
                formatted[i : i + 4] for i in range(0, 16, 4)
            )
            text = formatted
        else:
            text = self.label_text
        self.label.setText(text)

    def updateStyle(self):
        bg = (
            HIGHLIGHT_COLOR
            if self.isSelected
            else (HOVER_COLOR if self.isHover else "transparent")
        )
        fg = (
            BREADCRUMB_ACTIVE_COLOR
            if self.isSelected
            else BREADCRUMB_INACTIVE_COLOR
        )
        opacity = 0.4 if self.isDimmed else 1.0
        icon_effect = QtWidgets.QGraphicsOpacityEffect(self.icon)
        icon_effect.setOpacity(opacity)
        self.icon.setGraphicsEffect(icon_effect)
        label_effect = QtWidgets.QGraphicsOpacityEffect(self.label)
        label_effect.setOpacity(opacity)
        self.label.setGraphicsEffect(label_effect)
        tags_effect = QtWidgets.QGraphicsOpacityEffect(self.tags_widget)
        tags_effect.setOpacity(opacity)
        self.tags_widget.setGraphicsEffect(tags_effect)
        self.label.setStyleSheet(
            f"color: {fg}; padding-left: 5px; border: none;"
        )
        self.setStyleSheet(f"background-color: {bg}; border-radius: 3px;")

    def _build_tag_pills(self):
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        for t_id, t_label, t_order, parent_uuid in self.tags:
            btn = QtWidgets.QPushButton(t_label)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(
                f"background-color: {BREADCRUMB_INACTIVE_COLOR}; color: {TEXT_COLOR}; border: none;"
                " border-radius: 10px; padding: 3px 7px;"
            )
            btn.setMinimumWidth(60)
            btn.mousePressEvent = self.mousePressEvent  # type: ignore[attr-defined]
            btn.installEventFilter(self)
            self.tags_layout.addWidget(btn)

    def _on_enter(self):
        self.isHover = True
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

    def _on_leave(self):
        self.isHover = False
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))

    def enterEvent(self, event):
        self._on_enter()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._on_leave()
        super().leaveEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Enter:
            self._on_enter()
        elif event.type() == QtCore.QEvent.Leave:
            pos = self.mapFromGlobal(QtGui.QCursor.pos())
            if not self.rect().contains(pos):
                self._on_leave()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if self.page:
            if event.button() == QtCore.Qt.LeftButton:
                self.page.set_selection(self.index)
            elif event.button() == QtCore.Qt.RightButton:
                self.page.set_selection(self.index)
                self.page._edit_tag_label_with_icon()
        event.accept()
