import json
import os

def process_jump_map_data(cursor, lang=None):
    """
    从JSON文件读取星系间距离数据并写入数据库的jumpMap表
    
    Args:
        cursor: 数据库游标
        lang: 语言代码（在此函数中未使用，但保持与其他处理器一致的接口）
    """
    # 创建jumpMap表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jumpMap (
            from_system_id INTEGER,
            to_system_id INTEGER,
            distance REAL,
            PRIMARY KEY (from_system_id, to_system_id)
        )
    """)
    
    # 读取JSON文件
    json_file = "nearby_systems.json"
    if not os.path.exists(json_file):
        print(f"错误：未找到 {json_file} 文件")
        return
        
    print(f"正在处理 {json_file} 数据...")
    with open(json_file, 'r', encoding='utf-8') as f:
        nearby_systems = json.load(f)
    
    # 准备插入数据
    insert_data = []
    for from_system, targets in nearby_systems.items():
        for to_system, distance in targets.items():
            insert_data.append((int(from_system), int(to_system), float(distance)))
    
    # 批量插入数据
    if insert_data:
        cursor.executemany(
            "INSERT OR REPLACE INTO jumpMap (from_system_id, to_system_id, distance) VALUES (?, ?, ?)",
            insert_data
        )
        print(f"已插入 {len(insert_data)} 条星系间距离数据")
    else:
        print("警告：没有找到可插入的数据") 