import yaml

def read_yaml(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

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
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO factions 
            (id, iconID, iconName, name)
            VALUES (?, ?, ?, ?)
        ''', (faction_id, icon_id, icon_name, name)) 