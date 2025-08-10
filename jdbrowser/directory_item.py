import os
from PySide6 import QtWidgets, QtGui, QtCore
from .constants import (
    HIGHLIGHT_COLOR,
    HOVER_COLOR,
    SLATE_COLOR,
    TEXT_COLOR,
    BORDER_COLOR,
    TAG_COLOR,
)
from .flow_layout import FlowLayout


class DirectoryItem(QtWidgets.QWidget):
    def __init__(self, tag_id, label, order, icon_data, page, index, tags=None):
        super().__init__()
        self.tag_id = tag_id
        self.label_text = label if label is not None else ""
        self.order = order
        # Each tag tuple: (tag_id, label, order, parent_uuid)
        self.tags = tags or []
        self.tag_buttons = []
        self.page = page
        self.index = index
        self.isSelected = False
        self.isHover = False
        self.isDimmed = False
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
        right_layout.setSpacing(5)

        self.label = QtWidgets.QLabel(self.label_text)
        self.label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        font = self.label.font()
        font.setPointSize(int(font.pointSize() * 1.2))
        font.setBold(True)
        self.label.setFont(font)
        # Add a small padding so the text isn't flush against the edges
        self.label.setStyleSheet(f"color: {TEXT_COLOR}; padding: 2px 2px 4px 2px;")
        right_layout.addWidget(self.label)

        # Tag pills container
        self.tags_widget = QtWidgets.QWidget()
        self.tags_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        self.tags_layout = FlowLayout(self.tags_widget, margin=0, spacing=5)
        self.tags_layout.setContentsMargins(10, 2, 0, 0)
        right_layout.addWidget(self.tags_widget)
        right_layout.addStretch(1)
        self._build_tag_pills()
        layout.addWidget(self.right)

        # Ensure clicks on child widgets behave like the parent item and
        # monitor their hover events via an event filter
        for widget in (self.icon, self.right, self.label, self.tags_widget):
            widget.mousePressEvent = self.mousePressEvent  # type: ignore[attr-defined]
            widget.installEventFilter(self)

        self.updateStyle()

    def _format_prefix(self, order):
        s = f"{order:016d}"
        area = int(s[0:4])
        jd_id = int(s[4:8])
        jd_ext = int(s[8:12])
        return f"[{area:02d}.{jd_id:02d}+{jd_ext:04d}]"

    def _build_tag_pills(self):
        # Clear existing pills
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        self.tag_buttons = []
        for t_id, t_label, t_order, parent_uuid in self.tags:
            text = t_label if not self.page.show_prefix else self._format_prefix(t_order)
            btn = QtWidgets.QPushButton(text)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(
                f"background-color: {TAG_COLOR}; color: {TEXT_COLOR}; border: none;"
                " border-radius: 10px; padding: 3px 7px;"
            )
            btn.setMinimumWidth(60)
            # Pass mouse events through to the DirectoryItem so clicking a tag
            # pill still selects the underlying directory entry
            btn.mousePressEvent = self.mousePressEvent  # type: ignore[attr-defined]
            btn.installEventFilter(self)
            self.tag_buttons.append((btn, t_id, t_label, t_order, parent_uuid))
            self.tags_layout.addWidget(btn)
        self.tags_widget.adjustSize()

    def updateLabel(self, show_prefix):
        if show_prefix:
            formatted = f"{self.order:016d}"
            formatted = "_".join(formatted[i:i+4] for i in range(0, 16, 4))
            text = os.path.join(self.page.repository_path, formatted)
        else:
            text = self.label_text
        self.label.setText(text)
        # Update tag pills
        for btn, t_id, t_label, t_order, _ in self.tag_buttons:
            btn.setText(t_label if not show_prefix else self._format_prefix(t_order))

    def updateStyle(self):
        bg = HIGHLIGHT_COLOR if self.isSelected else (
            HOVER_COLOR if self.isHover else "transparent"
        )
        opacity = 0.4 if self.isDimmed else 1.0
        icon_effect = QtWidgets.QGraphicsOpacityEffect(self.icon)
        icon_effect.setOpacity(opacity)
        self.icon.setGraphicsEffect(icon_effect)
        right_effect = QtWidgets.QGraphicsOpacityEffect(self.right)
        right_effect.setOpacity(opacity)
        self.right.setGraphicsEffect(right_effect)
        self.setStyleSheet(f"background-color: {bg}; border-radius: 5px;")

    def _on_enter(self):
        """Handle hover entering the item."""
        self.isHover = True
        self.updateStyle()
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

    def _on_leave(self):
        """Handle hover leaving the item."""
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
        """Select on left-click; right-click edits the tag."""
        if self.page:
            if event.button() == QtCore.Qt.LeftButton:
                self.page.set_selection(self.index)
            elif event.button() == QtCore.Qt.RightButton:
                self.page.set_selection(self.index)
                self.page._edit_tag_label_with_icon()
        event.accept()

