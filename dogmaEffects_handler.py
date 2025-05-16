from ruamel.yaml import YAML
import sqlite3
import time
import json

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 dogmaEffects.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_dogma_effects_table(cursor):
    """创建 dogmaEffects 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaEffects (
            effect_id INTEGER NOT NULL PRIMARY KEY,
            effect_category INTEGER,
            effect_name TEXT,
            display_name TEXT,
            description TEXT,
            published BOOLEAN,
            is_assistance BOOLEAN,
            is_offensive BOOLEAN,
            resistance_attribute_id INTEGER,
            modifier_info TEXT
        )
    ''')

def process_data(data, cursor, lang):
    """处理 dogmaEffects 数据并插入数据库（针对单一语言）"""
    create_dogma_effects_table(cursor)
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for effect_id, effect_data in data.items():
        # 获取多语言字段
        display_name = effect_data.get('displayNameID', {}).get(lang, None)
        description = effect_data.get('descriptionID', {}).get(lang, None)
        
        # 获取其他字段
        effect_name = effect_data.get('effectName', None)
        effect_category = effect_data.get('effectCategory', None)
        published = effect_data.get('published', False)
        is_assistance = effect_data.get('isAssistance', False)
        is_offensive = effect_data.get('isOffensive', False)
        resistance_attribute_id = effect_data.get('resistanceAttributeID', None)
        
        # 处理modifierInfo字段，转换为JSON字符串
        modifier_info = effect_data.get('modifierInfo', None)
        modifier_info_json = json.dumps(modifier_info) if modifier_info is not None else None
        
        # 添加到批处理列表
        batch_data.append((
            effect_id, effect_category, effect_name, display_name, description,
            published, is_assistance, is_offensive, resistance_attribute_id, modifier_info_json
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO dogmaEffects (
                    effect_id, effect_category, effect_name, display_name, description,
                    published, is_assistance, is_offensive, resistance_attribute_id, modifier_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO dogmaEffects (
                effect_id, effect_category, effect_name, display_name, description,
                published, is_assistance, is_offensive, resistance_attribute_id, modifier_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data) 