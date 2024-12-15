import sqlite3
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
register_cache_cleaner('typeDogma', clear_cache)

def read_yaml(file_path):
    """读取 typeDogma.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def create_tables(cursor):
    """创建数据库表以存储 typeAttributes 和 typeEffects"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS typeAttributes (
            type_id INTEGER,
            attribute_id INTEGER,
            value REAL,
            unitID INTEGER,
            PRIMARY KEY (type_id, attribute_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS typeEffects (
            type_id INTEGER,
            effect_id INTEGER,
            is_default BOOLEAN,
            PRIMARY KEY (type_id, effect_id)
        )
    ''')

    # 添加新表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planetResourceHarvest (
            typeid INTEGER,
            harvest_typeid INTEGER,
            PRIMARY KEY (typeid, harvest_typeid)
        )
    ''')

def process_data(data, cursor, lang):
    """处理 typeDogma 数据并插入数据库"""
    create_tables(cursor)
    
    if lang == 'en':
        # 获取 dogmaAttributes 表中的 attribute_id 和 unitID 映射
        cursor.execute('''
            SELECT attribute_id, unitID
            FROM dogmaAttributes
            WHERE unitID IS NOT NULL
        ''')
        attribute_unit_map = dict(cursor.fetchall())
        
        # 用于批量插入的数据
        attribute_batch = []
        effect_batch = []
        harvest_batch = []
        batch_size = 1000
        
        for type_id, details in data.items():
            # 处理 dogmaAttributes 数据
            if 'dogmaAttributes' in details:
                for attribute in details['dogmaAttributes']:
                    attribute_id = attribute['attributeID']
                    value = attribute['value']
                    unit_id = attribute_unit_map.get(attribute_id)  # 获取对应的 unitID
                    
                    attribute_batch.append((type_id, attribute_id, value, unit_id))
                    
                    # 特殊处理 attribute_id = 709 的情况
                    if attribute_id == 709:
                        harvest_typeid = int(value)
                        harvest_batch.append((harvest_typeid, type_id))
                    
                    # 当达到批处理大小时执行插入
                    if len(attribute_batch) >= batch_size:
                        cursor.executemany('''
                            INSERT OR REPLACE INTO typeAttributes (type_id, attribute_id, value, unitID)
                            VALUES (?, ?, ?, ?)
                        ''', attribute_batch)
                        attribute_batch = []
            
            # 处理 dogmaEffects 数据
            if 'dogmaEffects' in details:
                for effect in details['dogmaEffects']:
                    effect_batch.append((type_id, effect['effectID'], effect['isDefault']))
                    
                    # 当达到批处理大小时执行插入
                    if len(effect_batch) >= batch_size:
                        cursor.executemany('''
                            INSERT OR REPLACE INTO typeEffects (type_id, effect_id, is_default)
                            VALUES (?, ?, ?)
                        ''', effect_batch)
                        effect_batch = []
                        
            # 处理 planetResourceHarvest 数据
            if harvest_batch and len(harvest_batch) >= batch_size:
                cursor.executemany('''
                    INSERT OR REPLACE INTO planetResourceHarvest (typeid, harvest_typeid)
                    VALUES (?, ?)
                ''', harvest_batch)
                harvest_batch = []
        
        # 处理剩余的批量数据
        if attribute_batch:
            cursor.executemany('''
                INSERT OR REPLACE INTO typeAttributes (type_id, attribute_id, value, unitID)
                VALUES (?, ?, ?, ?)
            ''', attribute_batch)
        
        if effect_batch:
            cursor.executemany('''
                INSERT OR REPLACE INTO typeEffects (type_id, effect_id, is_default)
                VALUES (?, ?, ?)
            ''', effect_batch)
        
        if harvest_batch:
            cursor.executemany('''
                INSERT OR REPLACE INTO planetResourceHarvest (typeid, harvest_typeid)
                VALUES (?, ?)
            ''', harvest_batch)
    else:
        # 对于非英文数据库，从英文数据库复制表
        try:
            # 删除现有表（如果存在）
            cursor.execute('DROP TABLE IF EXISTS typeAttributes')
            cursor.execute('DROP TABLE IF EXISTS typeEffects')
            cursor.execute('DROP TABLE IF EXISTS planetResourceHarvest')
            
            # 从英文数据库复制表
            cursor.execute('ATTACH DATABASE "output/db/item_db_en.sqlite" AS en_db')
            
            cursor.execute('''
                CREATE TABLE typeAttributes AS 
                SELECT * FROM en_db.typeAttributes
            ''')
            
            cursor.execute('''
                CREATE TABLE typeEffects AS 
                SELECT * FROM en_db.typeEffects
            ''')
            
            cursor.execute('''
                CREATE TABLE planetResourceHarvest AS 
                SELECT * FROM en_db.planetResourceHarvest
            ''')
            
            cursor.execute('DETACH DATABASE en_db')
            
            print(f"已从英文数据库复制 typeDogma 相关表到 {lang} 数据库")
        except Exception as e:
            print(f"复制表时出错: {str(e)}")