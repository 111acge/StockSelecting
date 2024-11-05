from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QCheckBox,
                             QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
                             QGridLayout, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from datetime import datetime, timedelta


class ControlPanel(QWidget):
    """控制面板"""
    start_screening = pyqtSignal(dict)  # 开始筛选信号

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(300)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 日期选择组
        layout.addWidget(self.create_date_group())

        # 过滤条件组
        layout.addWidget(self.create_filter_group())

        # 技术指标组
        layout.addWidget(self.create_technical_group())

        # 操作按钮组
        layout.addWidget(self.create_control_group())

        # 文字说明
        layout.addWidget(self.create_text())

        # 添加伸缩空间
        layout.addStretch()

    def create_date_group(self) -> QGroupBox:
        """创建日期选择组"""
        group = QGroupBox("日期范围")
        layout = QGridLayout()

        # 开始日期
        layout.addWidget(QLabel("开始日期:"), 0, 0)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        layout.addWidget(self.start_date, 0, 1)

        # 结束日期
        layout.addWidget(QLabel("结束日期:"), 1, 0)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        layout.addWidget(self.end_date, 1, 1)

        group.setLayout(layout)
        return group

    def create_filter_group(self) -> QGroupBox:
        """创建过滤条件组"""
        group = QGroupBox("过滤条件")
        layout = QGridLayout()

        # 创建过滤选项
        self.st_checkbox = QCheckBox("排除ST股票")
        self.gem_checkbox = QCheckBox("排除创业板")
        self.star_checkbox = QCheckBox("排除科创板")
        self.bse_checkbox = QCheckBox("排除北交所")

        # 设置默认值
        checkboxes = [self.st_checkbox, self.gem_checkbox,
                      self.star_checkbox, self.bse_checkbox]
        for checkbox in checkboxes:
            checkbox.setChecked(True)

        # 最小成交额
        layout.addWidget(QLabel("最小成交额（100-10000）:"), 4, 0)
        self.min_amount_spin = QSpinBox()
        self.min_amount_spin.setRange(100, 10000)
        self.min_amount_spin.setValue(1000)
        self.min_amount_spin.setSuffix(" 万")
        layout.addWidget(self.min_amount_spin, 4, 1)

        # 布局
        layout.addWidget(self.st_checkbox, 0, 0, 1, 2)
        layout.addWidget(self.gem_checkbox, 1, 0, 1, 2)
        layout.addWidget(self.star_checkbox, 2, 0, 1, 2)
        layout.addWidget(self.bse_checkbox, 3, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_technical_group(self) -> QGroupBox:
        """创建技术指标参数组"""
        group = QGroupBox("技术指标参数")
        layout = QGridLayout()

        # 五线谱参数
        layout.addWidget(QLabel("MA5周期（3-10）:"), 0, 0)
        self.ma5_spin = QSpinBox()
        self.ma5_spin.setRange(3, 10)
        self.ma5_spin.setValue(5)
        self.ma5_spin.setSuffix(" 天")
        layout.addWidget(self.ma5_spin, 0, 1)

        layout.addWidget(QLabel("MA10周期（8-15）:"), 1, 0)
        self.ma10_spin = QSpinBox()
        self.ma10_spin.setRange(8, 15)
        self.ma10_spin.setValue(10)
        self.ma10_spin.setSuffix(" 天")
        layout.addWidget(self.ma10_spin, 1, 1)

        layout.addWidget(QLabel("MA20周期（15-25）:"), 2, 0)
        self.ma20_spin = QSpinBox()
        self.ma20_spin.setRange(15, 25)
        self.ma20_spin.setValue(20)
        self.ma20_spin.setSuffix(" 天")
        layout.addWidget(self.ma20_spin, 2, 1)

        layout.addWidget(QLabel("MA30周期（25-35）:"), 3, 0)
        self.ma30_spin = QSpinBox()
        self.ma30_spin.setRange(25, 35)
        self.ma30_spin.setValue(30)
        self.ma30_spin.setSuffix(" 天")
        layout.addWidget(self.ma30_spin, 3, 1)

        layout.addWidget(QLabel("MA60周期（50-70）:"), 4, 0)
        self.ma60_spin = QSpinBox()
        self.ma60_spin.setRange(50, 70)
        self.ma60_spin.setValue(60)
        self.ma60_spin.setSuffix(" 天")
        layout.addWidget(self.ma60_spin, 4, 1)

        # 筹码计算参数
        layout.addWidget(QLabel("筹码计算天数（30-730）:"), 5, 0)
        self.chip_days_spin = QSpinBox()
        self.chip_days_spin.setRange(30, 730)
        self.chip_days_spin.setValue(365)
        self.chip_days_spin.setSuffix(" 天")
        layout.addWidget(self.chip_days_spin, 5, 1)

        group.setLayout(layout)
        return group

    def create_control_group(self) -> QGroupBox:
        """创建操作按钮组"""
        group = QGroupBox("操作")
        layout = QVBoxLayout()

        # 开始按钮
        self.start_button = QPushButton("开始筛选")
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)

        # 导出按钮
        self.export_button = QPushButton("导出结果")
        self.export_button.setEnabled(False)
        layout.addWidget(self.export_button)

        group.setLayout(layout)
        return group

    def create_text(self) -> QGroupBox:
        """创建说明"""
        group = QGroupBox("说明")
        layout = QVBoxLayout()
        # 文字
        layout.addWidget(QLabel("仅供程序学习参考！严禁用作股票推荐！"))
        group.setLayout(layout)
        return group

    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            'data': {
                'start_date': self.start_date.date().toString('yyyyMMdd'),
                'end_date': self.end_date.date().toString('yyyyMMdd'),
                'min_data_length': 30,
                'min_trading_amount': self.min_amount_spin.value() * 10000  # 转换为元
            },
            'filter_switches': {
                'exclude_st': self.st_checkbox.isChecked(),
                'exclude_gem': self.gem_checkbox.isChecked(),
                'exclude_star': self.star_checkbox.isChecked(),
                'exclude_bse': self.bse_checkbox.isChecked()
            },
            'technical': {
                'moving_averages': {
                    'ma5': self.ma5_spin.value(),
                    'ma10': self.ma10_spin.value(),
                    'ma20': self.ma20_spin.value(),
                    'ma30': self.ma30_spin.value(),
                    'ma60': self.ma60_spin.value()
                },
                'chip_distribution': {
                    'n_days': self.chip_days_spin.value()
                }
            },
            'system': {
                'max_workers': 24,
                'retry_times': 3,
                'retry_delay': 2,
                'request_delay': (0.1, 0.5)
            }
        }

    def on_start_clicked(self):
        """开始按钮点击处理"""
        self.start_button.setEnabled(False)
        self.start_button.setText("筛选中...")
        self.export_button.setEnabled(False)
        config = self.get_config()

        # 验证日期
        start_date = datetime.strptime(config['data']['start_date'], '%Y%m%d')
        end_date = datetime.strptime(config['data']['end_date'], '%Y%m%d')

        if start_date >= end_date:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "日期错误",
                "开始日期必须早于结束日期",
                QMessageBox.StandardButton.Ok
            )
            self.on_screening_finished()
            return

        self.start_screening.emit(config)

    def on_screening_finished(self, success: bool = True):
        """筛选完成处理"""
        self.start_button.setEnabled(True)
        self.start_button.setText("开始筛选")
        self.export_button.setEnabled(success)
