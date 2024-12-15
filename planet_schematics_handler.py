import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from cache_manager import register_cache_cleaner

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('planetSchematics', clear_cache)

def read_yaml(file_path):
    """读取 planetSchematics.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def process_data(yaml_data, cursor, language):
    """处理 YAML 数据并写入数据库"""
    # 创建行星制造表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS planetSchematics (
        output_typeid INTEGER,
        name TEXT,
        facilitys TEXT,
        cycle_time INTEGER,
        output_value INTEGER,
        input_typeid TEXT,
        input_value TEXT
    )
    ''')

    # 处理行星制造数据
    for schematic_id, schematic_data in yaml_data.items():
        cycle_time = schematic_data.get('cycleTime', 0)
        name = schematic_data.get('nameID', {}).get(language, '')
        facilitys = ','.join(map(str, schematic_data.get('pins', [])))

        input_typeids = []
        input_values = []
        output_typeid = None
        output_value = None

        for type_id, type_data in schematic_data.get('types', {}).items():
            if type_data.get('isInput', False):
                input_typeids.append(str(type_id))
                input_values.append(str(type_data.get('quantity', 0)))
            else:
                output_typeid = type_id
                output_value = type_data.get('quantity', 0)

        input_typeid_str = ','.join(input_typeids)
        input_value_str = ','.join(input_values)

        cursor.execute('''
        INSERT INTO planetSchematics (output_typeid, name, facilitys, cycle_time, output_value, input_typeid, input_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (output_typeid, name, facilitys, cycle_time, output_value, input_typeid_str, input_value_str))

