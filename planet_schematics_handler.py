import yaml
import json
import time

def read_yaml(file_path):
    """读取 YAML 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def process_data(yaml_data, cursor, language):
    """处理 YAML 数据并写入数据库"""
    # 创建行星制造表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS planetSchematics (
        output_typeid INTEGER NOT NULL PRIMARY KEY,
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
        if not name:  # 如果当前语言的name为空，尝试获取英语的name
            name = schematic_data.get('nameID', {}).get('en', '')
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

