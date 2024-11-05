from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from .control_panel import ControlPanel
from .result_panel import ResultPanel
from core.worker import ScreeningWorker
import qdarkstyle
import pandas as pd
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QMessageBox,
                          QFileDialog, QGroupBox, QVBoxLayout, QLabel,
                          QSpinBox, QCheckBox, QDateEdit, QPushButton)
from PyQt6.QtCore import Qt, QDate, pyqtSignal


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('股票筛选工具')
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.worker = None

    def setup_ui(self):
        """设置界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建水平布局
        layout = QHBoxLayout(central_widget)

        # 创建控制面板
        self.control_panel = ControlPanel()
        self.control_panel.start_screening.connect(self.start_screening)
        self.control_panel.export_button.clicked.connect(self.export_results)

        # 创建结果面板
        self.result_panel = ResultPanel()

        # 添加到布局
        layout.addWidget(self.control_panel)
        layout.addWidget(self.result_panel)

    def start_screening(self, config: dict):
        """开始股票筛选"""
        # 清空之前的结果
        self.result_panel.clear()

        # 创建工作线程
        self.worker = ScreeningWorker(config)

        # 连接信号
        self.worker.progress_updated.connect(self.result_panel.update_progress)
        self.worker.status_updated.connect(self.result_panel.update_status)
        self.worker.log_updated.connect(self.result_panel.add_log)
        self.worker.result_ready.connect(self.handle_results)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.finished.connect(self.screening_finished)

        # 启动线程
        self.worker.start()

    def handle_results(self, results: pd.DataFrame):
        """处理筛选结果"""
        self.result_panel.show_results(results)
        self.current_results = results  # 保存结果用于导出

    def handle_error(self, error_msg: str):
        """处理错误"""
        QMessageBox.critical(self, "错误", f"筛选过程发生错误：\n{error_msg}")

    def screening_finished(self):
        """筛选完成处理"""
        self.control_panel.on_screening_finished()

    def export_results(self):
        """导出结果"""
        if not hasattr(self, 'current_results') or self.current_results.empty:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return

        # 获取保存路径
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            "",
            "Excel 文件 (*.xlsx);;CSV 文件 (*.csv)"
        )

        if not file_name:
            return

        try:
            if file_name.endswith('.xlsx'):
                self.current_results.to_excel(file_name, index=False)
            else:
                self.current_results.to_csv(file_name, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "成功", f"结果已成功导出至：\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")