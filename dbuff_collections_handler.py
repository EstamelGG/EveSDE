# -*- coding: utf-8 -*-
import yaml
import json
import sqlite3
import re
import codecs
import time

# 操作名称映射到操作ID
OPERATION_MAP = {
    "preassign": -1,
    "premul": 0,
    "prediv": 1,
    "modadd": 2,
    "modsub": 3,
    "postmul": 4,
    "postdiv": 5,
    "postpercent": 6,
    "postassign": 7
}

def read_yaml(file_path):
    """读取 dbuffCollections.yaml 文件"""
    start_time = time.time()
    
    with codecs.open(file_path, 'r', 'utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print("读取 %s 耗时: %.2f 秒" % (file_path, end_time - start_time))
    return data

def get_warfare_buff_mapping(cursor):
    """
    从数据库获取warfare buff的映射关系
    
    Returns:
        dict: warfare buff ID到Value ID的映射
        dict: dbuff_id到type_id列表的映射
    """
    print("正在获取warfare buff映射关系...")
    
    # 获取所有warfare buff相关的attribute_id
    cursor.execute('''
        SELECT da.attribute_id, name 
        FROM dogmaAttributes AS da 
        WHERE name like "warfareBuff%"
    ''')
    
    warfare_attributes = cursor.fetchall()
    
    # 创建ID到Value的映射
    buff_mapping = {}
    buff_ids = []
    
    for attr_id, name in warfare_attributes:
        if name.endswith('ID'):
            # 提取数字部分，如 warfareBuff1ID -> 1
            buff_num = re.search(r'warfareBuff(\d+)ID', name)
            if buff_num:
                buff_num = buff_num.group(1)
                # 查找对应的Value属性
                value_name = f"warfareBuff{buff_num}Value"
                for v_attr_id, v_name in warfare_attributes:
                    if v_name == value_name:
                        buff_mapping[attr_id] = v_attr_id
                        buff_ids.append(attr_id)
                        break
    
    print(f"找到 {len(buff_mapping)} 个warfare buff映射关系")
    
    # 获取所有相关的type_id和dbuff_id关系
    if buff_ids:
        placeholders = ','.join(['?' for _ in buff_ids])
        cursor.execute(f'''
            SELECT ta.type_id, ta.attribute_id, ta.value 
            FROM typeAttributes AS ta 
            WHERE attribute_id in ({placeholders}) and value > 0
        ''', buff_ids)
        
        type_dbuff_mapping = {}
        warfare_results = cursor.fetchall()
        
        for type_id, attr_id, dbuff_id in warfare_results:
            dbuff_id = int(dbuff_id)
            if dbuff_id not in type_dbuff_mapping:
                type_dbuff_mapping[dbuff_id] = []
            type_dbuff_mapping[dbuff_id].append({
                'type_id': type_id,
                'buff_attr_id': attr_id,
                'value_attr_id': buff_mapping.get(attr_id, 0)
            })
        
        print(f"找到 {len(warfare_results)} 个type与dbuff的关联关系")
        
    return buff_mapping, type_dbuff_mapping

def create_dbuff_collection_table(cursor):
    """创建 dbuffCollection 表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dbuffCollection (
        dbuff_id INTEGER NOT NULL,
        type_id INTEGER NOT NULL,
        dbuff_name TEXT,
        aggregateMode TEXT,
        modifier_info TEXT,
        PRIMARY KEY (dbuff_id, type_id)
    )
    ''')

def parse_modifiers(dbuff_data, modifying_attribute_id):
    """
    解析dbuff数据中的修饰器信息
    
    Args:
        dbuff_data: dbuff数据
        modifying_attribute_id: 修饰属性ID
        
    Returns:
        list: 修饰器列表
    """
    modifiers = []
    operation_str = dbuff_data.get('operationName', 'postMul').lower()
    if operation_str in OPERATION_MAP.keys():
        operation = OPERATION_MAP[operation_str]
    else:
        print(f"未找到 {operation_str} 的 operation, 请检查")
        operation = 4  # 默认为postmul
    
    # 处理itemModifiers
    if 'itemModifiers' in dbuff_data and dbuff_data['itemModifiers']:
        for modifier in dbuff_data['itemModifiers']:
            if 'dogmaAttributeID' in modifier:
                modifiers.append({
                    "domain": "shipID",
                    "func": "ItemModifier",
                    "modifiedAttributeID": modifier['dogmaAttributeID'],
                    "modifyingAttributeID": modifying_attribute_id,
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
                    "modifyingAttributeID": modifying_attribute_id,
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
                    "modifyingAttributeID": modifying_attribute_id,
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
                    "modifyingAttributeID": modifying_attribute_id,
                    "skillTypeID": modifier['skillID'],
                    "operation": operation
                })
    
    return modifiers

def process_data(data, cursor, lang):
    """处理 dbuffCollections 数据并插入数据库（针对单一语言）"""
    create_dbuff_collection_table(cursor)
    
    # 获取warfare buff映射关系
    buff_mapping, type_dbuff_mapping = get_warfare_buff_mapping(cursor)
    
    # 清空表
    cursor.execute('DELETE FROM dbuffCollection')
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for dbuff_id, dbuff_data in data.items():
        dbuff_id = int(dbuff_id)
        
        # 提取developerDescription并仅保留英文字母作为dbuff_name
        if 'developerDescription' in dbuff_data:
            dev_desc = dbuff_data['developerDescription']
            dbuff_name = re.sub(r'[^a-zA-Z]', '', dev_desc)
        else:
            dbuff_name = "dbuff_" + str(dbuff_id)

        if 'aggregateMode' in dbuff_data:
            aggregateMode = dbuff_data['aggregateMode']
        else:
            aggregateMode = None

        # 检查是否有对应的type_id关系
        if dbuff_id in type_dbuff_mapping:
            # 为每个type_id创建一条记录
            for type_info in type_dbuff_mapping[dbuff_id]:
                type_id = type_info['type_id']
                modifying_attribute_id = type_info['value_attr_id']
                
                # 解析修饰器信息
                modifiers = parse_modifiers(dbuff_data, modifying_attribute_id)
                
                # 将修饰器列表转换为JSON字符串
                modifier_info = json.dumps(modifiers)
                
                # 添加到批量数据
                batch_data.append((dbuff_id, type_id, dbuff_name, aggregateMode, modifier_info))
                
                # 当达到批处理大小时执行插入
                if len(batch_data) >= batch_size:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO dbuffCollection (
                            dbuff_id, type_id, dbuff_name, aggregateMode, modifier_info
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', batch_data)
                    batch_data = []  # 清空批处理列表
        # 如果没有找到对应的type_id关系，跳过该记录（不写入type_id为0的记录）
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO dbuffCollection (
                dbuff_id, type_id, dbuff_name, aggregateMode, modifier_info
            ) VALUES (?, ?, ?, ?, ?)
        ''', batch_data)
    
    print("已处理 %d 个dbuff集合，语言: %s" % (len(data), lang))
