import yaml
import time

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建factions表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factions (
        id INTEGER PRIMARY KEY,
        iconID INTEGER,
        iconName TEXT,
        name TEXT
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM factions')
    
    # 处理每个派系
    for faction_id, faction_data in yaml_data.items():
        # 获取iconID
        icon_id = faction_data.get('iconID')
        
        # 从iconIDs表获取iconFile_new
        icon_name = None
        if icon_id is not None:
            cursor.execute('SELECT iconFile_new FROM iconIDs WHERE icon_id = ?', (icon_id,))
            result = cursor.fetchone()
            if result:
                icon_name = result[0]
        
        # 获取当前语言的名称
        name = faction_data.get('nameID', {}).get(language, '')
        if not name:  # 如果当前语言的name为空，尝试获取英语的name
            name = faction_data.get('nameID', {}).get('en', '')
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO factions 
            (id, iconID, iconName, name)
            VALUES (?, ?, ?, ?)
        ''', (faction_id, icon_id, icon_name, name)) 