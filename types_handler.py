from ruamel.yaml import YAML
import sqlite3
from typeTraits_handler import process_trait_data
import shutil
import os
import hashlib
import json

yaml = YAML(typ='safe')


def read_yaml(file_path):
    """读取 types.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        types_data = {}
        for part in yaml.load_all(file):
            types_data.update(part)
        return types_data


def load_md5_map():
    """从文件加载MD5映射"""
    try:
        with open('icon_md5_map.txt', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_md5_map(md5_map):
    """保存MD5映射到文件"""
    with open('icon_md5_map.txt', 'w', encoding='utf-8') as f:
        json.dump(md5_map, f, ensure_ascii=False, indent=2)


# 初始化全局字典
icon_md5_map = load_md5_map()


def calculate_file_md5(file_path):
    """计算文件的MD5值"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def copy_and_rename_icon(x):
    global icon_md5_map
    
    # 定义文件路径
    input_directory = "Data/Types"
    output_directory = "output/Icons"
    input_file = f"{x}_64.png"
    output_file = f"icon_{x}_64.png"

    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)

    # 构造输入文件完整路径
    input_path = os.path.join(input_directory, input_file)

    # 检查源文件是否存在
    if not os.path.exists(input_path):
        return "items_7_64_15.png"

    # 计算源文件的MD5
    file_md5 = calculate_file_md5(input_path)
    
    # 检查MD5是否存在于映射中
    if file_md5 in icon_md5_map:
        # 如果存在，直接返回之前保存的文件名
        output_file = icon_md5_map[file_md5]

    # 如果MD5没有重复，则复制一次，如果已经复制了就不再重复复制
    output_path = os.path.join(output_directory, output_file)
    if os.path.exists(output_path):
        return output_file
    # 复制文件并重命名
    shutil.copy(input_path, output_path)
    # 将新的MD5和文件名添加到映射中
    icon_md5_map[file_md5] = output_file
    # 保存更新后的映射
    save_md5_map(icon_md5_map)
    
    return output_file


def create_types_table(cursor):
    """创建 types 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS types (
            type_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            icon_filename TEXT,
            published BOOLEAN,
            volume REAL,
            capacity REAL,
            mass REAL,
            marketGroupID INTEGER,
            metaGroupID INTEGER,
            iconID INTEGER,
            groupID INTEGER,
            group_name TEXT,
            categoryID INTEGER,
            category_name TEXT,
            pg_need INTEGER,
            cpu_need INTEGER,
            rig_cost INTEGER,
            em_damage REAL,
            them_damage REAL,
            kin_damage REAL,
            exp_damage REAL,
            high_slot INTEGER,
            mid_slot INTEGER,
            low_slot INTEGER,
            rig_slot INTEGER,
            gun_slot INTEGER,
            miss_slot INTEGER,
            variationParentTypeID INTEGER,
            process_size INTEGER
        )
    ''')


def fetch_and_process_data(cursor):
    # 查询 categories 表
    cursor.execute("SELECT category_id, name FROM categories")
    categories_data = cursor.fetchall()

    # 查询 groups 表
    cursor.execute("SELECT group_id, name, categoryID FROM groups")
    groups_data = cursor.fetchall()

    # 1. 创建 category_id 与 group_id 的关系
    group_to_category = {group_id: category_id for group_id, _, category_id in groups_data}

    # 2. 创建 categories 中 category_id 与 name 的映射关系
    category_id_to_name = {category_id: name for category_id, name in categories_data}

    # 3. 创建 groups 中 group_id 与 name 的映射关系
    group_id_to_name = {group_id: name for group_id, name, _ in groups_data}

    return group_to_category, category_id_to_name, group_id_to_name

def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    create_types_table(cursor)
    group_to_category, category_id_to_name, group_id_to_name = fetch_and_process_data(cursor)
    for type_id, item in types_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        description = item.get('description', {}).get(lang,
                                                      item.get('description', {}).get('en', ""))  # 优先取 lang，没有则取 en
        published = item.get('published', False)
        volume = item.get('volume', None)
        marketGroupID = item.get('marketGroupID', 0)
        metaGroupID = item.get('metaGroupID', 1)
        iconID = item.get('iconID', 0)
        groupID = item.get('groupID', 0)
        process_size = item.get('portionSize', None)
        capacity = item.get('capacity', None)
        mass = item.get('mass', None)
        variationParentTypeID = item.get('variationParentTypeID', None)
        group_name = group_id_to_name.get(groupID, 'Unknown')
        category_id = group_to_category.get(groupID, 0)
        category_name = category_id_to_name.get(category_id, 'Unknown')
        copied_file = copy_and_rename_icon(type_id)  # 复制物品图像
        # 获取 pg_need 和 cpu_need 的值
        res = get_attributes_value(cursor, type_id, [30, 50, 1153, 114, 118, 117, 116, 14, 13, 12, 1154, 102, 101, 1367]) # 获取 pg占用 的值 (pg_need)和 cpu占用 的值 (cpu_need)
        pg_need =  res[0]
        cpu_need = res[1]
        rig_cost = res[2]
        em_damage = res[3]
        them_damage = res[4]
        kin_damage = res[5]
        exp_damage = res[6]
        high_slot = res[7]
        mid_slot = res[8]
        low_slot = res[9]
        rig_slot = res[10]
        gun_slot = res[11]
        miss_slot = res[12]

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO types (
            type_id, name, description, icon_filename, published, volume, capacity, mass, marketGroupID,
             metaGroupID, iconID, groupID, group_name, categoryID, category_name, pg_need, cpu_need, rig_cost,
             em_damage, them_damage, kin_damage, exp_damage, high_slot, mid_slot, low_slot, rig_slot,gun_slot, miss_slot,
             variationParentTypeID, process_size
             )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            type_id, name, description, copied_file,  published, volume, capacity, mass, marketGroupID, metaGroupID, iconID, groupID,
            group_name, category_id, category_name, pg_need,
            cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage, high_slot,
            mid_slot, low_slot, rig_slot, gun_slot, miss_slot, variationParentTypeID, process_size))

    process_trait_data(types_data, cursor, lang)


def get_attributes_value(cursor, type_id, attribute_ids):
    """
    从 typeAttributes 表获取多个属性的值

    参数:
    - cursor: 数据库游标
    - type_id: 类型ID
    - attribute_ids: 属性ID列表

    返回:
    - 包含所有请求属性值的列表，如果某个属性不存在则对应位置返回None
    """
    # 构建 SQL 查询中的 IN 子句
    placeholders = ','.join('?' * len(attribute_ids))

    cursor.execute(f'''
        SELECT attribute_id, value 
        FROM typeAttributes 
        WHERE type_id = ? AND attribute_id IN ({placeholders})
    ''', (type_id, *attribute_ids))

    # 获取所有结果并转换为字典
    results = dict(cursor.fetchall())

    # 为每个请求的 attribute_id 获取对应的值，如果不存在则返回 None
    return [results.get(attr_id, None) for attr_id in attribute_ids]
