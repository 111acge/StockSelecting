from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTableWidget,
                             QTableWidgetItem, QTextEdit, QProgressBar, QLabel,
                             QHeaderView)
from PyQt6.QtCore import Qt
import pandas as pd
import traceback
import sys


class ResultPanel(QWidget):
    """结果显示面板"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.debug = False

    def setup_ui(self):
        """设置界面"""
        try:
            layout = QVBoxLayout(self)

            # 创建选项卡
            self.tab_widget = QTabWidget()

            # 结果表格
            self.result_table = self.create_result_table()
            self.tab_widget.addTab(self.result_table, "筛选结果")

            # 日志文本框
            self.log_text = self.create_log_text()
            self.tab_widget.addTab(self.log_text, "运行日志")

            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(True)

            # 状态标签
            self.status_label = QLabel("就绪")

            # 添加到布局
            layout.addWidget(self.tab_widget)
            layout.addWidget(self.progress_bar)
            layout.addWidget(self.status_label)
        except Exception as e:
            print(f"setup_ui error: {str(e)}")
            print(traceback.format_exc())
            raise

    def create_result_table(self) -> QTableWidget:
        """创建结果表格"""
        try:
            table = QTableWidget()
            # 设置列数和标题
            table.setColumnCount(12)
            table.setHorizontalHeaderLabels([
                '代码', '名称', '现价', '筹码均价',
                '获利比例', '基准价', '支撑位', '价格位置',
                '成交量', '价格标准差', '距基准线%', '距均价%'
            ])

            # 表格属性设置
            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            table.setAlternatingRowColors(True)
            table.setSortingEnabled(True)

            return table
        except Exception as e:
            print(f"create_result_table error: {str(e)}")
            print(traceback.format_exc())
            raise

    def create_log_text(self) -> QTextEdit:
        """创建日志文本框"""
        try:
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            return log_text
        except Exception as e:
            print(f"create_log_text error: {str(e)}")
            print(traceback.format_exc())
            raise

    def update_progress(self, value: int):
        """更新进度条"""
        try:
            self.progress_bar.setValue(value)
        except Exception as e:
            print(f"update_progress error: {str(e)}")

    def update_status(self, status: str):
        """更新状态标签"""
        try:
            self.status_label.setText(status)
        except Exception as e:
            print(f"update_status error: {str(e)}")

    def add_log(self, message: str):
        """添加日志消息"""
        try:
            print(message)  # 同时输出到控制台
            if hasattr(self, 'log_text'):
                self.log_text.append(message)
        except Exception as e:
            print(f"add_log error: {str(e)}")

    def safe_convert_value(self, value):
        """安全地转换值为显示格式"""
        try:
            if pd.isna(value):
                return ''
            if isinstance(value, bool):
                return "是" if value else "否"
            if isinstance(value, (int, float)):
                return f"{value:.2f}"
            return str(value)
        except Exception as e:
            print(f"safe_convert_value error for {value}: {str(e)}")
            return str(value)

    def show_results(self, df: pd.DataFrame):
        """显示筛选结果"""
        try:

            if df is None:
                self.add_log("输入的DataFrame为None")
                return

            if df.empty:
                self.add_log("输入的DataFrame为空")
                return

            # 列名映射
            column_mapping = {
                'code': 0,  # 代码
                'name': 1,  # 名称
                'current_price': 2,  # 现价
                'avg_cost': 3,  # 筹码均价
                'profit_ratio': 4,  # 获利比例
                'base_price': 5,  # 基准价
                'support_price': 6,  # 支撑位
                'price_position': 7,  # 价格位置
                'volume_ratio': 8,  # 成交量
                'is_trending_up': 9,  # 趋势
                '价格距离基准线': 10,  # 距基准线%
                '价格距离筹码均价': 11  # 距均价%
            }

            # 清空并设置行数
            self.result_table.setRowCount(0)
            self.result_table.setRowCount(len(df))

            # 逐行填充数据
            for row_idx, (_, row) in enumerate(df.iterrows()):
                try:
                    for col_name, col_idx in column_mapping.items():
                        try:
                            if col_name in row.index:
                                value = self.safe_convert_value(row[col_name])
                                item = QTableWidgetItem(value)
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                self.result_table.setItem(row_idx, col_idx, item)
                        except Exception as e:
                            self.add_log(f"处理列 {col_name} 时出错: {str(e)}")
                except Exception as e:
                    self.add_log(f"处理行 {row_idx} 时出错: {str(e)}")

            # 调整列宽
            self.result_table.resizeColumnsToContents()

            # 切换到结果标签页
            self.tab_widget.setCurrentIndex(0)

            # 更新状态
            self.update_status(f"已显示 {len(df)} 条记录")
            self.add_log("显示结果完成，查看程序窗口或者导出结果文件。")

        except Exception as e:
            error_msg = f"显示结果时发生错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # 输出到控制台
            self.add_log(error_msg)

    def clear(self):
        """清空所有显示"""
        try:
            self.result_table.setRowCount(0)
            self.log_text.clear()
            self.progress_bar.setValue(0)
            self.status_label.setText("就绪")
        except Exception as e:
            print(f"clear error: {str(e)}")
            print(traceback.format_exc())