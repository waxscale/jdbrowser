import sys
import signal
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from jdbrowser.file_browser import FileBrowser
from PySide6.QtCore import QSettings, QPoint, QSize
from PySide6.QtGui import QFont

# Allow Ctrl+C (SIGINT) to quit the Qt application
signal.signal(signal.SIGINT, lambda sig, frame: QApplication.quit())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont('FiraCode Nerd Font'))
    browser = FileBrowser()
    settings = QSettings("xAI", "jdbrowser")
    size = settings.value("size", QSize(1000, 600), type=QSize)
    pos = settings.value("pos", None, type=QPoint)
    browser.resize(size)
    if pos is not None:
        browser.move(pos)
    else:
        screen = app.primaryScreen().geometry()
        browser.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2,
        )
    browser.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    sys.exit(app.exec())
