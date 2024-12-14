import sqlite3

def update_type_attributes_unit(cursor):
    """
    更新typeAttributes表中的unitID
    
    Args:
        cursor: 数据库游标
    """
    # 首先修改typeAttributes表，添加unitID字段
    try:
        cursor.execute('ALTER TABLE typeAttributes ADD COLUMN unitID INTEGER')
    except sqlite3.OperationalError:
        # 如果列已存在，忽略错误
        pass
    
    # 获取dogmaAttributes表中的attribute_id和unitID映射并缓存
    cursor.execute('''
        SELECT attribute_id, unitID
        FROM dogmaAttributes
        WHERE unitID IS NOT NULL
    ''')
    attribute_unit_map = dict(cursor.fetchall())
    
    # 获取所有需要更新的typeAttributes记录
    cursor.execute('''
        SELECT DISTINCT attribute_id 
        FROM typeAttributes 
        WHERE attribute_id IN (
            SELECT attribute_id 
            FROM dogmaAttributes 
            WHERE unitID IS NOT NULL
        )
    ''')
    attributes_to_update = cursor.fetchall()
    
    # 准备批量更新数据
    updates = []
    for (attribute_id,) in attributes_to_update:
        unit_id = attribute_unit_map.get(attribute_id)
        if unit_id is not None:
            updates.append((unit_id, attribute_id))
    
    # 批量执行更新
    if updates:
        cursor.executemany('''
            UPDATE typeAttributes
            SET unitID = ?
            WHERE attribute_id = ?
        ''', updates)


if __name__ == '__main__':
    # 示例用法
    db_path = 'output/db/zh.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        update_type_attributes_unit(cursor)
        conn.commit()
    finally:
        conn.close()
    
    print(f"Database {db_path} has been updated.") 