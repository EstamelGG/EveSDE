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
        output_material INTEGER,
        output_quantity INTEGER,
        output_material_name TEXT,
        PRIMARY KEY (typeid, output_material)
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM typeMaterials')
    
    # 创建材料名称缓存字典
    material_names = {}
    
    def get_material_name(material_id):
        """从缓存或数据库获取材料名称"""
        if material_id not in material_names:
            cursor.execute('SELECT name FROM types WHERE type_id = ?', (material_id,))
            result = cursor.fetchone()
            material_names[material_id] = result[0] if result else None
        return material_names[material_id]
    
    # 处理每个物品的材料数据
    for type_id, type_data in yaml_data.items():
        if 'materials' in type_data:
            for material in type_data['materials']:
                material_type_id = material['materialTypeID']
                quantity = material['quantity']
                material_name = get_material_name(material_type_id)
                
                # 逐行插入数据
                cursor.execute(
                    '''INSERT OR REPLACE INTO typeMaterials 
                       (typeid, output_material, output_quantity, output_material_name) 
                       VALUES (?, ?, ?, ?)''',
                    (type_id, material_type_id, quantity, material_name)
                )