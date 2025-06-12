# -*- coding: utf-8 -*-
import yaml
import json
import sqlite3
import re
import codecs
import time

# 操作名称映射到操作ID
OPERATION_MAP = {
    "preAssign": -1,
    "preMul": 0,
    "preDiv": 1,
    "modAdd": 2,
    "modSub": 3,
    "postMul": 4,
    "postDiv": 5,
    "postPercent": 6,
    "postAssign": 7
}

def read_yaml(file_path):
    """读取 dbuffCollections.yaml 文件"""
    start_time = time.time()
    
    with codecs.open(file_path, 'r', 'utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print("读取 %s 耗时: %.2f 秒" % (file_path, end_time - start_time))
    return data

def create_dbuff_collection_table(cursor):
    """创建 dbuffCollection 表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dbuffCollection (
        dbuff_id INTEGER NOT NULL PRIMARY KEY,
        dbuff_name TEXT,
        modifier_info TEXT
    )
    ''')

def parse_modifiers(dbuff_data):
    """
    解析dbuff数据中的修饰器信息
    
    Args:
        dbuff_data: dbuff数据
        
    Returns:
        list: 修饰器列表
    """
    modifiers = []
    operation = OPERATION_MAP.get(dbuff_data.get('operationName', 'postMul').lower(), 4)  # 默认为postMul(4)
    
    # 处理itemModifiers
    if 'itemModifiers' in dbuff_data and dbuff_data['itemModifiers']:
        for modifier in dbuff_data['itemModifiers']:
            if 'dogmaAttributeID' in modifier:
                modifiers.append({
                    "domain": "shipID",
                    "func": "ItemModifier",
                    "modifiedAttributeID": modifier['dogmaAttributeID'],
                    "modifyingAttributeID": 0,  # 暂时设为0
                    "operation": operation
                })
    
    # 处理locationModifiers
    if 'locationModifiers' in dbuff_data and dbuff_data['locationModifiers']:
        for modifier in dbuff_data['locationModifiers']:
            if 'dogmaAttributeID' in modifier:
                modifiers.append({
                    "domain": "shipID",
                    "func": "LocationModifier",
                    "modifiedAttributeID": modifier['dogmaAttributeID'],
                    "modifyingAttributeID": 0,  # 暂时设为0
                    "operation": operation
                })
    
    # 处理locationGroupModifiers
    if 'locationGroupModifiers' in dbuff_data and dbuff_data['locationGroupModifiers']:
        for modifier in dbuff_data['locationGroupModifiers']:
            if 'dogmaAttributeID' in modifier and 'groupID' in modifier:
                modifiers.append({
                    "domain": "shipID",
                    "func": "LocationGroupModifier",
                    "modifiedAttributeID": modifier['dogmaAttributeID'],
                    "modifyingAttributeID": 0,  # 暂时设为0
                    "groupID": modifier['groupID'],
                    "operation": operation
                })
    
    # 处理locationRequiredSkillModifiers
    if 'locationRequiredSkillModifiers' in dbuff_data and dbuff_data['locationRequiredSkillModifiers']:
        for modifier in dbuff_data['locationRequiredSkillModifiers']:
            if 'dogmaAttributeID' in modifier and 'skillID' in modifier:
                modifiers.append({
                    "domain": "shipID",
                    "func": "LocationRequiredSkillModifier",
                    "modifiedAttributeID": modifier['dogmaAttributeID'],
                    "modifyingAttributeID": 0,  # 暂时设为0
                    "skillTypeID": modifier['skillID'],
                    "operation": operation
                })
    
    return modifiers

def process_data(data, cursor, lang):
    """处理 dbuffCollections 数据并插入数据库（针对单一语言）"""
    create_dbuff_collection_table(cursor)
    
    # 清空表
    cursor.execute('DELETE FROM dbuffCollection')
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for dbuff_id, dbuff_data in data.items():
        # 提取developerDescription并仅保留英文字母作为dbuff_name
        if 'developerDescription' in dbuff_data:
            dev_desc = dbuff_data['developerDescription']
            dbuff_name = re.sub(r'[^a-zA-Z]', '', dev_desc)
        else:
            dbuff_name = "dbuff_" + str(dbuff_id)
        
        # 解析修饰器信息
        modifiers = parse_modifiers(dbuff_data)
        
        # 将修饰器列表转换为JSON字符串
        modifier_info = json.dumps(modifiers)
        
        # 添加到批量数据
        batch_data.append((int(dbuff_id), dbuff_name, modifier_info))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO dbuffCollection (
                    dbuff_id, dbuff_name, modifier_info
                ) VALUES (?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO dbuffCollection (
                dbuff_id, dbuff_name, modifier_info
            ) VALUES (?, ?, ?)
        ''', batch_data)
    
    print("已处理 %d 个dbuff集合，语言: %s" % (len(data), lang))
