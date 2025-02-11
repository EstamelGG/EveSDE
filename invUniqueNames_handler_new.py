import json
import sqlite3
from typing import Dict

# 支持的语言列表
LANGUAGES = ['de', 'en', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']

def read_universe_data(file_path: str = 'fetchUniverse/universe_data.json') -> dict:
    """读取 universe_data.json 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_table(cursor):
    """创建所需的表"""
    # 构建语言列的SQL片段
    lang_columns = ', '.join([f"name_{lang} TEXT" for lang in LANGUAGES])
    
    # 创建星域表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS regions (
            regionID INTEGER NOT NULL PRIMARY KEY,
            {lang_columns}
        )
    ''')
    
    # 创建星座表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS constellations (
            constellationID INTEGER NOT NULL PRIMARY KEY,
            {lang_columns}
        )
    ''')
    
    # 创建恒星系表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS solarsystems (
            solarSystemID INTEGER NOT NULL PRIMARY KEY,
            {lang_columns},
            security_status REAL
        )
    ''')

def process_data(data: dict, cursor):
    """处理数据并插入到数据库"""
    # 创建表
    create_table(cursor)
    
    # 准备SQL语句
    regions_sql = f'''
        INSERT OR REPLACE INTO regions (regionID, {', '.join([f'name_{lang}' for lang in LANGUAGES])})
        VALUES (?, {', '.join(['?' for _ in LANGUAGES])})
    '''
    
    constellations_sql = f'''
        INSERT OR REPLACE INTO constellations (constellationID, {', '.join([f'name_{lang}' for lang in LANGUAGES])})
        VALUES (?, {', '.join(['?' for _ in LANGUAGES])})
    '''
    
    solarsystems_sql = f'''
        INSERT OR REPLACE INTO solarsystems (solarSystemID, {', '.join([f'name_{lang}' for lang in LANGUAGES])}, security_status)
        VALUES (?, {', '.join(['?' for _ in LANGUAGES])}, ?)
    '''
    
    # 处理星域数据
    for region_id, region_data in data.items():
        region_names = region_data['region_name']
        region_values = [int(region_id)]
        for lang in LANGUAGES:
            region_values.append(region_names.get(lang))
        cursor.execute(regions_sql, region_values)
        
        # 处理星座数据
        for const_id, const_data in region_data['constellations'].items():
            const_names = const_data['constellation_name']
            const_values = [int(const_id)]
            for lang in LANGUAGES:
                const_values.append(const_names.get(lang))
            cursor.execute(constellations_sql, const_values)
            
            # 处理星系数据
            for sys_id, sys_data in const_data['systems'].items():
                sys_names = sys_data['system_name']
                sys_values = [int(sys_id)]
                for lang in LANGUAGES:
                    sys_values.append(sys_names.get(lang))
                sys_values.append(sys_data['system_info']['security_status'])
                cursor.execute(solarsystems_sql, sys_values)