import sqlite3

def update_groups_with_icon_filename(cursor):
    """根据 group_id 从 types 表获取 icon_filename，并更新 groups 表"""
    # 获取 groups 表中的所有 group_id
    cursor.execute('SELECT group_id FROM groups')
    groups = cursor.fetchall()
    
    # 创建一个缓存字典来存储已查询的图标
    icon_cache = {}
    
    # 批量更新列表
    updates = []
    
    for group in groups:
        group_id_value = group[0]
        
        # 如果图标已在缓存中，直接使用
        if group_id_value in icon_cache:
            icon_filename = icon_cache[group_id_value]
        else:
            # 获取对应的 icon_filename，查找符合条件的第一条数据
            cursor.execute('''
                SELECT icon_filename 
                FROM types 
                WHERE groupID = ? 
                  AND icon_filename != "items_73_16_50.png" 
                  AND icon_filename != "items_7_64_15.png" 
                  AND icon_filename != "icon_0_64.png" 
                ORDER BY metaGroupID ASC 
                LIMIT 1
            ''', (group_id_value,))
            result = cursor.fetchone()
            
            if result:
                icon_filename = result[0]
            else:
                icon_filename = "items_73_16_50.png"  # 如果没有找到符合条件的结果，设置为默认值
            
            # 将结果存入缓存
            icon_cache[group_id_value] = icon_filename
        
        # 添加到批量更新列表
        updates.append((icon_filename, group_id_value))
    
    # 批量执行更新
    cursor.executemany('''
        UPDATE groups
        SET icon_filename = ?
        WHERE group_id = ?
    ''', updates)
    
    print("Updated icon_filename for all groups.")

if __name__ == '__main__':
    # 示例用法
    db_filename = 'output/db/zh.db'
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()
    
    try:
        update_groups_with_icon_filename(cursor)
        conn.commit()
    finally:
        conn.close()
    
    print(f"Database {db_filename} has been updated.")
