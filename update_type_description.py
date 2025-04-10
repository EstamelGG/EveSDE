import sqlite3

def update_type_description():
    """
    更新指定数据库中types表的description字段
    """
    # 在脚本开始时建立数据库连接
    conn = sqlite3.connect("output/db/item_db_zh.sqlite")
    cursor = conn.cursor()

    def execute_sql(sql):
        """
        执行SQL语句的通用函数
        
        Args:
            sql (str): 要执行的SQL语句
        Returns:
            int: 受影响的行数
        """
        cursor.execute(sql)
        conn.commit()
        return cursor.rowcount

    try:
        # SQL语句
        sql = """
            UPDATE types 
            SET description = '测试测试测试' 
            WHERE type_id = 35834
        """

        # 执行SQL
        affected_rows = execute_sql(sql)

        # 输出结果
        if affected_rows > 0:
            print("更新成功！")
        else:
            print("未找到指定记录")

    finally:
        # 在脚本结束时关闭数据库连接
        conn.close()

if __name__ == "__main__":
    update_type_description() 