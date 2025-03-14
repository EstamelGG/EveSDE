import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import sqlite3
import time

def read_stations_yaml(file_path):
    """读取 staStations.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_stations_table(cursor):
    """创建 stations 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            stationID INTEGER NOT NULL PRIMARY KEY,
            stationTypeID INTEGER,
            stationName TEXT,
            regionID INTEGER,
            solarSystemID INTEGER,
            security REAL
        )
    ''')
    
    # 创建索引以优化查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stations_solarSystemID ON stations(solarSystemID)')

def process_data(data, cursor, lang):
    """处理空间站数据并插入数据库"""
    create_stations_table(cursor)
    
    # 用于批量插入的数据
    batch_data = []
    batch_size = 1000
    
    for station in data:
        station_id = station['stationID']
        stationTypeID = station['stationTypeID']
        station_name = station['stationName']
        region_id = station['regionID']
        solar_system_id = station['solarSystemID']
        security = station['security']
        
        batch_data.append((
            station_id,
            stationTypeID,
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
                    stationTypeID,
                    stationName,
                    regionID,
                    solarSystemID,
                    security
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []
    
    # 处理剩余的批量数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO stations (
                stationID,
                stationTypeID,
                stationName,
                regionID,
                solarSystemID,
                security
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', batch_data) 