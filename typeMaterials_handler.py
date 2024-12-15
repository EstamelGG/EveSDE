import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import time
from cache_manager import register_cache_cleaner
import sqlite3
import os

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('typeMaterials_handler', clear_cache)

def read_yaml(file_path):
    """读取 typeMaterials.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data

def process_data(yaml_data, cursor, language):
    """处理YAML数据并写入数据库"""
    try:
        print(f"开始处理 {language} 语言的材料数据...")
        
        if language == 'en':
            # 英文数据库保存完整数据
            cursor.execute('DROP TABLE IF EXISTS typeMaterials')
            cursor.execute('''
                CREATE TABLE typeMaterials (
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
            total_items = len(yaml_data)
            processed_items = 0
            batch_data = []
            batch_size = 1000
            
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
                        
                        batch_data.append((
                            type_id, category_id, process_size, material_type_id,
                            material_info['categoryid'], material_info['groupID'],
                            quantity, material_info['name'], material_info['icon']
                        ))
                        
                        if len(batch_data) >= batch_size:
                            cursor.executemany('''
                                INSERT INTO typeMaterials VALUES (?,?,?,?,?,?,?,?,?)
                            ''', batch_data)
                            batch_data = []
                
                processed_items += 1
                if processed_items % 1000 == 0:
                    print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
            
            # 处理剩余的数据
            if batch_data:
                cursor.executemany('''
                    INSERT INTO typeMaterials VALUES (?,?,?,?,?,?,?,?,?)
                ''', batch_data)
        
        else:
            # 非英文数据库只保存变化的字段
            cursor.execute('DROP TABLE IF EXISTS typeMaterials_translation')
            cursor.execute('DROP TABLE IF EXISTS typeMaterials')
            
            # 创建翻译表
            cursor.execute('''
                CREATE TABLE typeMaterials_translation (
                    typeid INTEGER,
                    output_material INTEGER,
                    output_material_name TEXT,
                    PRIMARY KEY (typeid, output_material)
                )
            ''')
            
            # 连接英文数据库
            cursor.execute('ATTACH DATABASE ? AS en_db', (os.path.join('output/db', 'item_db_en.sqlite'),))
            
            # 创建typeMaterials表并从英文数据库复制数据
            cursor.execute('''
                CREATE TABLE typeMaterials AS SELECT * FROM en_db.typeMaterials
            ''')
            
            # 获取翻译后的名称
            type_info_cache = {}
            def get_type_name(type_id):
                if type_id not in type_info_cache:
                    cursor.execute('SELECT name FROM types WHERE type_id = ?', (type_id,))
                    result = cursor.fetchone()
                    type_info_cache[type_id] = result[0] if result else None
                return type_info_cache[type_id]
            
            print(f"正在处理 {language} 语言的材料翻译数据...")
            total_items = len(yaml_data)
            processed_items = 0
            batch_data = []
            batch_size = 1000
            
            for type_id, type_data in yaml_data.items():
                if 'materials' in type_data:
                    for material in type_data['materials']:
                        material_type_id = material['materialTypeID']
                        material_name = get_type_name(material_type_id)
                        
                        if material_name:
                            batch_data.append((type_id, material_type_id, material_name))
                        
                        if len(batch_data) >= batch_size:
                            cursor.executemany('''
                                INSERT INTO typeMaterials_translation VALUES (?,?,?)
                            ''', batch_data)
                            batch_data = []
                
                processed_items += 1
                if processed_items % 1000 == 0:
                    print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
            
            # 处理剩余的数据
            if batch_data:
                cursor.executemany('''
                    INSERT INTO typeMaterials_translation VALUES (?,?,?)
                ''', batch_data)
            
            # 更新typeMaterials表中的翻译字段
            cursor.execute('''
                UPDATE typeMaterials
                SET output_material_name = COALESCE(
                    (SELECT output_material_name 
                     FROM typeMaterials_translation 
                     WHERE typeMaterials_translation.typeid = typeMaterials.typeid 
                     AND typeMaterials_translation.output_material = typeMaterials.output_material),
                    output_material_name)
            ''')
            
            # 分离英文数据库
            cursor.execute('DETACH DATABASE en_db')
        
        print(f"已成功完成 {language} 材料数据的处理")
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {str(e)}")
        raise
    except Exception as e:
        print(f"处理 {language} 材料数据时发生错误: {str(e)}")
        raise