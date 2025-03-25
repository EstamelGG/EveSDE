import json
import sqlite3
import requests
import time
from typing import Dict, Any

def fetch_dynamic_items_data() -> Dict[str, Any]:
    """
    从hoboleak获取动态物品属性数据
    """
    url = "https://sde.hoboleaks.space/tq/dynamicitemattributes.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取动态物品属性数据失败: {e}")
        return {}

def create_dynamic_items_tables(cursor: sqlite3.Cursor):
    """
    创建动态物品属性相关的表
    """
    # 创建动态物品属性表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_item_attributes (
            type_id INTEGER,
            attribute_id INTEGER,
            min_value REAL,
            max_value REAL,
            PRIMARY KEY (type_id, attribute_id)
        )
    ''')

    # 创建动态物品映射表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_item_mappings (
            type_id INTEGER,
            applicable_type INTEGER,
            resulting_type INTEGER,
            PRIMARY KEY (type_id, applicable_type)
        )
    ''')

def process_data(cursor: sqlite3.Cursor):
    """
    处理动态物品数据并插入到数据库
    """
    start_time = time.time()
    print("开始处理动态物品属性数据...")

    # 获取数据
    data = fetch_dynamic_items_data()
    if not data:
        print("未获取到动态物品属性数据，处理终止")
        return

    # 创建表
    create_dynamic_items_tables(cursor)

    # 用于批量插入的数据列表
    attributes_batch = []
    mappings_batch = []
    batch_size = 1000

    # 遍历所有动态物品
    for type_id_str, item_data in data.items():
        type_id = int(type_id_str)
        
        # 处理属性数据
        if "attributeIDs" in item_data:
            for attr_id, attr_data in item_data["attributeIDs"].items():
                attributes_batch.append((
                    type_id,
                    int(attr_id),
                    round(attr_data.get("min", 0.0), 4),
                    round(attr_data.get("max", 0.0), 4)
                ))

        # 处理映射数据
        if "inputOutputMapping" in item_data:
            for mapping in item_data["inputOutputMapping"]:
                resulting_type = mapping.get("resultingType")
                if resulting_type and "applicableTypes" in mapping:
                    for applicable_type in mapping["applicableTypes"]:
                        mappings_batch.append((
                            type_id,
                            applicable_type,
                            resulting_type
                        ))

        # 批量插入属性数据
        if len(attributes_batch) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO dynamic_item_attributes 
                (type_id, attribute_id, min_value, max_value)
                VALUES (?, ?, ?, ?)
            ''', attributes_batch)
            attributes_batch = []

        # 批量插入映射数据
        if len(mappings_batch) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO dynamic_item_mappings
                (type_id, applicable_type, resulting_type)
                VALUES (?, ?, ?)
            ''', mappings_batch)
            mappings_batch = []

    # 处理剩余的批次数据
    if attributes_batch:
        cursor.executemany('''
            INSERT OR REPLACE INTO dynamic_item_attributes 
            (type_id, attribute_id, min_value, max_value)
            VALUES (?, ?, ?, ?)
        ''', attributes_batch)

    if mappings_batch:
        cursor.executemany('''
            INSERT OR REPLACE INTO dynamic_item_mappings
            (type_id, applicable_type, resulting_type)
            VALUES (?, ?, ?)
        ''', mappings_batch)

    end_time = time.time()
    print(f"动态物品属性数据处理完成，耗时: {end_time - start_time:.2f} 秒") 