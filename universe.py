import os
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from typing import Dict, List, Tuple

# 用于缓存universe数据
_universe_data: List[Tuple[int, int, int, float]] = []

# 需要处理的宇宙目录
UNIVERSE_DIRS = [
    'Data/sde/universe/eve',
    'Data/sde/universe/abyssal',
    'Data/sde/universe/void',
    'Data/sde/universe/wormhole'
]

def create_table(cursor):
    """创建universe表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universe (
            region_id INTEGER,
            constellation_id INTEGER,
            solarsystem_id INTEGER,
            system_security REAL,
            PRIMARY KEY (region_id, constellation_id, solarsystem_id)
        )
    ''')

def read_yaml_file(file_path: str) -> dict:
    """读取单个YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file, Loader=SafeLoader)

def process_universe_data(base_path: str, cursor=None) -> List[Tuple[int, int, int, float]]:
    """处理universe目录下的所有数据"""
    universe_data = []
    all_universe_data = []  # 用于存储所有数据
    
    # 检查目录是否存在
    if not os.path.exists(base_path):
        print(f"警告: 目录 {base_path} 不存在，跳过处理")
        return all_universe_data
    
    # 遍历基础目录（星域级别）
    for region_name in os.listdir(base_path):
        region_path = os.path.join(base_path, region_name)
        if not os.path.isdir(region_path):
            continue
            
        # 读取region.yaml
        region_yaml_path = os.path.join(region_path, 'region.yaml')
        if not os.path.exists(region_yaml_path):
            continue
            
        region_data = read_yaml_file(region_yaml_path)
        region_id = region_data.get('regionID')
        if not region_id:
            continue
            
        # 遍历星座目录
        for constellation_name in os.listdir(region_path):
            constellation_path = os.path.join(region_path, constellation_name)
            if not os.path.isdir(constellation_path):
                continue
                
            # 读取constellation.yaml
            constellation_yaml_path = os.path.join(constellation_path, 'constellation.yaml')
            if not os.path.exists(constellation_yaml_path):
                continue
                
            constellation_data = read_yaml_file(constellation_yaml_path)
            constellation_id = constellation_data.get('constellationID')
            if not constellation_id:
                continue
                
            # 遍历恒星系目录
            for system_name in os.listdir(constellation_path):
                system_path = os.path.join(constellation_path, system_name)
                if not os.path.isdir(system_path):
                    continue
                    
                # 读取solarsystem.yaml
                system_yaml_path = os.path.join(system_path, 'solarsystem.yaml')
                if not os.path.exists(system_yaml_path):
                    continue
                    
                system_data = read_yaml_file(system_yaml_path)
                system_id = system_data.get('solarSystemID')
                system_security = system_data.get('security', 0)
                if not system_id:
                    continue
                    
                # 将关系数据添加到列表中
                universe_data.append((region_id, constellation_id, system_id, system_security))
                all_universe_data.append((region_id, constellation_id, system_id, system_security))
                
                # 如果数据量达到1000条，执行批量插入
                if cursor and len(universe_data) >= 1000:
                    cursor.executemany(
                        'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security) VALUES (?, ?, ?, ?)',
                        universe_data
                    )
                    universe_data = []  # 清空临时数据，但保留在all_universe_data中
    
    # 处理剩余的数据
    if cursor and universe_data:
        cursor.executemany(
            'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security) VALUES (?, ?, ?, ?)',
            universe_data
        )
    
    return all_universe_data

def process_all_universe_data(cursor=None) -> List[Tuple[int, int, int, float]]:
    """处理所有宇宙目录的数据"""
    all_data = []
    
    # 处理每个宇宙目录
    for universe_dir in UNIVERSE_DIRS:
        print(f"处理目录: {universe_dir}")
        universe_data = process_universe_data(universe_dir, cursor)
        all_data.extend(universe_data)
    
    # 在所有数据收集完成后，一次性执行批量插入
    if cursor and all_data:
        print(f"正在插入 {len(all_data)} 条宇宙数据记录...")
        cursor.executemany(
            'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security) VALUES (?, ?, ?, ?)',
            all_data
        )
    
    return all_data

def process_data(cursor, lang: str = 'en'):
    """主处理函数"""
    global _universe_data
    start_time = time.time()
    
    # 创建表
    create_table(cursor)
    
    # 只在处理英文数据时读取文件
    if lang == 'en':
        print("处理英文宇宙数据...")
        _universe_data.clear()  # 清空缓存
        _universe_data = process_all_universe_data(cursor)
        print(f"缓存了 {len(_universe_data)} 条宇宙数据记录")
    else:
        # 使用缓存数据
        if _universe_data:
            print(f"使用缓存数据插入 {len(_universe_data)} 条宇宙数据记录...")
            cursor.executemany(
                'INSERT OR REPLACE INTO universe (region_id, constellation_id, solarsystem_id, system_security) VALUES (?, ?, ?, ?)',
                _universe_data
            )
        else:
            print("警告: 没有找到缓存的宇宙数据")
    
    end_time = time.time()
    print(f"处理universe数据耗时: {end_time - start_time:.2f} 秒")