import sys
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
import qdarkstyle
import logging
from utils.logger import logger


def main():
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建应用
    app = QApplication(sys.argv)

    # 设置更高的线程优先级
    app.thread().setPriority(QThread.Priority.HighestPriority)

    # 应用暗色主题
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
