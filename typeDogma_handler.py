import sqlite3
from ruamel.yaml import YAML

# 解析 YAML 文件
yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 typeDogma.yaml 文件并返回数据"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)

def create_tables(cursor):
    """创建数据库表以存储 typeAttributes 和 typeEffects"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS typeAttributes (
            type_id INTEGER,
            attribute_id INTEGER,
            value REAL,
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

def insert_data(data, cursor):
    """将 typeDogma.yaml 数据插入到数据库中"""
    for type_id, details in data.items():
        # 插入 dogmaAttributes 数据
        if 'dogmaAttributes' in details:
            for attribute in details['dogmaAttributes']:
                cursor.execute('''
                    INSERT OR REPLACE INTO typeAttributes (type_id, attribute_id, value)
                    VALUES (?, ?, ?)
                ''', (type_id, attribute['attributeID'], attribute['value']))
                
                # 特殊处理 attribute_id = 709 的情况
                if attribute['attributeID'] == 709:
                    harvest_typeid = int(attribute['value'])
                    cursor.execute('''
                        INSERT OR REPLACE INTO planetResourceHarvest (typeid, harvest_typeid)
                        VALUES (?, ?)
                    ''', (harvest_typeid, type_id))

        # 插入 dogmaEffects 数据
        if 'dogmaEffects' in details:
            for effect in details['dogmaEffects']:
                cursor.execute('''
                    INSERT OR REPLACE INTO typeEffects (type_id, effect_id, is_default)
                    VALUES (?, ?, ?)
                ''', (type_id, effect['effectID'], effect['isDefault']))

def process_data(data, cursor, lang):
    """处理 typeDogma 数据并插入数据库"""
    create_tables(cursor)
    insert_data(data, cursor)