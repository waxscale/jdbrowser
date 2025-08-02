import sys
import signal
import re
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from jdbrowser.file_browser import FileBrowser
from PySide6.QtCore import QSettings, QPoint, QSize
from PySide6.QtGui import QFont

# Allow Ctrl+C (SIGINT) to quit the Qt application
signal.signal(signal.SIGINT, lambda sig, frame: QApplication.quit())

if __name__ == '__main__':
    start_id = sys.argv[1] if len(sys.argv) > 1 else None
    if start_id and not re.match(r'^\d{2}(\.\d{2})?$', start_id):
        print('Error:', start_id, 'is not a valid id. Use XX or XX.YY.')
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setFont(QFont('FiraCode Nerd Font'))
    browser = FileBrowser(start_id)
    settings = QSettings("xAI", "jdbrowser")
    if not (settings.contains("pos") and settings.contains("size")):
        browser.resize(1000, 600)
        screen = app.primaryScreen().geometry()
        browser.move((screen.width() - 1000) // 2, (screen.height() - 600) // 2)
    browser.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)
    sys.exit(app.exec())
