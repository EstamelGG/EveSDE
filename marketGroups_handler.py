import yaml

def read_yaml(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def get_child_groups(cursor, parent_group_id):
    """获取指定组的所有直接子组"""
    cursor.execute('SELECT group_id FROM marketGroups WHERE parentgroup_id = ?', (parent_group_id,))
    return [row[0] for row in cursor.fetchall()]

def get_icon_from_children(cursor, group_id, visited=None):
    """递归查找子组的图标"""
    if visited is None:
        visited = set()
    
    if group_id in visited:
        return None
    visited.add(group_id)
    
    # 获取所有子组
    child_groups = get_child_groups(cursor, group_id)
    
    for child_id in child_groups:
        # 检查子组是否有图标
        cursor.execute('SELECT icon_name FROM marketGroups WHERE group_id = ?', (child_id,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
        
        # 递归检查子组的子组
        child_icon = get_icon_from_children(cursor, child_id, visited)
        if child_icon:
            return child_icon
    
    return None

def check_group_has_items(cursor, group_id, visited=None):
    """递归检查组及其子组是否包含物品"""
    if visited is None:
        visited = set()
    
    if group_id in visited:
        return False
    visited.add(group_id)
    
    # 检查当前组是否有物品
    cursor.execute('SELECT COUNT(*) FROM types WHERE marketGroupID = ?', (group_id,))
    if cursor.fetchone()[0] > 0:
        return True
    
    # 检查子组
    child_groups = get_child_groups(cursor, group_id)
    for child_id in child_groups:
        if check_group_has_items(cursor, child_id, visited):
            return True
    
    return False

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建marketGroups表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marketGroups (
        group_id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        icon_name TEXT,
        parentgroup_id INTEGER,
        show BOOLEAN DEFAULT 1
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
        
        # 如果没有找到图标，从types表中获取
        if not icon_name:
            cursor.execute('''
                SELECT icon_filename 
                FROM types 
                WHERE marketGroupID = ? 
                AND icon_filename IS NOT NULL 
                LIMIT 1
            ''', (group_id,))
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
    
    # 后处理：处理图标继承
    cursor.execute('SELECT group_id FROM marketGroups WHERE icon_name IS NULL')
    groups_without_icon = cursor.fetchall()
    
    for (group_id,) in groups_without_icon:
        # 尝试从子组获取图标
        icon_name = get_icon_from_children(cursor, group_id)
        if not icon_name:
            icon_name = 'items_73_16_50.png'  # 默认图标
        
        cursor.execute('''
            UPDATE marketGroups 
            SET icon_name = ? 
            WHERE group_id = ?
        ''', (icon_name, group_id))
    
    # 后处理：检查显示状态
    cursor.execute('SELECT group_id FROM marketGroups')
    all_groups = cursor.fetchall()
    
    for (group_id,) in all_groups:
        should_show = check_group_has_items(cursor, group_id)
        cursor.execute('''
            UPDATE marketGroups 
            SET show = ? 
            WHERE group_id = ?
        ''', (should_show, group_id))