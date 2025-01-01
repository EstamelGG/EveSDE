import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import sqlite3
import time

def read_yaml(file_path):
    """读取 npcCorporations.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_npc_corporations_table(cursor):
    """创建 npcCorporations 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS npcCorporations (
            corporation_id INTEGER PRIMARY KEY,
            name TEXT,
            en_name TEXT,
            description TEXT,
            faction_id INTEGER,
            icon_id INTEGER
        )
    ''')

def process_data(corporations_data, cursor, lang):
    """处理 npcCorporations 数据并插入数据库"""
    create_npc_corporations_table(cursor)
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for corp_id, corp_info in corporations_data.items():
        # 获取名称，如果没有对应语言的就用英文
        name = corp_info.get('nameID', {}).get(lang) or corp_info.get('nameID', {}).get('en')
        # 英文数据库不需要 en_name，其他语言数据库存储英文名称
        en_name = None if lang == 'en' else corp_info.get('nameID', {}).get('en')
        # 获取描述，如果没有对应语言的就用英文
        description = corp_info.get('descriptionID', {}).get(lang) or corp_info.get('descriptionID', {}).get('en')
        
        # 获取其他信息
        faction_id = corp_info.get('factionID')
        icon_id = corp_info.get('iconID')
        
        # 添加到批处理列表
        batch_data.append((
            corp_id,
            name,
            en_name,
            description,
            faction_id,
            icon_id
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO npcCorporations (
                    corporation_id,
                    name,
                    en_name,
                    description,
                    faction_id,
                    icon_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO npcCorporations (
                corporation_id,
                name,
                en_name,
                description,
                faction_id,
                icon_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', batch_data) 