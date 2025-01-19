import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from typing import Dict, Optional, List

# 用于缓存数据
_regions_data: List[Dict] = []
_constellations_data: List[Dict] = []
_solarsystems_data: List[Dict] = []

def read_yaml(file_path: str = 'Data/sde/bsd/invUniqueNames.yaml') -> list:
    """读取 invUniqueNames.yaml 文件"""
    start_time = time.time()
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_table(cursor):
    """创建所需的表"""
    # 创建星域表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regions (
            regionID INTEGER NOT NULL PRIMARY KEY,
            regionName TEXT
        )
    ''')
    
    # 创建星座表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS constellations (
            constellationID INTEGER NOT NULL PRIMARY KEY,
            constellationName TEXT
        )
    ''')
    
    # 创建恒星系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solarsystems (
            solarSystemID INTEGER NOT NULL PRIMARY KEY,
            solarSystemName TEXT
        )
    ''')

def process_data(data: list, cursor, lang: str):
    """处理数据并插入到数据库"""
    global _regions_data, _constellations_data, _solarsystems_data
    
    # 创建表（无论是什么语言都需要创建表）
    create_table(cursor)
    
    # 只在处理英文数据时处理和缓存数据
    if lang == 'en':
        # 清空缓存
        _regions_data.clear()
        _constellations_data.clear()
        _solarsystems_data.clear()
        
        # 准备批量插入的数据
        regions_batch = []
        constellations_batch = []
        solarsystems_batch = []
        batch_size = 1000
        
        for item in data:
            if isinstance(item, dict) and all(key in item for key in ['itemID', 'itemName']):
                if item['groupID'] == 3:  # 星域数据
                    regions_batch.append((item['itemID'], item['itemName']))
                    _regions_data.append(item)
                elif item['groupID'] == 4:  # 星座数据
                    constellations_batch.append((item['itemID'], item['itemName']))
                    _constellations_data.append(item)
                elif item['groupID'] == 5:  # 恒星系数据
                    solarsystems_batch.append((item['itemID'], item['itemName']))
                    _solarsystems_data.append(item)
                
                # 批量插入数据
                if len(regions_batch) >= batch_size:
                    cursor.executemany(
                        'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                        regions_batch
                    )
                    regions_batch = []
                
                if len(constellations_batch) >= batch_size:
                    cursor.executemany(
                        'INSERT OR REPLACE INTO constellations (constellationID, constellationName) VALUES (?, ?)',
                        constellations_batch
                    )
                    constellations_batch = []
                
                if len(solarsystems_batch) >= batch_size:
                    cursor.executemany(
                        'INSERT OR REPLACE INTO solarsystems (solarSystemID, solarSystemName) VALUES (?, ?)',
                        solarsystems_batch
                    )
                    solarsystems_batch = []
        
        # 处理剩余的数据
        if regions_batch:
            cursor.executemany(
                'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                regions_batch
            )
        if constellations_batch:
            cursor.executemany(
                'INSERT OR REPLACE INTO constellations (constellationID, constellationName) VALUES (?, ?)',
                constellations_batch
            )
        if solarsystems_batch:
            cursor.executemany(
                'INSERT OR REPLACE INTO solarsystems (solarSystemID, solarSystemName) VALUES (?, ?)',
                solarsystems_batch
            )
    else:
        # 非英文数据库，直接从缓存中插入数据
        if _regions_data:
            cursor.executemany(
                'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                [(item['itemID'], item['itemName']) for item in _regions_data]
            )
        if _constellations_data:
            cursor.executemany(
                'INSERT OR REPLACE INTO constellations (constellationID, constellationName) VALUES (?, ?)',
                [(item['itemID'], item['itemName']) for item in _constellations_data]
            )
        if _solarsystems_data:
            cursor.executemany(
                'INSERT OR REPLACE INTO solarsystems (solarSystemID, solarSystemName) VALUES (?, ?)',
                [(item['itemID'], item['itemName']) for item in _solarsystems_data]
            )