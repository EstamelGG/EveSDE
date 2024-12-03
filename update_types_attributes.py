import sqlite3

def update_types_with_attributes(db_filename):
    """根据 type_id 从 typeAttributes 表获取属性值并更新 types 表的 pg_need 和 cpu_need 列"""
    # 连接数据库
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # 获取 types 表中的所有 type_id
    cursor.execute('SELECT type_id FROM types')
    types = cursor.fetchall()

    for type_id in types:
        type_id_value = type_id[0]

        # 获取 attribute_id=30 对应的 pg_need 值
        cursor.execute('''
            SELECT value FROM typeAttributes WHERE type_id = ? AND attribute_id = 30
        ''', (type_id_value,))
        pg_need = cursor.fetchone()
        pg_need_value = pg_need[0] if pg_need else None  # 如果没有值，则为 None

        # 获取 attribute_id=50 对应的 cpu_need 值
        cursor.execute('''
            SELECT value FROM typeAttributes WHERE type_id = ? AND attribute_id = 50
        ''', (type_id_value,))
        cpu_need = cursor.fetchone()
        cpu_need_value = cpu_need[0] if cpu_need else None  # 如果没有值，则为 None

        # 更新 types 表中的 pg_need 和 cpu_need 列
        cursor.execute('''
            UPDATE types
            SET pg_need = ?, cpu_need = ?
            WHERE type_id = ?
        ''', (pg_need_value, cpu_need_value, type_id_value))

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

    print(f"Updated pg_need and cpu_need for all types in {db_filename}.")