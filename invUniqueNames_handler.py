import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
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
            _cached_data = yaml.load(file, Loader=SafeLoader)
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def process_data(data: list, cursor, lang: str):
    """处理 invUniqueNames 数据并插入到数据库"""
    # 创建 invUniqueNames 表（仅在处理英文数据时）
    if lang == 'en':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invUniqueNames (
                groupID INTEGER,
                itemID INTEGER PRIMARY KEY,
                itemName TEXT
            )
        ''')

        # 准备批量插入的数据
        batch_size = 1000
        valid_items = []
        total_items = len(data)
        
        # 收集有效数据
        for item in data:
            if isinstance(item, dict) and all(key in item for key in ['groupID', 'itemID', 'itemName']):
                valid_items.append((item['groupID'], item['itemID'], item['itemName']))
        
        # 批量插入数据
        for i in range(0, len(valid_items), batch_size):
            batch = valid_items[i:i + batch_size]
            cursor.executemany(
                'INSERT OR REPLACE INTO invUniqueNames (groupID, itemID, itemName) VALUES (?, ?, ?)',
                batch
            )
            
            # 计算并显示进度
            progress = (i + len(batch)) / total_items * 100
            print(f"\r处理进度: {progress:.2f}%", end='', flush=True)
        
        print("\n数据插入完成")
            
    else:
        # 对于非英文数据库，从英文数据库复制表
        try:
            # 删除目标表（如果存在）
            cursor.execute('DROP TABLE IF EXISTS invUniqueNames')
            
            # 从英文数据库复制表
            cursor.execute('ATTACH DATABASE "output/db/item_db_en.sqlite" AS en_db')
            
            cursor.execute('''
                CREATE TABLE invUniqueNames AS 
                SELECT * FROM en_db.invUniqueNames
            ''')
            
            cursor.execute('DETACH DATABASE en_db')
            
            print(f"已从英文数据库复制 invUniqueNames 表到 {lang} 数据库")
        except Exception as e:
            print(f"复制表时出错: {str(e)}")