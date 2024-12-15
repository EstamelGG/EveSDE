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

# 虫洞目标映射
WORMHOLE_TARGET_MAP = {
    1: {"zh": "1级虫洞空间", "other": "W-Space C2"},
    2: {"zh": "2级虫洞空间", "other": "W-Space C3"},
    3: {"zh": "3级虫洞空间", "other": "W-Space C4"},
    4: {"zh": "4级虫洞空间", "other": "W-Space C5"},
    5: {"zh": "5级虫洞空间", "other": "W-Space C6"},
    6: {"zh": "6级虫洞空间", "other": "W-Space C7"},
    7: {"zh": "高安星系", "other": "High-Sec Space"},
    8: {"zh": "低安星系", "other": "Low-Sec Space"},
    9: {"zh": "0.0星系", "other": "Null-Sec Space"},
    12: {"zh": "希拉星系", "other": "Thera"},
    13: {"zh": "破碎星系", "other": "Shattered WH"},
    14: {"zh": "流浪者 Sentinel", "other": "Drifter Sentinel"},
    15: {"zh": "流浪者 Barbican", "other": "Drifter Barbican"},
    16: {"zh": "流浪者 Vidette", "other": "Drifter Vidette"},
    17: {"zh": "流浪者 Conflux", "other": "Drifter Conflux"},
    18: {"zh": "流浪者 Redoubt", "other": "Drifter Redoubt"},
    25: {"zh": "波赫文", "other": "Pochven"}
}

# 虫洞尺寸映射
WORMHOLE_SIZE_MAP = {
    2000000000: {"zh": "XL(旗舰)", "other": "XL(Capital)"},
    1000000000: {"zh": "XL(货舰)", "other": "XL(Freighter)"},
    375000000: {"zh": "L(战列舰)", "other": "L(Battleship)"},
    62000000: {"zh": "M(战巡)", "other": "M(Battlecruiser)"},
    5000000: {"zh": "S(驱逐舰)", "other": "S(Destroyer)"}
}

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

def format_number(value, unit=""):
    """格式化数字，添加千分位分隔符，去除多余的零和小数点，添加单位"""
    if not value:
        return None
    
    # 转换为浮点数
    num = float(value)
    
    # 将数字转换为字符串，并去除多余的零和小数点
    formatted = f"{num:f}".rstrip('0').rstrip('.')
    
    # 处理整数部分的千分位
    parts = formatted.split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else ""
    
    # 添加千分位分隔符
    integer_part = "{:,}".format(int(integer_part))
    
    # 重新组合整数和小数部分
    if decimal_part:
        formatted = f"{integer_part}.{decimal_part}"
    else:
        formatted = integer_part
    
    # 添加单位（如果有）
    if unit:
        formatted += unit
    
    return formatted

def create_wormholes_table(cursor):
    """创建虫洞数据表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wormholes (
            type_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            icon TEXT,
            target TEXT,
            stable_time TEXT,
            max_stable_mass TEXT,
            max_jump_mass TEXT,
            size_type TEXT
        )
    ''')

def get_wormhole_size_type(max_jump_mass, lang):
    """根据最大跳跃质量确定虫洞尺寸类型"""
    if not max_jump_mass:
        return None
    
    # 直接使用浮点数进行比较
    for threshold, size_map in sorted(WORMHOLE_SIZE_MAP.items(), reverse=True):
        if max_jump_mass >= threshold:
            return size_map["zh" if lang == "zh" else "other"]
    return None

def get_wormhole_target(target_value, name, lang):
    """获取虫洞目标描述"""
    # 特殊处理 K162
    if "K162" in name:
        return "出口虫洞" if lang == "zh" else "Exit WH"
    
    # 特殊处理 U372
    if "U372" in name:
        return "0.0 无人机星域" if lang == "zh" else "Null-Sec Drone Regions"
    
    # 处理常规映射
    if target_value and int(target_value) in WORMHOLE_TARGET_MAP:
        return WORMHOLE_TARGET_MAP[int(target_value)]["zh" if lang == "zh" else "other"]
    
    return "Unknown"

def process_wormhole_data(cursor, type_id, name, description, icon, lang):
    """处理虫洞数据"""
    # 获取虫洞属性
    attributes = get_attributes_value(cursor, type_id, [1381, 1382, 1383, 1385])
    target_value, stable_time, max_stable_mass, max_jump_mass = attributes
    
    # 处理目标
    target = get_wormhole_target(target_value, name, lang)
    
    # 先进行数值计算
    if stable_time:
        stable_time = float(stable_time) / 60  # 转换为小时
    if max_stable_mass:
        max_stable_mass = float(max_stable_mass)  # 转换为浮点数
    if max_jump_mass:
        max_jump_mass = float(max_jump_mass)  # 转换为浮点数
    
    # 获取尺寸类型（在格式化之前）
    size_type = get_wormhole_size_type(max_jump_mass, lang)
    
    # 格式化并添加单位
    stable_time = format_number(stable_time, "h") if stable_time else None
    max_stable_mass = format_number(max_stable_mass, "Kg") if max_stable_mass else None
    max_jump_mass = format_number(max_jump_mass, "Kg") if max_jump_mass else None
    
    # 插入数据
    cursor.execute('''
        INSERT OR IGNORE INTO wormholes (
            type_id, name, description, icon, target, stable_time, 
            max_stable_mass, max_jump_mass, size_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        type_id, name, description, icon, target, stable_time,
        max_stable_mass, max_jump_mass, size_type
    ))

def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    create_types_table(cursor)
    create_wormholes_table(cursor)  # 创建虫洞表
    group_to_category, category_id_to_name, group_id_to_name = fetch_and_process_data(cursor)
    
    # 如果是英文数据库，清空缓存
    if lang == 'en':
        npc_classification_cache.clear()
    
    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for type_id, item in types_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))
        description = item.get('description', {}).get(lang, item.get('description', {}).get('en', ""))
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
        group_name = group_id_to_name.get(groupID, 'Unknown')
        category_id = group_to_category.get(groupID, 0)
        category_name = category_id_to_name.get(category_id, 'Unknown')
        
        # 处理NPC船只分类
        npc_ship_scene = None
        npc_ship_faction = None
        npc_ship_type = None
        npc_ship_faction_icon = None
        
        if lang == 'en' and category_id == 11:  # 只在英文数据库中处理分类
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
        elif type_id in npc_classification_cache:  # 其他语言从缓存获取
            cached_data = npc_classification_cache[type_id]
            npc_ship_scene = cached_data['scene']
            npc_ship_faction = cached_data['faction']
            npc_ship_type = cached_data['type']
            npc_ship_faction_icon = cached_data['faction_icon']
        
        copied_file = copy_and_rename_icon(type_id)
        res = get_attributes_value(cursor, type_id, [30, 50, 1153, 114, 118, 117, 116, 14, 13, 12, 1154, 102, 101])
        
        pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage, \
        high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot = res
        
        # 处理虫洞数据
        if groupID == 988:
            process_wormhole_data(cursor, type_id, name, description, copied_file, lang)
            
        # 添加到批处理列表
        batch_data.append((
            type_id, name, description, copied_file, published, volume, capacity, mass, marketGroupID,
            metaGroupID, iconID, groupID, group_name, category_id, category_name,
            pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage,
            high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot, variationParentTypeID,
            process_size, npc_ship_scene, npc_ship_faction, npc_ship_type, npc_ship_faction_icon
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR IGNORE INTO types (
                    type_id, name, description, icon_filename, published, volume, capacity, mass, marketGroupID,
                    metaGroupID, iconID, groupID, group_name, categoryID, category_name, pg_need, cpu_need, rig_cost,
                    em_damage, them_damage, kin_damage, exp_damage, high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot,
                    variationParentTypeID, process_size, npc_ship_scene, npc_ship_faction, npc_ship_type, npc_ship_faction_icon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR IGNORE INTO types (
                type_id, name, description, icon_filename, published, volume, capacity, mass, marketGroupID,
                metaGroupID, iconID, groupID, group_name, categoryID, category_name, pg_need, cpu_need, rig_cost,
                em_damage, them_damage, kin_damage, exp_damage, high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot,
                variationParentTypeID, process_size, npc_ship_scene, npc_ship_faction, npc_ship_type, npc_ship_faction_icon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)

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
