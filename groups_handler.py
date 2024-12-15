import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from cache_manager import register_cache_cleaner

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('groups', clear_cache)

def read_yaml(file_path):
    """读取 groups.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def create_groups_table(cursor):
    """创建 groups 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            name TEXT,
            iconID INTEGER,
            categoryID INTEGER,
            anchorable BOOLEAN,
            anchored BOOLEAN,
            fittableNonSingleton BOOLEAN,
            published BOOLEAN,
            useBasePrice BOOLEAN,
            icon_filename TEXT
        )
    ''')

def process_data(groups_data, cursor, lang):
    """处理 groups 数据并插入数据库（针对单一语言）"""
    create_groups_table(cursor)

    for group_id, item in groups_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        if name is None:
            continue

        categoryID = item['categoryID']
        iconID = item.get('iconID', 0)
        anchorable = item['anchorable']
        anchored = item['anchored']
        fittableNonSingleton = item['fittableNonSingleton']
        published = item['published']
        useBasePrice = item['useBasePrice']

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO groups (group_id, name, categoryID, iconID, anchorable, anchored, fittableNonSingleton, published, useBasePrice, icon_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (group_id, name, categoryID, iconID, anchorable, anchored, fittableNonSingleton, published, useBasePrice, "items_73_16_50.png"))