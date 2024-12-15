import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from typing import Dict, Optional, List

# 用于缓存星域(groupID=3)的数据
_regions_data: List[Dict] = []

def read_yaml(file_path: str = 'Data/sde/bsd/invUniqueNames.yaml') -> list:
    """读取 invUniqueNames.yaml 文件"""
    start_time = time.time()
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_table(cursor):
    """创建星域表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regions (
            regionID INTEGER PRIMARY KEY,
            regionName TEXT
        )
    ''')

def process_data(data: list, cursor, lang: str):
    """处理星域数据并插入到数据库"""
    global _regions_data
    
    # 创建表（无论是什么语言都需要创建表）
    create_table(cursor)
    
    # 只在处理英文数据时处理和缓存数据
    if lang == 'en':
        # 清空缓存
        _regions_data.clear()
        
        # 处理数据并缓存星域记录
        batch_data = []
        batch_size = 1000
        
        for item in data:
            if isinstance(item, dict) and all(key in item for key in ['itemID', 'itemName']):
                if item['groupID'] == 3:  # groupID=3 表示星域数据
                    batch_data.append((item['itemID'], item['itemName']))
                    _regions_data.append(item)
                    
                    if len(batch_data) >= batch_size:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                            batch_data
                        )
                        batch_data = []
        
        # 处理剩余的数据
        if batch_data:
            cursor.executemany(
                'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                batch_data
            )
    else:
        # 非英文数据库，直接从缓存中插入数据
        if _regions_data:
            batch_data = [(item['itemID'], item['itemName']) for item in _regions_data]
            cursor.executemany(
                'INSERT OR REPLACE INTO regions (regionID, regionName) VALUES (?, ?)',
                batch_data
            ) 