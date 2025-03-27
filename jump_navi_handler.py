import sqlite3
import numpy as np
from itertools import combinations
import os

def calculate_distance_ly(x1, y1, z1, x2, y2, z2):
    """计算两点之间的距离（光年）"""
    # 1米 = 1/9460528400000000 光年
    LY_CONVERSION = 1 / 9460528400000000
    
    # 计算欧几里得距离
    distance_m = np.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
    
    # 转换为光年
    distance_ly = float(distance_m * LY_CONVERSION)

    
    return distance_ly

def get_nearby_systems():
    """获取所有符合条件的星系对"""
    # 连接数据库
    conn = sqlite3.connect('output/db/item_db_en.sqlite')
    cursor = conn.cursor()
    
    # 执行查询
    query = """
    SELECT solarsystem_id, x, y, z 
    FROM universe 
    WHERE system_security <= 0.5 
    AND hasJumpGate 
    AND NOT isJSpace 
    AND region_id NOT IN (10000019, 10000004, 10000017)
    """
    
    cursor.execute(query)
    systems = cursor.fetchall()
    
    print(f"SQL查询返回 {len(systems)} 个星系")
    if len(systems) > 0:
        print("示例数据:")
        print(systems[0])
    
    # 存储结果
    nearby_pairs = []
    
    # 计算所有星系对之间的距离
    total_pairs = 0
    for (sys1, sys2) in combinations(systems, 2):
        total_pairs += 1
        source_id, x1, y1, z1 = sys1
        dest_id, x2, y2, z2 = sys2
        
        # 确保数据类型正确
        x1, y1, z1 = float(x1), float(y1), float(z1)
        x2, y2, z2 = float(x2), float(y2), float(z2)

        distance_ly = calculate_distance_ly(x1, y1, z1, x2, y2, z2)
        
        if distance_ly < 10:
            # 只保存source_id < dest_id的情况，避免重复
            if source_id < dest_id:
                nearby_pairs.append((int(source_id), int(dest_id), distance_ly))
    
    print(f"\n总结:")
    print(f"计算了 {total_pairs} 对星系之间的距离")
    print(f"找到 {len(nearby_pairs)} 对距离小于10光年的星系")
    if len(nearby_pairs) > 0:
        print("示例近距离星系对:")
        print(nearby_pairs[0])
    
    conn.close()
    return nearby_pairs

def create_jump_map_table(cursor):
    """创建JumpMap表"""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS JumpMap (
        source_id INTEGER,
        dest_id INTEGER,
        distance_ly REAL,
        PRIMARY KEY (source_id, dest_id)
    )
    ''')

def batch_insert_data(cursor, data, batch_size=1000):
    """批量插入数据"""
    if not data:
        print("警告：没有数据需要插入")
        return
        
    print(f"准备插入 {len(data)} 条数据")
    print(f"数据示例: {data[0] if data else 'No data'}")
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        try:
            cursor.executemany('''
            INSERT INTO JumpMap (source_id, dest_id, distance_ly)
            VALUES (?, ?, ?)
            ''', batch)
        except sqlite3.Error as e:
            print(f"插入数据时出错: {e}")
            print(f"问题数据示例: {batch[0] if batch else 'No data'}")
            raise

def process_jump_navigation_data(cursor):
    """处理跳跃导航数据"""
    # 创建JumpMap表
    create_jump_map_table(cursor)
    
    # 清空现有数据
    cursor.execute('DELETE FROM JumpMap')
    
    # 获取结果
    results = get_nearby_systems()
    
    # 批量插入数据
    batch_insert_data(cursor, results)

def process_all_languages():
    """处理所有语言的数据库"""
    # 获取结果
    results = get_nearby_systems()
    print(f"找到 {len(results)} 对距离小于10光年的星系")
    
    if not results:
        print("警告：没有找到符合条件的星系对")
        return
    
    # 处理每种语言的数据库
    languages = ['en', 'de', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']
    for lang in languages:
        db_filename = os.path.join('output/db', f'item_db_{lang}.sqlite')
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        
        try:
            # 创建JumpMap表
            create_jump_map_table(cursor)
            
            # 清空现有数据
            cursor.execute('DELETE FROM JumpMap')
            
            # 批量插入数据
            batch_insert_data(cursor, results)
            
            conn.commit()
            print(f"数据库 {db_filename} 已更新")
        except Exception as e:
            print(f"处理数据库 {db_filename} 时出错: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    process_all_languages() 