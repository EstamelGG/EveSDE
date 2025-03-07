import yaml
import time
import os

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def read_divisions_yaml(file_path):
    """读取npcCorporationDivisions.yaml文件"""
    return read_yaml(file_path)

def process_divisions_data(divisions_data, cursor, language):
    """处理NPC公司部门数据并写入数据库"""
    # 创建divisions表，只包含division_id和name字段
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS divisions (
        division_id INTEGER NOT NULL PRIMARY KEY,
        name TEXT
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM divisions')
    
    # 处理每个部门
    for division_id, division_data in divisions_data.items():
        # 获取当前语言的名称
        name = ''
        if 'nameID' in division_data:
            name = division_data['nameID'].get(language, division_data['nameID'].get('en', ''))
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO divisions 
            (division_id, name)
            VALUES (?, ?)
        ''', (
            division_id, 
            name
        )) 