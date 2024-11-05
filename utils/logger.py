import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback
from PyQt6.QtWidgets import QMessageBox


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """初始化日志配置"""
        # 创建logger
        self.logger = logging.getLogger('StockScreener')
        self.logger.setLevel(logging.DEBUG)  # 设置为DEBUG以捕获所有级别的日志

        # 清除现有的处理器（避免重复）
        self.logger.handlers.clear()

        # 创建logs目录
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # 文件处理器
        log_file = log_dir / f'stock_screener_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 设置全局异常处理器
        sys.excepthook = self._exception_hook

    def _exception_hook(self, exctype, value, tb):
        """全局异常处理器"""
        error_msg = ''.join(traceback.format_exception(exctype, value, tb))
        self.logger.error(f"Uncaught exception: {error_msg}")

        # 显示错误对话框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("An error has occurred")
        msg.setInformativeText(str(value))
        msg.setDetailedText(error_msg)
        msg.setWindowTitle("Error")
        msg.exec()

    def get_logger(self):
        """获取logger实例"""
        return self.logger


# 创建全局logger实例
logger = Logger().get_logger()