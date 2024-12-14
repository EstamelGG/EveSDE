import yaml

def read_yaml(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建marketGroups表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marketGroups (
        group_id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        icon_name TEXT,
        parentgroup_id INTEGER
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM marketGroups')
    
    # 处理每个市场组
    for group_id, group_data in yaml_data.items():
        # 获取当前语言的名称和描述
        name = group_data.get('nameID', {}).get(language, '')
        description = group_data.get('descriptionID', {}).get(language, '')
        
        # 获取图标ID并查找对应的图标文件名
        icon_id = group_data.get('iconID')
        icon_name = None
        if icon_id is not None:
            cursor.execute('SELECT iconFile_new FROM iconIDs WHERE icon_id = ?', (icon_id,))
            result = cursor.fetchone()
            if result:
                icon_name = result[0]
        
        # 获取父组ID
        parentgroup_id = group_data.get('parentGroupID')
        
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO marketGroups 
            (group_id, name, description, icon_name, parentgroup_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_id, name, description, icon_name, parentgroup_id)) 