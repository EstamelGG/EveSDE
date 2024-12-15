import os
import yaml

def get_region_files():
    """获取所有region.yaml文件的路径"""
    base_path = 'Data/sde/universe/eve'
    region_files = []
    
    for region_dir in os.listdir(base_path):
        region_file = os.path.join(base_path, region_dir, 'region.yaml')
        if os.path.exists(region_file):
            region_files.append((region_file, region_dir))
    
    return region_files

# 用于缓存region信息的全局变量
region_cache = {}

def read_yaml(file_path=None):
    """读取region数据，这里file_path参数不使用，保持与其他handler一致的接口"""
    global region_cache
    
    # 如果缓存为空，则读取并处理数据
    if not region_cache:
        region_files = get_region_files()
        region_data = {}
        
        for region_file, region_name in region_files:
            with open(region_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                region_id = data.get('regionID')
                if region_id:
                    region_data[region_id] = region_name
                    region_cache[region_id] = region_name
        
        return region_data
    return region_cache

def process_data(data, cursor, lang):
    """处理region数据并插入数据库"""
    # 创建Regions表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Regions (
            regionID INTEGER PRIMARY KEY,
            regionName TEXT
        )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM Regions')
    
    # 插入数据
    for region_id, region_name in data.items():
        cursor.execute('INSERT INTO Regions (regionID, regionName) VALUES (?, ?)',
                      (region_id, region_name))