import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import sqlite3
import time
from cache_manager import register_cache_cleaner

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('stations_handler', clear_cache)

def read_yaml(file_path):
    """读取 stations.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def create_stations_table(cursor):
    """创建 stations 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            stationID INTEGER PRIMARY KEY,
            stationName TEXT,
            regionID INTEGER,
            solarSystemID INTEGER,
            security REAL
        )
    ''')

def process_data(data, cursor, lang):
    """处理空间站数据并插入数据库"""
    create_stations_table(cursor)
    
    # 用于批量插入的数据
    batch_data = []
    batch_size = 1000
    
    for station in data:
        station_id = station['stationID']
        station_name = station['stationName']
        region_id = station['regionID']
        solar_system_id = station['solarSystemID']
        security = station['security']
        
        batch_data.append((
            station_id,
            station_name,
            region_id,
            solar_system_id,
            security
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO stations (
                    stationID,
                    stationName,
                    regionID,
                    solarSystemID,
                    security
                ) VALUES (?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []
    
    # 处理剩余的批量数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO stations (
                stationID,
                stationName,
                regionID,
                solarSystemID,
                security
            ) VALUES (?, ?, ?, ?, ?)
        ''', batch_data) 