from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QStyleFactory

from app.ui_mainwindow import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
