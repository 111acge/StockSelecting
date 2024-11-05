from datetime import datetime, timedelta

DEFAULT_CONFIG = {
    'data': {
        'start_date': (datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
        'end_date': datetime.now().strftime('%Y%m%d'),
        'min_data_length': 30,
        'min_trading_amount': 1000000
    },
    'filter_switches': {
        'exclude_st': True,          # 排除ST股票
        'exclude_gem': True,         # 排除创业板
        'exclude_star': True,        # 排除科创板
        'exclude_bse': True          # 排除北交所
    },
    'technical': {
        'moving_averages': {  # 五线谱参数
            'ma5': 5,    # 5日均线
            'ma10': 10,  # 10日均线
            'ma20': 20,  # 20日均线
            'ma30': 30,  # 30日均线
            'ma60': 60   # 60日均线
        }
    },
    'system': {
        'max_workers': 24,          # 增加并发数
        'chunk_size': 512,           # 分块大小
        'memory_limit': 16*1024**3,    # 内存限制
        'cache_enabled': True,      # 启用缓存
        'cache_ttl': 3600,         # 缓存有效期
        'retry_times': 3,
        'retry_delay': 1,
        'request_delay': (0.1, 0.3)  # 减小请求延迟
    }
}