import yaml

def read_yaml(file_path):
    """读取YAML文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建typeMaterials表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS typeMaterials (
        typeid INTEGER,
        categoryid INTEGER,
        process_size INTEGER,
        output_material INTEGER,
        output_quantity INTEGER,
        output_material_name TEXT,
        output_material_icon TEXT,
        PRIMARY KEY (typeid, output_material)
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM typeMaterials')
    
    # 创建材料信息缓存字典
    material_info = {}
    type_info = {}
    
    def get_material_info(material_id):
        """从缓存或数据库获取材料信息"""
        if material_id not in material_info:
            cursor.execute('SELECT name, icon_filename FROM types WHERE type_id = ?', (material_id,))
            result = cursor.fetchone()
            if result:
                material_info[material_id] = {'name': result[0], 'icon': result[1]}
            else:
                material_info[material_id] = {'name': None, 'icon': None}
        return material_info[material_id]
    
    def get_type_info(type_id):
        """从缓存或数据库获取物品的categoryid和process_size"""
        if type_id not in type_info:
            cursor.execute('SELECT categoryID, process_size FROM types WHERE type_id = ?', (type_id,))
            result = cursor.fetchone()
            if result:
                type_info[type_id] = {'categoryid': result[0], 'process_size': result[1]}
            else:
                type_info[type_id] = {'categoryid': None, 'process_size': None}
        return type_info[type_id]
    
    # 处理每个物品的材料数据
    for type_id, type_data in yaml_data.items():
        if 'materials' in type_data:
            # 获取物品的信息
            type_data = get_type_info(type_id)
            category_id = type_data['categoryid']
            process_size = type_data['process_size']
            
            for material in type_data['materials']:
                material_type_id = material['materialTypeID']
                quantity = material['quantity']
                material_data = get_material_info(material_type_id)
                
                # 逐行插入数据
                cursor.execute(
                    '''INSERT OR REPLACE INTO typeMaterials 
                       (typeid, categoryid, process_size, output_material, output_quantity, output_material_name, output_material_icon) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (type_id, category_id, process_size, material_type_id, quantity, material_data['name'], material_data['icon'])
                )