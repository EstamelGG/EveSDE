import sqlite3

def update_type_attributes_unit(db_path):
    """
    更新typeAttributes表中的unitID
    
    Args:
        db_path: 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 首先修改typeAttributes表，添加unitID字段
    try:
        cursor.execute('ALTER TABLE typeAttributes ADD COLUMN unitID INTEGER')
    except sqlite3.OperationalError:
        # 如果列已存在，忽略错误
        pass
    
    # 获取dogmaAttributes表中的attribute_id和unitID映射
    cursor.execute('''
        SELECT attribute_id, unitID
        FROM dogmaAttributes
        WHERE unitID IS NOT NULL
    ''')
    attribute_unit_map = dict(cursor.fetchall())
    
    # 开始事务
    conn.execute('BEGIN')
    
    # 更新typeAttributes表中的unitID
    cursor.execute('''
        UPDATE typeAttributes
        SET unitID = CASE
            WHEN attribute_id IN (
                SELECT attribute_id
                FROM dogmaAttributes
                WHERE unitID IS NOT NULL
            )
            THEN (
                SELECT unitID
                FROM dogmaAttributes
                WHERE dogmaAttributes.attribute_id = typeAttributes.attribute_id
            )
            ELSE NULL
        END
    ''')
    
    # 提交事务
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # 这里可以直接调用函数进行测试
    db_path = 'output/db/zh.db'  # 示例路径
    update_type_attributes_unit(db_path) 