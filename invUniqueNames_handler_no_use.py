import yaml
import time
from typing import Dict, Optional

# 用于缓存数据的全局变量
_cached_data: Optional[list] = None

def read_yaml(file_path: str = 'Data/sde/bsd/invUniqueNames.yaml') -> list:
    """读取 invUniqueNames.yaml 文件，使用缓存避免重复读取"""
    start_time = time.time()
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.safe_load(file)
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def process_data(data: list, cursor, lang: str):
    """处理 invUniqueNames 数据并插入到数据库"""
    # 只在处理英文数据时创建表和插入数据，因为这个表不需要多语言
    if lang != 'en':
        return
        
    # 创建 invUniqueNames 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invUniqueNames (
            groupID INTEGER,
            itemID INTEGER PRIMARY KEY,
            itemName TEXT
        )
    ''')

    # 插入数据
    for item in data:
        if isinstance(item, dict) and all(key in item for key in ['groupID', 'itemID', 'itemName']):
            cursor.execute(
                'INSERT OR REPLACE INTO invUniqueNames (groupID, itemID, itemName) VALUES (?, ?, ?)',
                (item['groupID'], item['itemID'], item['itemName'])
            )