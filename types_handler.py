import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import sqlite3
from typeTraits_handler import process_trait_data
import shutil
import os
import hashlib
import json
import time

# NPC船只场景映射
NPC_SHIP_SCENES = [
    "Asteroid ",
    "Deadspace ",
    "FW ",
    "Ghost Site ",
    "Incursion ",
    "Mission ",
    "Storyline ",
    "Abyssal "
]

# NPC船只势力映射
NPC_SHIP_FACTIONS = [
    "Angel Cartel",
    "Blood Raider",
    "Guristas",
    "Mordu",
    "Rogue Drone",
    "Sansha",
    "Serpentis",
    "Overseer",
    "Sleeper",
    "Drifter",
    "Amarr Empire",
    "Gallente Federation",
    "Minmatar Republic",
    "Caldari State",
    "CONCORD",
    "Faction",
    "Generic",
    "Khanid",
    "Thukker"
]

# NPC势力ICON映射
NPC_FACTION_ICON_MAP = {
    "Angel Cartel": "corporations_45_128_2.png",
    "Blood Raider": "corporations_19_128_3.png",
    "Guristas": "corporations_28_128_3.png",
    "Mordu": "corporations_34_128_2.png",
    "Rogue Drone": "corporations_roguedronesgeneric.png",
    "Sansha": "corporations_44_128_2.png",
    "Serpentis": "corporations_45_128_1.png",
    "Overseer": "items_73_16_50.png",  # 使用默认图标
    "Sleeper": "corporations_48_128_1.png",
    "Drifter": "corporations_48_128_1.png",
    "Amarr Empire": "items_19_128_4.png",
    "Gallente Federation": "items_19_128_3.png",
    "Minmatar Republic": "items_19_128_2.png",
    "Caldari State": "items_19_128_1.png",
    "CONCORD": "corporations_26_128_3.png",
    "Faction": "items_73_16_50.png",  # 使用默认图标
    "Generic": "items_73_16_50.png",  # 使用默认图标
    "Khanid": "corporations_11_128_1.png",
    "Thukker": "corporations_44_128_3.png"
}

# NPC船只类型映射
NPC_SHIP_TYPES = [
    " Frigate",
    " Destroyer",
    " Battlecruiser",
    " Cruiser",
    " Battleship",
    " Hauler",
    " Transports",
    " Dreadnought",
    " Titan",
    " Supercarrier",
    " Carrier",
    " Officer",
    " Sentry",
    " Drone"
]

# 缓存字典
npc_classification_cache = {}
# 势力图标缓存字典
faction_icon_cache = {}

def get_npc_ship_scene(group_name):
    """根据组名确定NPC船只场景"""
    for scene in NPC_SHIP_SCENES:
        if group_name.startswith(scene):
            return scene.strip()
    return "Other"

def get_npc_ship_faction(group_name):
    """根据组名确定NPC船只势力"""
    for faction in NPC_SHIP_FACTIONS:
        if faction in group_name:
            return faction.strip()
    return "Other"

def get_npc_ship_type(group_name, name):
    """根据组名和物品名称确定NPC船只类型"""
    # 首先检查组名是否以Officer结尾
    if group_name.endswith("Officer"):
        return "Officer"
    
    # 然后检查物品名称是否以指定类型结尾
    for ship_type in NPC_SHIP_TYPES:
        if name.endswith(ship_type) or group_name.endswith(ship_type):
            return ship_type.strip()
    
    return "Other"

def read_yaml(file_path):
    """读取 types.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        types_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
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
            process_size INTEGER,
            npc_ship_scene TEXT,
            npc_ship_faction TEXT,
            npc_ship_type TEXT,
            npc_ship_faction_icon TEXT
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

def get_faction_icon(cursor, faction_name):
    """根据势力名称直接获取图标"""
    return NPC_FACTION_ICON_MAP.get(faction_name, "items_73_16_50.png")

def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    try:
        print(f"开始处理 {lang} 语言的数据库...")
        
        if lang == 'en':
            # 英文数据库保存完整数据
            cursor.execute('DROP TABLE IF EXISTS types')
            cursor.execute('''
                CREATE TABLE types (
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
                    process_size INTEGER,
                    npc_ship_scene TEXT,
                    npc_ship_faction TEXT,
                    npc_ship_type TEXT,
                    npc_ship_faction_icon TEXT
                )
            ''')
            
            print(f"正在处理英文数据...")
            total_items = len(types_data)
            processed_items = 0
            batch_data = []
            batch_size = 500
            
            # 获取分类和组信息
            cursor.execute("SELECT category_id, name FROM categories")
            categories_data = dict(cursor.fetchall())
            
            cursor.execute("SELECT group_id, name, categoryID FROM groups")
            groups_data = {row[0]: {'name': row[1], 'category_id': row[2]} for row in cursor.fetchall()}
            
            # 清空NPC分类缓存
            npc_classification_cache.clear()
            
            for type_id, item in types_data.items():
                name = item['name'].get(lang, "")
                description = item.get('description', {}).get(lang, "")
                published = item.get('published', False)
                volume = item.get('volume', None)
                marketGroupID = item.get('marketGroupID', None)
                metaGroupID = item.get('metaGroupID', 1)
                iconID = item.get('iconID', 0)
                groupID = item.get('groupID', 0)
                process_size = item.get('portionSize', None)
                capacity = item.get('capacity', None)
                mass = item.get('mass', None)
                variationParentTypeID = item.get('variationParentTypeID', None)
                
                # 获取组和分类信息
                group_info = groups_data.get(groupID, {'name': 'Unknown', 'category_id': 0})
                group_name = group_info['name']
                category_id = group_info['category_id']
                category_name = categories_data.get(category_id, 'Unknown')
                
                # 处理图标
                icon_filename = copy_and_rename_icon(type_id)
                
                # 获取NPC相关信息
                if category_id == 11:  # 只处理船只类型
                    npc_ship_scene = get_npc_ship_scene(group_name)
                    npc_ship_faction = get_npc_ship_faction(group_name)
                    npc_ship_type = get_npc_ship_type(group_name, name)
                    npc_ship_faction_icon = get_faction_icon(cursor, npc_ship_faction)
                    
                    # 保存到缓存
                    npc_classification_cache[type_id] = {
                        'scene': npc_ship_scene,
                        'faction': npc_ship_faction,
                        'type': npc_ship_type,
                        'faction_icon': npc_ship_faction_icon
                    }
                else:
                    npc_ship_scene = None
                    npc_ship_faction = None
                    npc_ship_type = None
                    npc_ship_faction_icon = None
                
                # 获取属性值
                res = get_attributes_value(cursor, type_id, [30, 50, 1153, 114, 118, 117, 116, 14, 13, 12, 1154, 102, 101])
                pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage, \
                high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot = res
                
                batch_data.append((
                    type_id, name, description, icon_filename, published, volume, capacity, mass,
                    marketGroupID, metaGroupID, iconID, groupID, group_name, category_id, category_name,
                    pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage,
                    high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot,
                    variationParentTypeID, process_size, npc_ship_scene, npc_ship_faction,
                    npc_ship_type, npc_ship_faction_icon
                ))
                
                processed_items += 1
                if len(batch_data) >= batch_size:
                    cursor.executemany('''
                        INSERT INTO types VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', batch_data)
                    print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
                    batch_data = []
            
            # 处理剩余的数据
            if batch_data:
                cursor.executemany('''
                    INSERT INTO types VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', batch_data)
                print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
        
        else:
            # 非英文数据库只保存变化的字段
            cursor.execute('DROP TABLE IF EXISTS types_translation')
            # 先删除视图（如果存在）
            cursor.execute('DROP VIEW IF EXISTS types')
            
            cursor.execute('''
                CREATE TABLE types_translation (
                    type_id INTEGER PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    group_name TEXT,
                    category_name TEXT
                )
            ''')
            
            # 连接英文数据库
            cursor.execute('ATTACH DATABASE ? AS en_db', (os.path.join('output/db', 'item_db_en.sqlite'),))
            
            # 创建视图
            cursor.execute('''
                CREATE VIEW types AS
                SELECT 
                    e.*,
                    COALESCE(t.name, e.name) as name,
                    COALESCE(t.description, e.description) as description,
                    COALESCE(t.group_name, e.group_name) as group_name,
                    COALESCE(t.category_name, e.category_name) as category_name
                FROM en_db.types e
                LEFT JOIN types_translation t ON e.type_id = t.type_id
            ''')
            
            print(f"正在处理 {lang} 语言的翻译数据...")
            total_items = len(types_data)
            processed_items = 0
            batch_data = []
            batch_size = 1000
            
            # 获取分类和组信息
            cursor.execute("SELECT category_id, name FROM categories")
            categories_data = dict(cursor.fetchall())
            
            cursor.execute("SELECT group_id, name, categoryID FROM groups")
            groups_data = {row[0]: {'name': row[1], 'category_id': row[2]} for row in cursor.fetchall()}
            
            for type_id, item in types_data.items():
                name = item['name'].get(lang, item['name'].get('en', ""))
                description = item.get('description', {}).get(lang, item.get('description', {}).get('en', ""))
                
                # 获取组和分类信息
                groupID = item.get('groupID', 0)
                group_info = groups_data.get(groupID, {'name': 'Unknown', 'category_id': 0})
                group_name = group_info['name']
                category_id = group_info['category_id']
                category_name = categories_data.get(category_id, 'Unknown')
                
                batch_data.append((type_id, name, description, group_name, category_name))
                
                processed_items += 1
                if len(batch_data) >= batch_size:
                    cursor.executemany('''
                        INSERT INTO types_translation VALUES (?,?,?,?,?)
                    ''', batch_data)
                    print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
                    batch_data = []
            
            # 处理剩余的数据
            if batch_data:
                cursor.executemany('''
                    INSERT INTO types_translation VALUES (?,?,?,?,?)
                ''', batch_data)
                print(f"已处理: {processed_items}/{total_items} ({(processed_items/total_items*100):.2f}%)")
            
            # 分离英文数据库
            cursor.execute('DETACH DATABASE en_db')
        
        print(f"已成功完成 {lang} 数据库的处理")
        
        # 处理特征数据
        process_trait_data(types_data, cursor, lang)
        
    except sqlite3.Error as e:
        print(f"SQLite错误: {str(e)}")
        raise
    except Exception as e:
        print(f"处理 {lang} 数据库时发生错误: {str(e)}")
        raise


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
