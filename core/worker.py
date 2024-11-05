from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List
import pandas as pd
from core.screener import StockScreener
from utils.logger import logger
import time
from datetime import datetime, timedelta


class ScreeningWorker(QThread):
    """股票筛选工作线程"""
    # 信号定义
    progress_updated = pyqtSignal(int)  # 进度更新信号
    status_updated = pyqtSignal(str)  # 状态更新信号
    log_updated = pyqtSignal(str)  # 日志更新信号
    result_ready = pyqtSignal(pd.DataFrame)  # 结果就绪信号
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.is_running = True
        self.screener = None

    def stop(self):
        """停止任务"""
        self.is_running = False

    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes}分{seconds}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"

    def run(self):
        """执行筛选任务"""
        try:
            self.is_running = True
            start_time = time.time()
            self.status_updated.emit("初始化筛选器...")
            self.screener = StockScreener(self.config)

            # 获取股票列表
            self.status_updated.emit("获取股票列表...")
            stock_list = self.screener.get_stock_list()
            if stock_list.empty:
                raise ValueError("没有获取到符合条件的股票")

            total_stocks = len(stock_list)
            self.log_updated.emit(f"共获取到 {total_stocks} 只股票")

            # 分析每只股票
            results = []
            processed_stocks = 0

            for i, (code, name) in enumerate(zip(stock_list['code'], stock_list['name'])):
                if not self.is_running:
                    break

                try:
                    # 计算速度和时间估算
                    elapsed_time = time.time() - start_time
                    if processed_stocks > 0:
                        avg_time_per_stock = elapsed_time / processed_stocks
                        stocks_remaining = total_stocks - processed_stocks
                        estimated_time_remaining = avg_time_per_stock * stocks_remaining
                        speed = processed_stocks / elapsed_time  # 每秒处理的股票数

                        status_msg = (
                            f"分析股票 {code} {name} | "
                            f"速度: {speed:.1f}只/秒 | "
                            f"已用时: {self.format_time(elapsed_time)} | "
                            f"预计剩余: {self.format_time(estimated_time_remaining)}"
                        )
                    else:
                        status_msg = f"分析股票 {code} {name}..."

                    self.status_updated.emit(status_msg)

                    # 分析股票
                    result = self.screener.analyze_single_stock((code, name))
                    if result:
                        results.append(result)
                        processed_stocks += 1

                except Exception as e:
                    self.log_updated.emit(f"分析股票 {code} {name} 失败: {str(e)}")

                # 更新进度
                progress = int((i + 1) / total_stocks * 100)
                self.progress_updated.emit(progress)

            # 处理结果
            if not self.is_running:
                self.status_updated.emit("任务已取消")
                return

            if not results:
                self.status_updated.emit("未找到符合条件的股票")
                return

            # 转换为DataFrame并排序
            df_results = pd.DataFrame(results)
            df_results = self._format_results(df_results)

            # 计算总耗时
            total_time = time.time() - start_time
            avg_speed = processed_stocks / total_time if total_time > 0 else 0

            # 发送结果和完成信息
            self.result_ready.emit(df_results)
            self.status_updated.emit(
                f"筛选完成 | 总耗时: {self.format_time(total_time)} | "
                f"平均速度: {avg_speed:.1f}只/秒"
            )

        except Exception as e:
            logger.error(f"筛选过程发生错误: {str(e)}")
            self.error_occurred.emit(str(e))
            self.status_updated.emit("筛选失败")

    def _format_results(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化结果数据"""
        try:
            # 添加衍生指标
            df['价格距离基准线'] = (df['base_price'] - df['current_price']) / df['current_price'] * 100
            df['价格距离筹码均价'] = (df['avg_cost'] - df['current_price']) / df['current_price'] * 100

            # 格式化数值列
            numeric_cols = ['current_price', 'avg_cost', 'main_force_cost',
                            'profit_ratio', 'price_position', 'volume_ratio']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"{float(x):.2f}")

            # 格式化百分比
            percent_cols = ['价格距离基准线', '价格距离筹码均价']
            for col in percent_cols:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: f"{float(x):.2f}%")

            # 转换布尔值
            df['is_trending_up'] = df['is_trending_up'].apply(
                lambda x: "上涨" if x else "下跌"
            )

            # 排序
            df = df.sort_values(['price_position', 'volume_ratio'],
                                ascending=[True, False])

            return df

        except Exception as e:
            logger.error(f"格式化结果失败: {str(e)}")
            raise