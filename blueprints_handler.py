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
register_cache_cleaner('blueprints', clear_cache)

def read_yaml(file_path):
    """读取 blueprints.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def get_type_name(cursor, type_id):
    """从types表获取类型名称"""
    cursor.execute('SELECT name FROM types WHERE type_id = ?', (type_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_type_icon(cursor, type_id):
    """从types表获取类型名称"""
    cursor.execute('SELECT icon_filename FROM types WHERE type_id = ?', (type_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def create_tables(cursor):
    """创建所需的数据表"""
    # 制造材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_manufacturing_materials (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 制造产出表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_manufacturing_output (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')

    # 制造技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_manufacturing_skills (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')

    # 材料研究材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_material_materials (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 材料研究技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_material_skills (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 时间研究材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_time_materials (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 时间研究技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_time_skills (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 复制材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_copying_materials (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 复制技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_copying_skills (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 发明材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_materials (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 发明产出表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_products (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        probability REAL,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 发明技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_skills (
        blueprintTypeID INTEGER,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER,
        PRIMARY KEY (blueprintTypeID, typeID)
    )
    ''')
    
    # 处理时间表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_process_time (
        blueprintTypeID INTEGER PRIMARY KEY,
        blueprintTypeName TEXT,
        blueprintTypeIcon TEXT,
        manufacturing_time INTEGER,
        research_material_time INTEGER,
        research_time_time INTEGER,
        copying_time INTEGER,
        invention_time INTEGER
    )
    ''')

def clear_tables(cursor):
    """清空所有相关表"""
    tables = [
        'blueprint_manufacturing_materials',
        'blueprint_manufacturing_output',
        'blueprint_research_material_materials',
        'blueprint_research_material_skills',
        'blueprint_manufacturing_skills',
        'blueprint_research_time_materials',
        'blueprint_research_time_skills',
        'blueprint_copying_materials',
        'blueprint_copying_skills',
        'blueprint_invention_materials',
        'blueprint_invention_products',
        'blueprint_invention_skills',
        'blueprint_process_time'
    ]
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    try:
        # 创建表
        create_tables(cursor)
        # 清空表
        clear_tables(cursor)
        
        for blueprint_id, blueprint_data in yaml_data.items():
            try:
                blueprint_type_id = blueprint_data['blueprintTypeID']
                blueprint_type_name = get_type_name(cursor, blueprint_type_id)
                blueprint_type_icon = get_type_icon(cursor, blueprint_type_id)
                activities = blueprint_data.get('activities', {})
                
                # 记录处理时间
                times = {
                    'manufacturing_time': (activities.get('manufacturing') or activities.get('reaction') or {}).get('time', 0),
                    'research_material_time': activities.get('research_material', {}).get('time', 0),
                    'research_time_time': activities.get('research_time', {}).get('time', 0),
                    'copying_time': activities.get('copying', {}).get('time', 0),
                    'invention_time': activities.get('invention', {}).get('time', 0)
                }
                cursor.execute(
                    'INSERT OR REPLACE INTO blueprint_process_time (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, manufacturing_time, research_material_time, research_time_time, copying_time, invention_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, times['manufacturing_time'], times['research_material_time'], times['research_time_time'], times['copying_time'], times['invention_time'])
                )
                
                # 处理制造
                if 'manufacturing' in activities or "reaction" in activities:
                    if "manufacturing" in activities:
                        mfg = activities['manufacturing']
                    else:
                        mfg = activities['reaction']
                    # 处理材料
                    if 'materials' in mfg:
                        for material in mfg['materials']:
                            if "typeID" in material:
                                type_id = material['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_manufacturing_materials (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, material.get("quantity", -1))
                                )
                    # 处理产出
                    if 'products' in mfg:
                        for product in mfg['products']:
                            if "typeID" in product:
                                type_id = product['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_manufacturing_output (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, product.get("quantity", -1))
                                )
                    # 处理技能
                    if 'skills' in mfg:
                        for skill in mfg['skills']:
                            if "typeID" in skill:
                                type_id = skill['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_manufacturing_skills (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, skill.get("level", -1))
                                )
                
                # 处理材料研究
                if 'research_material' in activities:
                    rm = activities['research_material']
                    # 处理材料
                    if 'materials' in rm:
                        for material in rm['materials']:
                            if "typeID" in material:
                                type_id = material['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_research_material_materials (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, material.get("quantity", -1))
                                )
                    # 处理技能
                    if 'skills' in rm:
                        for skill in rm['skills']:
                            if "typeID" in skill:
                                type_id = skill['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_research_material_skills (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, skill.get("level", -1))
                                )
                
                # 处理时间研究
                if 'research_time' in activities:
                    rt = activities['research_time']
                    # 处理材料
                    if 'materials' in rt:
                        for material in rt['materials']:
                            if "typeID" in material:
                                type_id = material['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_research_time_materials (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, material.get("quantity", -1))
                                )
                    # 处理技能
                    if 'skills' in rt:
                        for skill in rt['skills']:
                            if "typeID" in skill:
                                type_id = skill['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_research_time_skills (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, skill.get("level", -1))
                                )
                
                # 处理复制
                if 'copying' in activities:
                    cp = activities['copying']
                    # 处理材料
                    if 'materials' in cp:
                        for material in cp['materials']:
                            if "typeID" in material:
                                type_id = material['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_copying_materials (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, material.get("quantity", -1))
                                )
                    # 处理技能
                    if 'skills' in cp:
                        for skill in cp['skills']:
                            if "typeID" in skill:
                                type_id = skill['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_copying_skills (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, skill.get("level", -1))
                                )
                
                # 处理发明
                if 'invention' in activities:
                    inv = activities['invention']
                    # 处理材料
                    if 'materials' in inv:
                        for material in inv['materials']:
                            if "typeID" in material:
                                type_id = material['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_invention_materials (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, material.get("quantity", -1))
                                )
                    # 处理产出
                    if 'products' in inv:
                        for product in inv['products']:
                            if "typeID" in product:
                                type_id = product['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_invention_products (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, quantity, probability) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, product.get("quantity", -1), product.get("probability", 0))
                                )
                    # 处理技能
                    if 'skills' in inv:
                        for skill in inv['skills']:
                            if "typeID" in skill:
                                type_id = skill['typeID']
                                type_name = get_type_name(cursor, type_id)
                                type_icon = get_type_icon(cursor, type_id)
                                cursor.execute(
                                    'INSERT OR REPLACE INTO blueprint_invention_skills (blueprintTypeID, blueprintTypeName, blueprintTypeIcon, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                    (blueprint_type_id, blueprint_type_name, blueprint_type_icon, type_id, type_name, type_icon, skill.get("level", -1))
                                )
            
            except Exception as e:
                print(f"处理蓝图 {blueprint_id} 时出错: {str(e)}")
                continue

        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        raise