import yaml
from collections import defaultdict
import time

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def build_group_hierarchies(cursor):
    """构建组层级关系和组信息的缓存"""
    # 获取所有组的层级关系
    cursor.execute('SELECT group_id, parentgroup_id, icon_name FROM marketGroups')
    results = cursor.fetchall()
    
    # 构建父子关系映射
    children_map = defaultdict(list)
    group_info = {}
    for group_id, parent_id, icon_name in results:
        if parent_id is not None:
            children_map[parent_id].append(group_id)
        group_info[group_id] = {'icon_name': icon_name}
    
    return children_map, group_info

def build_group_items_map(cursor):
    """构建组与物品数量的映射"""
    cursor.execute('''
        SELECT marketGroupID, COUNT(*) as count 
        FROM types 
        WHERE marketGroupID IS NOT NULL 
        GROUP BY marketGroupID
    ''')
    return dict(cursor.fetchall())

def get_icon_for_group(group_id, children_map, group_info, visited=None):
    """使用缓存的数据递归查找组的图标"""
    if visited is None:
        visited = set()
    
    if group_id in visited:
        return None
    visited.add(group_id)
    
    # 检查当前组的图标
    current_icon = group_info[group_id]['icon_name']
    if current_icon:
        return current_icon
    
    # 检查子组的图标
    for child_id in children_map[group_id]:
        child_icon = get_icon_for_group(child_id, children_map, group_info, visited)
        if child_icon:
            return child_icon
    
    return None

def check_group_has_items_cached(group_id, children_map, items_map, visited=None):
    """使用缓存的数据递归检查组是否包含物品"""
    if visited is None:
        visited = set()
    
    if group_id in visited:
        return False
    visited.add(group_id)
    
    # 检查当前组是否有物品
    if items_map.get(group_id, 0) > 0:
        return True
    
    # 检查子组
    for child_id in children_map[group_id]:
        if check_group_has_items_cached(child_id, children_map, items_map, visited):
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
    insert_data = []
    for group_id, group_data in yaml_data.items():
        # 获取当前语言的名称和描述，如果为空则使用英语
        name = group_data.get('nameID', {}).get(language, '')
        if not name:  # 如果当前语言的name为空，尝试获取英语的name
            name = group_data.get('nameID', {}).get('en', '')
            
        description = group_data.get('descriptionID', {}).get(language, '')
        if not description:  # 如果当前语言的description为空，尝试获取英语的description
            description = group_data.get('descriptionID', {}).get('en', '')
        
        # 获取图标ID并查找对应的图标文件名
        icon_id = group_data.get('iconID')
        icon_name = None
        if icon_id == 20966:
            icon_name = "items_19_128_1.png"
        if icon_id == 20959:
            icon_name = "items_19_128_4.png"
        if icon_id == 20967:
            icon_name = "items_19_128_3.png"
        if icon_id == 20968:
            icon_name = "items_19_128_2.png"
        if icon_id is not None and icon_name is None:
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
                ORDER BY metaGroupID 
                LIMIT 1
            ''', (group_id,))
            result = cursor.fetchone()
            if result:
                icon_name = result[0]
        
        # 获取父组ID
        parentgroup_id = group_data.get('parentGroupID')
        
        # 收集插入数据
        insert_data.append((group_id, name, description, icon_name, parentgroup_id))
    
    # 批量插入数据
    cursor.executemany('''
        INSERT OR REPLACE INTO marketGroups 
        (group_id, name, description, icon_name, parentgroup_id)
        VALUES (?, ?, ?, ?, ?)
    ''', insert_data)
    
    # 构建缓存数据
    children_map, group_info = build_group_hierarchies(cursor)
    items_map = build_group_items_map(cursor)
    
    # 后处理：处理图标继承
    updates_icon = []
    for group_id in group_info:
        if not group_info[group_id]['icon_name']:
            icon_name = get_icon_for_group(group_id, children_map, group_info)
            if not icon_name:
                icon_name = 'items_73_16_50.png'
            updates_icon.append((icon_name, group_id))
    
    # 批量更新图标
    if updates_icon:
        cursor.executemany('''
            UPDATE marketGroups 
            SET icon_name = ? 
            WHERE group_id = ?
        ''', updates_icon)
    
    # 后处理：检查显示状态
    updates_show = []
    for group_id in group_info:
        should_show = check_group_has_items_cached(group_id, children_map, items_map)
        updates_show.append((should_show, group_id))
    
    # 批量更新显示状态
    cursor.executemany('''
        UPDATE marketGroups 
        SET show = ? 
        WHERE group_id = ?
    ''', updates_show)