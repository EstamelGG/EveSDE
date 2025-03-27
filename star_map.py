import sqlite3
import numpy as np
from scipy.spatial import cKDTree
import pandas as pd
from tqdm import tqdm
import os
import json


def calculate_distance_matrix():
    # 连接数据库
    db_path = "output/db/item_db_zh.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有星系数据
    print("正在读取星系数据...")
    cursor.execute("""
        SELECT solarsystem_id, x, y, z 
        FROM universe 
        WHERE hasJumpGate = true 
        AND isJSpace = false
        AND system_security <= 0.5
        AND region_id NOT IN (10000019, 10000017, 10000004)
        ORDER BY solarsystem_id
    """)
    systems = cursor.fetchall()

    if not systems:
        print("错误：未找到符合条件的星系")
        conn.close()
        return

    # 转换为numpy数组
    system_ids = np.array([s[0] for s in systems])
    coordinates = np.array([(s[1], s[2], s[3]) for s in systems])

    # 创建KD树用于快速查找
    print("正在构建KD树...")
    tree = cKDTree(coordinates)

    # 计算距离矩阵（分块处理以避免内存溢出）
    n_systems = len(systems)
    chunk_size = 100  # 每次处理100个星系
    max_distance_ly = 10  # 最大距离（光年）

    print(f"开始计算近邻星系，共 {n_systems} 个符合条件的星系...")

    # 光年转换系数
    light_year_conversion = 9460528400000000

    # 存储结果的字典
    nearby_systems = {}

    # 分块处理
    for i in tqdm(range(0, n_systems, chunk_size)):
        end_idx = min(i + chunk_size, n_systems)

        # 计算当前块到所有其他星系的距离
        distances, indices = tree.query(coordinates[i:end_idx], k=n_systems)
        
        # 将距离转换为光年
        distances = distances / light_year_conversion

        # 处理每个星系
        for j in range(end_idx - i):
            current_system = system_ids[i + j]
            # 找出距离小于等于10光年的星系
            nearby_mask = distances[j] <= max_distance_ly
            nearby_indices = indices[j][nearby_mask]
            nearby_distances = distances[j][nearby_mask]
            
            # 创建近邻星系字典（排除自身）
            nearby_dict = {
                int(system_ids[idx]): float(dist)
                for idx, dist in zip(nearby_indices, nearby_distances)
                if system_ids[idx] != current_system
            }
            
            if nearby_dict:  # 只保存有近邻星系的记录
                nearby_systems[int(current_system)] = nearby_dict

    # 保存为JSON文件
    output_file = "nearby_systems.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(nearby_systems, f, ensure_ascii=False, indent=2)

    print(f"\n近邻星系数据已保存到 {output_file}")

    # 输出一些统计信息
    print("\n统计信息：")
    print(f"符合条件的星系数：{n_systems}")
    print(f"有近邻星系的星系数：{len(nearby_systems)}")
    print(f"最大距离阈值：{max_distance_ly} 光年")

    # 计算文件大小
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # 转换为MB
    print(f"输出文件大小：{file_size:.2f} MB")

    conn.close()


def calculate_distance_between_systems(from_system_id: int, to_system_id: int) -> float:
    """
    计算两个星系之间的距离

    Args:
        from_system_id: 起始星系ID
        to_system_id: 目标星系ID

    Returns:
        float: 两个星系之间的距离
    """
    db_path = "/Users/gg/Documents/GitHub/EVE-Nexus/EVE Nexus/utils/SQLite/item_db_zh.sqlite"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取两个星系的坐标
    cursor.execute("""
        SELECT x, y, z 
        FROM universe 
        WHERE solarsystem_id IN (?, ?)
    """, (from_system_id, to_system_id))

    results = cursor.fetchall()

    if len(results) != 2:
        raise ValueError(f"未找到指定的星系ID: {from_system_id} 或 {to_system_id}")

    # 计算欧几里得距离
    x1, y1, z1 = results[0]
    x2, y2, z2 = results[1]

    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) / 9460528400000000

    conn.close()
    print(f"星系 {from_system_id} 到星系 {to_system_id} 的距离为: {distance} 光年")


if __name__ == "__main__":
    calculate_distance_between_systems(30004759, 30004708)
    calculate_distance_matrix()