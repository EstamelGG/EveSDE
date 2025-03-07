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
    # 构建语言列的SQL片段 - regions表
    region_lang_columns = ', '.join([f"regionName_{lang} TEXT" for lang in LANGUAGES])
    
    # 构建语言列的SQL片段 - constellations表
    constellation_lang_columns = ', '.join([f"constellationName_{lang} TEXT" for lang in LANGUAGES])
    
    # 构建语言列的SQL片段 - solarsystems表
    system_lang_columns = ', '.join([f"solarSystemName_{lang} TEXT" for lang in LANGUAGES])
    
    # 创建星域表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS regions (
            regionID INTEGER NOT NULL PRIMARY KEY,
            regionName TEXT,  -- 英文名称
            {region_lang_columns}
        )
    ''')
    
    # 创建星座表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS constellations (
            constellationID INTEGER NOT NULL PRIMARY KEY,
            constellationName TEXT,  -- 英文名称
            {constellation_lang_columns}
        )
    ''')
    
    # 创建恒星系表
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS solarsystems (
            solarSystemID INTEGER NOT NULL PRIMARY KEY,
            solarSystemName TEXT,  -- 英文名称
            {system_lang_columns},
            security_status REAL
        )
    ''')

def process_data(data: dict, cursor, lang: str = 'en'):
    """
    处理数据并插入到数据库
    
    Args:
        data: 数据字典
        cursor: 数据库游标
        lang: 数据库使用的语言代码
    """
    # 创建表
    create_table(cursor)
    
    # 准备SQL语句
    regions_sql = f'''
        INSERT OR REPLACE INTO regions (regionID, regionName, {', '.join([f'regionName_{lang}' for lang in LANGUAGES])})
        VALUES (?, ?, {', '.join(['?' for _ in LANGUAGES])})
    '''
    
    constellations_sql = f'''
        INSERT OR REPLACE INTO constellations (constellationID, constellationName, {', '.join([f'constellationName_{lang}' for lang in LANGUAGES])})
        VALUES (?, ?, {', '.join(['?' for _ in LANGUAGES])})
    '''
    
    solarsystems_sql = f'''
        INSERT OR REPLACE INTO solarsystems (solarSystemID, solarSystemName, {', '.join([f'solarSystemName_{lang}' for lang in LANGUAGES])}, security_status)
        VALUES (?, ?, {', '.join(['?' for _ in LANGUAGES])}, ?)
    '''
    
    # 处理星域数据
    for region_id, region_data in data.items():
        region_names = region_data['region_name']
        region_values = [
            int(region_id), 
            region_names.get(lang, region_names.get('en'))  # 使用指定语言的名称，如果没有则使用英文
        ]
        for lang_code in LANGUAGES:
            region_values.append(region_names.get(lang_code))
        cursor.execute(regions_sql, region_values)
        
        # 处理星座数据
        for const_id, const_data in region_data['constellations'].items():
            const_names = const_data['constellation_name']
            const_values = [
                int(const_id), 
                const_names.get(lang, const_names.get('en'))  # 使用指定语言的名称，如果没有则使用英文
            ]
            for lang_code in LANGUAGES:
                const_values.append(const_names.get(lang_code))
            cursor.execute(constellations_sql, const_values)
            
            # 处理星系数据
            for sys_id, sys_data in const_data['systems'].items():
                sys_names = sys_data['system_name']
                sys_values = [
                    int(sys_id), 
                    sys_names.get(lang, sys_names.get('en'))  # 使用指定语言的名称，如果没有则使用英文
                ]
                for lang_code in LANGUAGES:
                    sys_values.append(sys_names.get(lang_code))
                sys_values.append(sys_data['system_info']['security_status'])
                cursor.execute(solarsystems_sql, sys_values)