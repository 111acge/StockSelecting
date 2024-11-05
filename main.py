import sys
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
import qdarkstyle
from utils.logger import logger
import os

def setup_dll_path():
    """设置DLL路径"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        dll_paths = [
            base_path,
            os.path.join(base_path, '_internal'),
            os.path.join(base_path, 'py_mini_racer'),
        ]
        for path in dll_paths:
            if os.path.exists(path):
                try:
                    os.add_dll_directory(path)
                    logger.info(f"Added DLL directory: {path}")
                except Exception as e:
                    logger.error(f"Failed to add DLL directory {path}: {e}")
                if path not in os.environ['PATH']:
                    os.environ['PATH'] = path + os.pathsep + os.environ['PATH']

def setup_environment():
    """设置运行环境"""
    try:
        if getattr(sys, 'frozen', False):
            os.environ['AKSHARE_PATH'] = os.path.join(sys._MEIPASS, 'akshare')
            logger.info(f"Set AKSHARE_PATH to {os.environ['AKSHARE_PATH']}")
            setup_dll_path()
    except Exception as e:
        logger.error(f"Error in setup_environment: {e}")
        raise

def main():
    try:
        logger.info("Application starting...")

        # 设置环境
        setup_environment()

        # 创建应用
        app = QApplication(sys.argv)
        logger.info("QApplication created")

        # 设置更高的线程优先级
        app.thread().setPriority(QThread.Priority.HighestPriority)

        # 应用暗色主题
        try:
            app.setStyleSheet(qdarkstyle.load_stylesheet())
            logger.info("Dark style sheet loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load dark style sheet: {e}")
            # 使用备选的基本暗色主题
            app.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
            """)

        # 创建主窗口
        window = MainWindow()
        logger.info("Main window created")
        window.show()

        # 运行应用
        logger.info("Starting application event loop")
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()