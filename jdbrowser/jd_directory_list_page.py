from PySide6 import QtWidgets, QtGui, QtCore
import jdbrowser

class JdDirectoryListPage(QtWidgets.QMainWindow):
    def __init__(
        self,
        parent_uuid,
        jd_area,
        jd_id,
        jd_ext,
        grandparent_uuid,
        great_grandparent_uuid,
    ):
        super().__init__()
        self.parent_uuid = parent_uuid
        self.current_jd_area = jd_area
        self.current_jd_id = jd_id
        self.current_jd_ext = jd_ext
        self.grandparent_uuid = grandparent_uuid
        self.great_grandparent_uuid = great_grandparent_uuid
        self.setWindowTitle(
            f"File Browser - [{jd_area:02d}.{jd_id:02d}+{jd_ext:04d}]"
        )
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        central = QtWidgets.QWidget()
        central.setStyleSheet("background-color: black;")
        self.setCentralWidget(central)
        settings = QtCore.QSettings("xAI", "jdbrowser")
        if settings.contains("pos") and settings.contains("size"):
            self.move(settings.value("pos", type=QtCore.QPoint))
            self.resize(settings.value("size", type=QtCore.QSize))
        self._setup_shortcuts()

    def ascend_level(self):
        from .jd_ext_page import JdExtPage

        new_page = JdExtPage(
            parent_uuid=self.grandparent_uuid,
            jd_area=self.current_jd_area,
            jd_id=self.current_jd_id,
            grandparent_uuid=self.great_grandparent_uuid,
        )
        new_page.setGeometry(self.geometry())
        jdbrowser.current_page = new_page
        new_page.show()
        self.close()

    def _setup_shortcuts(self):
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        mappings = [
            (QtCore.Qt.Key_Backspace, self.ascend_level, None),
            (
                QtCore.Qt.Key_Up,
                self.ascend_level,
                None,
                QtCore.Qt.KeyboardModifier.AltModifier,
            ),
        ]
        self.shortcuts = []
        for mapping in mappings:
            key, func, arg = mapping[0], mapping[1], mapping[2]
            modifiers = (
                mapping[3]
                if len(mapping) > 3
                else QtCore.Qt.KeyboardModifier.NoModifier
            )
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key | modifiers), self)
            if arg is None:
                shortcut.activated.connect(func)
            else:
                shortcut.activated.connect(lambda f=func, a=arg: f(a))
            self.shortcuts.append(shortcut)
        quit_keys = ["Q", "Ctrl+Q", "Ctrl+W", "Alt+F4"]
        for seq in quit_keys:
            s = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            s.activated.connect(self.close)
            self.shortcuts.append(s)

    def closeEvent(self, event):
        settings = QtCore.QSettings("xAI", "jdbrowser")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        super().closeEvent(event)
