import yaml

def read_yaml(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

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
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 制造产出表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_manufacturing_output (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 材料研究材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_material_materials (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 材料研究技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_material_skills (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER
    )
    ''')
    
    # 时间研究材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_time_materials (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 时间研究技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_research_time_skills (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER
    )
    ''')
    
    # 复制材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_copying_materials (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 复制技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_copying_skills (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER
    )
    ''')
    
    # 发明材料表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_materials (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER
    )
    ''')
    
    # 发明产出表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_products (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        quantity INTEGER,
        probability REAL
    )
    ''')
    
    # 发明技能表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_invention_skills (
        blueprintTypeID INTEGER PRIMARY KEY,
        typeID INTEGER,
        typeName TEXT,
        typeIcon TEXT,
        level INTEGER
    )
    ''')
    
    # 处理时间表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blueprint_process_time (
        blueprintTypeID INTEGER PRIMARY KEY,
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
    # 创建表
    create_tables(cursor)
    # 清空表
    clear_tables(cursor)
    
    # 处理每个蓝图
    for _, blueprint_data in yaml_data.items():
        blueprint_type_id = blueprint_data['blueprintTypeID']
        blueprint_type_name = get_type_name(cursor, blueprint_type_id)
        activities = blueprint_data.get('activities', {})
        blueprintTypeIcon = get_type_icon(cursor, blueprint_type_id)
        
        # 记录处理时间
        times = {
            'manufacturing_time': activities.get('manufacturing', {}).get('time', 0),
            'research_material_time': activities.get('research_material', {}).get('time', 0),
            'research_time_time': activities.get('research_time', {}).get('time', 0),
            'copying_time': activities.get('copying', {}).get('time', 0),
            'invention_time': activities.get('invention', {}).get('time', 0)
        }
        cursor.execute(
            'INSERT OR REPLACE INTO blueprint_process_time (blueprintTypeID, manufacturing_time, research_material_time, research_time_time, copying_time, invention_time) VALUES (?, ?, ?, ?, ?, ?)',
            (blueprint_type_id, times.get("manufacturing_time", 0), times.get("research_material_time", 0), times.get("research_time_time", 0), times.get("copying_time", 0), times.get("invention_time", 0))
        )
        
        # 处理制造
        if 'manufacturing' in activities:
            mfg = activities['manufacturing']
            # 处理材料
            if 'materials' in mfg:
                for material in mfg['materials']:
                    if "typeID" in material:
                        type_id = material['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_manufacturing_materials (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, material.get("quantity", -1))
                        )
            # 处理产出
            if 'products' in mfg:
                for product in mfg['products']:
                    if "typeID" in product:
                        type_id = product['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_manufacturing_output (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, product.get("quantity", -1))
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
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_research_material_materials (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, material.get("quantity", -1))
                        )
            # 处理技能
            if 'skills' in rm:
                for skill in rm['skills']:
                    if "typeID" in skill:
                        type_id = skill['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_research_material_skills (blueprintTypeID, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, skill.get("level", -1))
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
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_research_time_materials (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, material.get("quantity", -1))
                        )
            # 处理技能
            if 'skills' in rt:
                for skill in rt['skills']:
                    if "typeID" in skill:
                        type_id = skill['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_research_time_skills (blueprintTypeID, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, skill.get("level", -1))
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
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_copying_materials (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, material.get("quantity", -1))
                        )
            # 处理技能
            if 'skills' in cp:
                for skill in cp['skills']:
                    if "typeID" in skill:
                        type_id = skill['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_copying_skills (blueprintTypeID, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, skill.get("level", -1))
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
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_invention_materials (blueprintTypeID, typeID, typeName, typeIcon, quantity) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, material.get("quantity", -1))
                        )
            # 处理产出
            if 'products' in inv:
                for product in inv['products']:
                    if "typeID" in product:
                        type_id = product['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_invention_products (blueprintTypeID, typeID, typeName, typeIcon, quantity, probability) VALUES (?, ?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, product.get("quantity", -1), product.get("probability", 0))
                        )
            # 处理技能
            if 'skills' in inv:
                for skill in inv['skills']:
                    if "typeID" in skill:
                        type_id = skill['typeID']
                        type_name = get_type_name(cursor, type_id)
                        typeIcon = get_type_icon(cursor, type_id)
                        cursor.execute(
                            'INSERT OR REPLACE INTO blueprint_invention_skills (blueprintTypeID, typeID, typeName, typeIcon, level) VALUES (?, ?, ?, ?, ?)',
                            (blueprint_type_id, type_id, type_name, typeIcon, skill.get("level", -1))
                        )