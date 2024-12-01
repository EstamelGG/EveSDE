import sqlite3
import numpy as np
from itertools import combinations
import os
import json
from datetime import datetime

def calculate_distance_ly(x1, y1, z1, x2, y2, z2):
    """计算两点之间的距离（光年）"""
    # 1米 = 1/9460528400000000 光年
    LY_CONVERSION = 1 / 9460528400000000
    
    # 计算欧几里得距离
    distance_m = np.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
    
    # 转换为光年
    distance_ly = float(distance_m * LY_CONVERSION)
    
    return distance_ly

def calculate_display_security(true_sec):
    """计算显示用的安全等级"""
    if true_sec > 0.0 and true_sec < 0.05:
        return 0.1  # 0.0到0.05之间向上取整到0.1
    return round(true_sec * 10) / 10  # 其他情况四舍五入到小数点后一位

def get_nearby_systems():
    """获取所有符合条件的星系对"""
    # 连接数据库
    conn = sqlite3.connect('output/db/item_db_en.sqlite')
    cursor = conn.cursor()
    
    # 执行查询
    query = """
    SELECT solarsystem_id, x, y, z, system_security 
    FROM universe 
    WHERE system_security < 0.5 
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
    
    # 二次过滤：计算显示安全等级并过滤
    filtered_systems = []
    for system in systems:
        solarsystem_id, x, y, z, sec = system
        display_sec = calculate_display_security(float(sec))
        if display_sec < 0.5:
            filtered_systems.append((solarsystem_id, x, y, z, display_sec))
    
    print(f"二次过滤后剩余 {len(filtered_systems)} 个星系")
    
    # 存储结果
    nearby_pairs = []
    
    # 计算所有星系对之间的距离
    total_pairs = 0
    for (sys1, sys2) in combinations(filtered_systems, 2):
        total_pairs += 1
        source_id, x1, y1, z1, sec1 = sys1
        dest_id, x2, y2, z2, sec2 = sys2
        
        # 确保数据类型正确
        x1, y1, z1 = float(x1), float(y1), float(z1)
        x2, y2, z2 = float(x2), float(y2), float(z2)

        distance_ly = calculate_distance_ly(x1, y1, z1, x2, y2, z2)
        
        if distance_ly < 10:
            # 只保存source_id < dest_id的情况，避免重复
            if source_id < dest_id:
                nearby_pairs.append({
                    'source_id': int(source_id),
                    'dest_id': int(dest_id),
                    'distance_ly': float(distance_ly),
                    'source_security': float(sec1),
                    'dest_security': float(sec2)
                })
    
    print(f"\n总结:")
    print(f"计算了 {total_pairs} 对星系之间的距离")
    print(f"找到 {len(nearby_pairs)} 对距离小于10光年的星系")
    if len(nearby_pairs) > 0:
        print("示例近距离星系对:")
        print(nearby_pairs[0])
    
    conn.close()
    return nearby_pairs

def save_to_json(data):
    """将数据保存到JSON文件"""
    if not data:
        print("警告：没有数据需要保存")
        return
        
    # 创建输出目录
    output_dir = 'output/jump_map'
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名（包含时间戳）
    filename = os.path.join(output_dir, f'jump_map.json')
    
    # 准备输出数据
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_pairs': len(data),
            'max_distance_ly': 10.0
        },
        'jump_pairs': data
    }
    
    # 保存到JSON文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"数据已保存到: {filename}")
    except Exception as e:
        print(f"保存JSON文件时出错: {e}")

def process_jump_navigation_data():
    """处理跳跃导航数据"""
    # 获取结果
    results = get_nearby_systems()
    
    # 保存到JSON文件
    save_to_json(results)

if __name__ == "__main__":
    process_jump_navigation_data() 