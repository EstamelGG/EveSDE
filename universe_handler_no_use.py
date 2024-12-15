import os
import yaml
from typing import Dict, List, Tuple

def read_yaml(file_path: str) -> dict:
    """读取 invUniqueNames.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def process_yaml_file(file_path: str) -> dict:
    """读取单个 YAML 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def collect_yaml_files(base_path: str) -> Tuple[List[str], List[str], List[str]]:
    """收集所有的region.yaml、constellation.yaml和solarsystem.yaml文件路径"""
    region_files = []
    constellation_files = []
    solarsystem_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == 'region.yaml':
                region_files.append(os.path.join(root, file))
            elif file == 'constellation.yaml':
                constellation_files.append(os.path.join(root, file))
            elif file == 'solarsystem.yaml':
                solarsystem_files.append(os.path.join(root, file))
    print("Get %i regions, %i constellations, %i solarsystems" % (len(region_files), len(constellation_files), len(solarsystem_files)))
    return region_files, constellation_files, solarsystem_files

def process_universe_data(unique_names_data: dict, cursor, lang: str):
    """处理宇宙数据并插入到数据库"""
    # 创建 universe 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universe (
            itemID INTEGER PRIMARY KEY,
            itemName TEXT,
            type TEXT
        )
    ''')

    # 创建 itemID 到 itemName 的映射
    unique_names = {}
    for item in unique_names_data:
        if isinstance(item, dict) and 'itemID' in item and 'itemName' in item:
            unique_names[item['itemID']] = item['itemName']
    
    universe_path = 'Data/sde/universe/eve'
    region_files, constellation_files, solarsystem_files = collect_yaml_files(universe_path)

    # 处理区域数据
    for region_file in region_files:
        region_data = process_yaml_file(region_file)
        region_id = region_data.get('regionID')
        if region_id in unique_names:
            cursor.execute('INSERT OR REPLACE INTO universe (itemID, itemName, type) VALUES (?, ?, ?)',
                         (region_id, unique_names[region_id], 'region'))

    # 处理星座数据
    for constellation_file in constellation_files:
        constellation_data = process_yaml_file(constellation_file)
        constellation_id = constellation_data.get('constellationID')
        if constellation_id in unique_names:
            cursor.execute('INSERT OR REPLACE INTO universe (itemID, itemName, type) VALUES (?, ?, ?)',
                         (constellation_id, unique_names[constellation_id], 'constellation'))

    # 处理恒星系数据
    for solarsystem_file in solarsystem_files:
        system_data = process_yaml_file(solarsystem_file)
        system_id = system_data.get('solarSystemID')
        if system_id in unique_names:
            cursor.execute('INSERT OR REPLACE INTO universe (itemID, itemName, type) VALUES (?, ?, ?)',
                         (system_id, unique_names[system_id], 'solarsystem'))