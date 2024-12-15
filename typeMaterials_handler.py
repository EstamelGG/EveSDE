import yaml
import time

def read_yaml(file_path):
    """读取YAML文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    # 创建typeMaterials表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS typeMaterials (
        typeid INTEGER,
        categoryid INTEGER,
        process_size INTEGER,
        output_material INTEGER,
        output_material_categoryid INTEGER,
        output_material_groupid INTEGER,
        output_quantity INTEGER,
        output_material_name TEXT,
        output_material_icon TEXT,
        PRIMARY KEY (typeid, output_material)
    )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM typeMaterials')
    
    # 创建物品信息缓存字典
    type_info_cache = {}
    
    def get_type_info(type_id):
        """从缓存或数据库获取物品的所有相关信息"""
        if type_id not in type_info_cache:
            cursor.execute('SELECT name, icon_filename, categoryID, groupID, process_size FROM types WHERE type_id = ?', (type_id,))
            result = cursor.fetchone()
            if result:
                type_info_cache[type_id] = {
                    'name': result[0],
                    'icon': result[1],
                    'categoryid': result[2],
                    'groupID': result[3],
                    'process_size': result[4]
                }
            else:
                type_info_cache[type_id] = {
                    'name': None,
                    'icon': None,
                    'categoryid': None,
                    'groupID': None,
                    'process_size': None
                }
        return type_info_cache[type_id]
    
    # 处理每个物品的材料数据
    for type_id, type_data in yaml_data.items():
        if 'materials' in type_data:
            # 获取物品的信息
            type_info = get_type_info(type_id)
            category_id = type_info['categoryid']
            process_size = type_info['process_size']
            
            for material in type_data['materials']:
                material_type_id = material['materialTypeID']
                quantity = material['quantity']
                material_info = get_type_info(material_type_id)
                
                # 逐行插入数据
                cursor.execute(
                    '''INSERT OR REPLACE INTO typeMaterials 
                       (typeid, categoryid, process_size, output_material, output_material_categoryid, output_material_groupid, output_quantity, output_material_name, output_material_icon) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (type_id, category_id, process_size, material_type_id, material_info['categoryid'], material_info['groupID'], quantity, material_info['name'], material_info['icon'])
                )