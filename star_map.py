import sqlite3
import numpy as np
from scipy.spatial import cKDTree
import pandas as pd
from tqdm import tqdm
import os


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
        ORDER BY solarsystem_id
    """)
    systems = cursor.fetchall()

    # 转换为numpy数组
    system_ids = np.array([s[0] for s in systems])
    coordinates = np.array([(s[1], s[2], s[3]) for s in systems])

    # 创建KD树用于快速查找
    print("正在构建KD树...")
    tree = cKDTree(coordinates)

    # 计算距离矩阵（分块处理以避免内存溢出）
    n_systems = len(systems)
    chunk_size = 100  # 每次处理100个星系

    print(f"开始计算距离矩阵，共 {n_systems} 个星系...")

    # 创建结果文件
    output_file = "distance_matrix.csv"

    # 光年转换系数
    light_year_conversion = 9460528400000000

    # 分块处理并保存
    for i in tqdm(range(0, n_systems, chunk_size)):
        end_idx = min(i + chunk_size, n_systems)

        # 计算当前块到所有其他星系的距离
        distances, indices = tree.query(coordinates[i:end_idx], k=n_systems)
        
        # 将距离转换为光年
        distances = distances / light_year_conversion

        # 创建DataFrame
        df_chunk = pd.DataFrame(
            distances,
            index=system_ids[i:end_idx],
            columns=system_ids
        )

        # 追加到CSV文件
        if i == 0:
            df_chunk.to_csv(output_file)
        else:
            df_chunk.to_csv(output_file, mode='a', header=False)

    print(f"距离矩阵已保存到 {output_file}")

    # 输出一些统计信息
    print("\n统计信息：")
    print(f"总星系数：{n_systems}")
    print(f"矩阵大小：{n_systems} x {n_systems}")
    print("距离单位：光年")

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