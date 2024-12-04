import sqlite3

def update_groups_with_icon_filename(db_filename):
    """根据 group_id 从 types 表获取 icon_filename，并更新 groups 表"""
    # 连接数据库
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # 获取 groups 表中的所有 group_id
    cursor.execute('SELECT group_id FROM groups')
    groups = cursor.fetchall()

    for group in groups:
        group_id_value = group[0]

        # 获取对应的 icon_filename，查找符合条件的第一条数据
        cursor.execute('''
            SELECT icon_filename FROM types WHERE groupID = ? AND icon_filename != "items_73_16_50.png" AND icon_filename != "items_7_64_15.png" LIMIT 1
        ''', (group_id_value,))
        result = cursor.fetchone()

        if result:
            icon_filename = result[0]
        else:
            icon_filename = "items_73_16_50.png"  # 如果没有找到符合条件的结果，设置为默认值

        # 更新 groups 表中的 icon_filename 字段
        cursor.execute('''
            UPDATE groups
            SET icon_filename = ?
            WHERE group_id = ?
        ''', (icon_filename, group_id_value))

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

    print(f"Updated icon_filename for all groups in {db_filename}.")