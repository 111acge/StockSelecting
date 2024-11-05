import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from pathlib import Path
import time
import random
import gc
import psutil
from datetime import datetime
from collections import defaultdict
from contextlib import contextmanager
import logging
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


def retry_on_exception(retries=3, delay_base=1):
    """装饰器: 在发生异常时进行重试"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"{func.__name__} 第{attempt + 1}次尝试失败: {str(e)}")
                    if attempt < retries - 1:
                        delay = delay_base * (1 + random.random())
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


class StockScreener:
    def __init__(self, config: Dict):
        """
        初始化股票筛选器

        参数:
            config (Dict): 配置字典，包含筛选参数
        """
        self.config = config
        self.max_workers = config['system'].get('max_workers', 24)
        self.chunk_size = config['system'].get('chunk_size', 512)
        self.memory_limit = config['system'].get('memory_limit', 16*1024**3)

        # 缓存设置
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = {}

        # 性能统计
        self.performance_stats = defaultdict(list)

        # 初始化统计信息
        self.statistics = {
            'total_stocks': 0,
            'filtered_stocks': 0,
            'filtered_details': {},
            'processed_stocks': 0,
            'successful_stocks': 0,
            'failed_stocks': 0
        }

        logger.info(f"初始化股票筛选器 - 最大并发数: {self.max_workers}, 分块大小: {self.chunk_size}")
        logger.debug(f"筛选配置: {config}")

    def _measure_time(self, func_name: str) -> contextmanager:
        """测量函数执行时间的上下文管理器"""

        @contextmanager
        def timer():
            start_time = time.time()
            yield
            execution_time = time.time() - start_time
            self.performance_stats[func_name].append(execution_time)

        return timer()

    def _clear_cache_if_needed(self):
        """如果内存使用过高则清理缓存"""
        process = psutil.Process()
        if process.memory_info().rss > self.memory_limit:
            logger.warning("内存使用过高，清理缓存...")
            self.cache.clear()
            gc.collect()

    def _get_cached_data(self, stock_code: str, cache_key: str) -> Optional[pd.DataFrame]:
        """获取缓存的数据"""
        cache_file = self.cache_dir / f"{stock_code}_{cache_key}.pkl"
        if cache_file.exists():
            try:
                return pd.read_pickle(cache_file)
            except Exception as e:
                logger.warning(f"读取缓存失败 {stock_code}: {e}")
                return None
        return None

    def _save_to_cache(self, stock_code: str, cache_key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        try:
            cache_file = self.cache_dir / f"{stock_code}_{cache_key}.pkl"
            data.to_pickle(cache_file)
        except Exception as e:
            logger.warning(f"保存缓存失败 {stock_code}: {e}")

    @retry_on_exception(retries=3, delay_base=1)
    def _get_stock_data(self, stock_code: str) -> pd.DataFrame:
        """获取股票数据，带缓存和重试机制"""
        cache_key = f"{self.config['data']['start_date']}_{self.config['data']['end_date']}"

        # 尝试从缓存获取
        cached_data = self._get_cached_data(stock_code, cache_key)
        if cached_data is not None:
            return cached_data

        # 获取新数据
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=self.config['data']['start_date'],
                end_date=self.config['data']['end_date'],
                adjust="qfq"
            )

            # 保存到缓存
            self._save_to_cache(stock_code, cache_key, df)
            return df

        except Exception as e:
            logger.error(f"获取股票数据失败 {stock_code}: {e}")
            raise

    def _apply_filter(self, df: pd.DataFrame, condition: pd.Series, filter_name: str) -> pd.DataFrame:
        """
        应用过滤条件并记录统计信息
        """
        original_count = len(df)
        df = df[condition]
        filtered_count = original_count - len(df)

        # 记录统计信息
        self.statistics['filtered_details'][filter_name] = {
            'removed': filtered_count,
            'remaining': len(df)
        }

        logger.info(f"{filter_name}: 过滤 {filtered_count} 只股票, 剩余 {len(df)} 只")
        return df

    def get_stock_list(self) -> pd.DataFrame:
        """获取并过滤A股股票列表"""
        try:
            logger.info("开始获取股票列表...")

            # 禁用 tqdm 进度条
            import tqdm
            original_tqdm = tqdm.tqdm
            tqdm.tqdm = lambda *args, **kwargs: args[0]

            try:
                # 获取股票列表，改用更可靠的方式
                stock_info = ak.stock_info_a_code_name()

                # 验证数据
                if stock_info is None or not isinstance(stock_info, pd.DataFrame) or stock_info.empty:
                    logger.error("获取股票列表失败: 返回数据无效")
                    return pd.DataFrame()

                # 确保必要的列存在
                required_columns = ['code', 'name']
                if not all(col in stock_info.columns for col in required_columns):
                    logger.error("获取股票列表失败: 数据格式不正确")
                    return pd.DataFrame()

            except Exception as e:
                logger.error(f"获取股票列表时发生错误: {str(e)}")
                return pd.DataFrame()
            finally:
                # 恢复 tqdm
                tqdm.tqdm = original_tqdm

            # 记录初始数量
            self.statistics['total_stocks'] = len(stock_info)
            logger.info(f"获取到原始股票数量: {self.statistics['total_stocks']}")

            # 应用过滤条件
            filter_switches = self.config['filter_switches']

            try:
                if filter_switches['exclude_st']:
                    stock_info = self._apply_filter(
                        stock_info,
                        ~stock_info['name'].str.contains('ST|\\*ST', case=False, na=False),
                        '排除ST股票'
                    )

                if filter_switches['exclude_gem']:
                    stock_info = self._apply_filter(
                        stock_info,
                        ~stock_info['code'].str.startswith('300'),
                        '排除创业板'
                    )

                if filter_switches['exclude_star']:
                    stock_info = self._apply_filter(
                        stock_info,
                        ~stock_info['code'].str.startswith('688'),
                        '排除科创板'
                    )

                if filter_switches['exclude_bse']:
                    stock_info = self._apply_filter(
                        stock_info,
                        ~stock_info['code'].str.startswith('8'),
                        '排除北交所'
                    )

                # 更新最终过滤统计
                self.statistics['filtered_stocks'] = len(stock_info)
                filtered_total = self.statistics['total_stocks'] - self.statistics['filtered_stocks']

                # 输出统计信息
                logger.info("====== 股票过滤统计 ======")
                logger.info(f"初始股票总数: {self.statistics['total_stocks']}")
                for filter_name, stats in self.statistics['filtered_details'].items():
                    logger.info(f"{filter_name}: 排除 {stats['removed']} 只")
                logger.info(f"最终剩余数量: {self.statistics['filtered_stocks']}")
                logger.info(
                    f"总计过滤掉: {filtered_total} 只股票 ({filtered_total / self.statistics['total_stocks'] * 100:.2f}%)")
                logger.info("=========================")

                if stock_info.empty:
                    logger.warning("过滤后没有符合条件的股票")
                    return pd.DataFrame()

                return stock_info

            except Exception as e:
                logger.error(f"应用过滤条件时发生错误: {str(e)}")
                logger.exception("详细错误信息:")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            logger.exception("详细错误信息:")
            return pd.DataFrame()

    def calculate_chip_distribution(self, stock_code: str) -> Optional[Dict]:
        """
        计算股票筹码分布

        参数:
            stock_code (str): 股票代码

        返回:
            Dict: 包含筹码分布信息的字典，计算失败返回 None
        """
        try:
            with self._measure_time('calculate_chip_distribution'):
                # 获取数据
                df = self._get_stock_data(stock_code)
                if len(df) < self.config['data']['min_data_length']:
                    return None

                # 计算筹码分布
                current_price = df['收盘'].iloc[-1]
                volume_price_df = df.copy()

                # 计算成本分布
                volume_price_df['成交额'] = volume_price_df['成交量'] * volume_price_df['收盘']
                total_volume = volume_price_df['成交量'].sum()

                if total_volume == 0:
                    logger.warning(f"{stock_code} 总成交量为0，跳过")
                    return None

                # 计算均价成本
                avg_cost = volume_price_df['成交额'].sum() / total_volume

                # 计算获利盘比例
                profit_volume = volume_price_df[volume_price_df['收盘'] <= current_price]['成交量'].sum()
                profit_ratio = profit_volume / total_volume if total_volume > 0 else 0

                # 计算主力成本
                recent_days = 20  # 最近20天
                if len(df) >= recent_days:
                    recent_df = volume_price_df.tail(recent_days)
                    main_force_cost = (recent_df['成交额'].sum() / recent_df['成交量'].sum()) if recent_df[
                                                                                                     '成交量'].sum() > 0 else 0
                else:
                    main_force_cost = avg_cost

                return {
                    'current_price': current_price,
                    'avg_cost': avg_cost,
                    'main_force_cost': main_force_cost,
                    'profit_ratio': profit_ratio,
                    'total_volume': total_volume
                }

        except Exception as e:
            logger.error(f"计算筹码分布失败 {stock_code}: {e}")
            return None

    def calculate_pentagram(self, stock_code: str) -> Optional[Dict]:
        """
        计算五线谱数据

        参数:
            stock_code (str): 股票代码

        返回:
            Dict: 包含五线谱数据的字典，计算失败返回 None
        """
        try:
            with self._measure_time('calculate_pentagram'):
                # 获取数据
                df = self._get_stock_data(stock_code)
                ma_config = self.config['technical']['moving_averages']

                if len(df) < ma_config['ma60']:  # 使用最长的均线周期判断
                    return None

                # 计算五线均线
                current_price = df['收盘'].iloc[-1]
                volume_ma5 = df['成交量'].rolling(window=5).mean().iloc[-1]
                volume_ma20 = df['成交量'].rolling(window=20).mean().iloc[-1]

                # 计算各均线
                ma_values = {}
                for ma_name, period in ma_config.items():
                    ma_values[ma_name] = df['收盘'].rolling(window=period).mean().iloc[-1]

                # 判断趋势
                is_trending_up = (
                        ma_values['ma5'] > ma_values['ma10'] >
                        ma_values['ma20'] > ma_values['ma30'] >
                        ma_values['ma60']
                )

                # 计算均线标准差
                price_std = df['收盘'].tail(20).std()  # 使用近20天计算标准差

                # 计算量比
                volume_ratio = volume_ma5 / volume_ma20 if volume_ma20 > 0 else 0

                return {
                    'current_price': current_price,
                    'ma_values': ma_values,
                    'volume_ratio': volume_ratio,
                    'price_std': price_std,
                    'is_trending_up': is_trending_up,
                    'base_price': ma_values['ma20'],  # 使用20日均线作为基准线
                    'support_price': ma_values['ma60']  # 使用60日均线作为支撑线
                }

        except Exception as e:
            logger.error(f"计算五线谱失败 {stock_code}: {e}")
            return None

    def analyze_single_stock(self, stock_info: Tuple[str, str]) -> Optional[Dict]:
        """
        分析单个股票

        参数:
            stock_info: (股票代码, 股票名称)的元组

        返回:
            Dict: 包含分析结果的字典，分析失败返回 None
        """
        stock_code, stock_name = stock_info
        self._clear_cache_if_needed()

        try:
            with self._measure_time('analyze_single_stock'):
                # 计算筹码分布
                chip_data = self.calculate_chip_distribution(stock_code)
                if not chip_data:
                    return None

                # 计算五线谱
                pentagram_data = self.calculate_pentagram(stock_code)
                if not pentagram_data:
                    return None

                current_price = pentagram_data['current_price']

                # 判断是否满足条件
                if (current_price < chip_data['avg_cost'] and  # 股价低于筹码均价
                        current_price > pentagram_data['support_price'] and  # 股价高于支撑线
                        current_price < pentagram_data['base_price']):  # 股价低于基准线

                    return {
                        'code': stock_code,
                        'name': stock_name,
                        'current_price': current_price,
                        'avg_cost': chip_data['avg_cost'],
                        'main_force_cost': chip_data['main_force_cost'],
                        'profit_ratio': chip_data['profit_ratio'],
                        'base_price': pentagram_data['base_price'],
                        'support_price': pentagram_data['support_price'],
                        'price_position': (current_price - pentagram_data['support_price']) /
                                          (pentagram_data['base_price'] - pentagram_data['support_price']),
                        'volume_ratio': pentagram_data['volume_ratio'],
                        'is_trending_up': pentagram_data['is_trending_up']
                    }

                return None

        except Exception as e:
            logger.error(f"分析股票失败 {stock_code} {stock_name}: {e}")
            return None

    def _process_chunk(self, stock_chunk: List[Tuple[str, str]]) -> List[Dict]:
        """
        处理一个股票分块

        参数:
            stock_chunk: 股票代码和名称的列表

        返回:
            List[Dict]: 分析结果列表
        """
        chunk_results = []
        for stock_code, stock_name in stock_chunk:
            try:
                result = self.analyze_single_stock((stock_code, stock_name))
                if result:
                    chunk_results.append(result)
                    self.statistics['successful_stocks'] += 1
                self.statistics['processed_stocks'] += 1
            except Exception as e:
                logger.error(f"处理股票失败 {stock_code} {stock_name}: {e}")
                self.statistics['failed_stocks'] += 1

        return chunk_results

    def screen_stocks(self) -> pd.DataFrame:
        """
        执行股票筛选

        返回:
            pd.DataFrame: 筛选结果
        """
        # 重置统计信息
        self.statistics.update({
            'processed_stocks': 0,
            'successful_stocks': 0,
            'failed_stocks': 0
        })

        # 获取股票列表
        stock_list = self.get_stock_list()
        if stock_list.empty:
            logger.error("没有获取到符合条件的股票")
            return pd.DataFrame()

        # 将股票列表分块
        stock_chunks = []
        for i in range(0, len(stock_list), self.chunk_size):
            chunk = list(zip(
                stock_list['code'].iloc[i:i + self.chunk_size],
                stock_list['name'].iloc[i:i + self.chunk_size]
            ))
            stock_chunks.append(chunk)

        results = []
        total_chunks = len(stock_chunks)
        logger.info(f"开始处理 {total_chunks} 个股票分块...")

        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            # 提交所有任务
            for chunk in stock_chunks:
                future = executor.submit(self._process_chunk, chunk)
                futures.append(future)

            # 处理完成的任务
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                    progress = (i / total_chunks) * 100
                    logger.info(f"进度: {progress:.2f}% ({i}/{total_chunks})")
                except Exception as e:
                    logger.error(f"处理分块失败: {e}")

        # 输出统计信息
        logger.info("\n====== 筛选统计 ======")
        logger.info(f"处理股票数: {self.statistics['processed_stocks']}")
        logger.info(f"成功筛选: {self.statistics['successful_stocks']}")
        logger.info(f"处理失败: {self.statistics['failed_stocks']}")

        # 输出性能统计
        logger.info("\n====== 性能统计 ======")
        for func_name, times in self.performance_stats.items():
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                logger.info(f"{func_name}:")
                logger.info(f"  平均耗时: {avg_time:.3f}秒")
                logger.info(f"  最长耗时: {max_time:.3f}秒")
                logger.info(f"  最短耗时: {min_time:.3f}秒")

        # 清理缓存
        self._clear_cache_if_needed()

        if not results:
            logger.warning("未找到符合条件的股票")
            return pd.DataFrame()

        # 转换为DataFrame并格式化
        return self._format_results(results)

    def _format_results(self, results: List[Dict]) -> pd.DataFrame:
        """
        格式化结果数据

        参数:
            results: 原始结果列表

        返回:
            pd.DataFrame: 格式化后的结果
        """
        try:
            if not results:
                return pd.DataFrame()

            df = pd.DataFrame(results)

            # 添加衍生指标
            df['价格距离基准线'] = (df['base_price'] - df['current_price']) / df['current_price'] * 100
            df['价格距离筹码均价'] = (df['avg_cost'] - df['current_price']) / df['current_price'] * 100

            # 格式化数值列
            numeric_cols = ['current_price', 'avg_cost', 'main_force_cost',
                            'profit_ratio', 'price_position', 'volume_ratio']
            for col in numeric_cols:
                df[col] = df[col].apply(lambda x: f"{float(x):.2f}")

            # 格式化百分比列
            percent_cols = ['价格距离基准线', '价格距离筹码均价']
            for col in percent_cols:
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
            logger.error(f"格式化结果失败: {e}")
            logger.exception("详细错误信息:")
            return pd.DataFrame()
