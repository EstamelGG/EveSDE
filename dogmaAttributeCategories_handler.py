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
register_cache_cleaner('dogmaAttributeCategories_handler', clear_cache)

def read_yaml(file_path):
    """读取 dogmaAttributeCategories.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data


def create_dogma_attribute_categories_table(cursor):
    """创建 dogmaAttributeCategories 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaAttributeCategories (
            attribute_category_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
        )
    ''')


def process_data(data, cursor, lang):
    """处理 dogmaAttributeCategories 数据并插入数据库（针对单一语言）"""
    create_dogma_attribute_categories_table(cursor)

    for category_id, category_data in data.items():
        # 获取字段
        name = category_data.get('name', "")
        description = category_data.get('description', "")

        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO dogmaAttributeCategories (
                attribute_category_id, name, description
            ) VALUES (?, ?, ?)
        ''', (category_id, name, description))