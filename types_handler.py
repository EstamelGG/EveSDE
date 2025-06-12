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
    {"en": "Asteroid ", "zh": "小行星带"},
    {"en": "Deadspace ", "zh": "死亡空间"},
    {"en": "FW ", "zh": "势力战争"},
    {"en": "Ghost Site ", "zh": "幽灵站点"},
    {"en": "Incursion ", "zh": "入侵"},
    {"en": "Mission ", "zh": "任务"},
    {"en": "Storyline ", "zh": "故事线"},
    {"en": "Abyssal ", "zh": "深渊"}
]

# NPC船只势力映射
NPC_SHIP_FACTIONS = [
    {"en": "Angel Cartel", "zh": "天使"},
    {"en": "Blood Raider", "zh": "血袭者"},
    {"en": "Guristas", "zh": "古斯塔斯"},
    {"en": "Mordu", "zh": "莫德团"},
    {"en": "Rogue Drone", "zh": "自由无人机"},
    {"en": "Sansha", "zh": "萨沙共和国"},
    {"en": "Serpentis", "zh": "天蛇"},
    {"en": "Overseer", "zh": "监察官"},
    {"en": "Sleeper", "zh": "冬眠者"},
    {"en": "Drifter", "zh": "流浪者"},
    {"en": "Amarr Empire", "zh": "艾玛帝国"},
    {"en": "Gallente Federation", "zh": "盖伦特联邦"},
    {"en": "Minmatar Republic", "zh": "米玛塔尔共和国"},
    {"en": "Caldari State", "zh": "加达里合众国"},
    {"en": "CONCORD", "zh": "统合部"},
    {"en": "Faction", "zh": "势力特属"},
    {"en": "Generic", "zh": "任务通用"},
    {"en": "Khanid", "zh": "卡尼迪"},
    {"en": "Thukker", "zh": "图克尔"}
]

# NPC势力ICON映射
NPC_FACTION_ICON_MAP = {
    "Angel Cartel": "faction_500011.png",
    "Blood Raider": "faction_500012.png",
    "Guristas": "faction_500010.png",
    "Mordu": "faction_500018.png",
    "Rogue Drone": "faction_500025.png",
    "Sansha": "faction_500019.png",
    "Serpentis": "faction_500020.png",
    "Overseer": "faction_500021.png",  # 使用默认图标
    "Sleeper": "faction_500005.png",
    "Drifter": "faction_500024.png",
    "Amarr Empire": "faction_500003.png",
    "Gallente Federation": "faction_500004.png",
    "Minmatar Republic": "faction_500002.png",
    "Caldari State": "faction_500001.png",
    "CONCORD": "faction_500006.png",
    "Faction": "faction_500021.png",  # 使用默认图标
    "Generic": "faction_500021.png",  # 使用默认图标
    "Khanid": "faction_500008.png",
    "Thukker": "faction_500015.png"
}

# NPC船只类型映射
NPC_SHIP_TYPES = [
    {"en": " Frigate", "zh": "护卫舰"},
    {"en": " Destroyer", "zh": "驱逐舰"},
    {"en": " Battlecruiser", "zh": "战列巡洋舰"},
    {"en": " Cruiser", "zh": "巡洋舰"},
    {"en": " Battleship", "zh": "战列舰"},
    {"en": " Hauler", "zh": "运输舰"},
    {"en": " Transports", "zh": "运输舰"},
    {"en": " Dreadnought", "zh": "无畏舰"},
    {"en": " Titan", "zh": "泰坦"},
    {"en": " Supercarrier", "zh": "超级航母"},
    {"en": " Carrier", "zh": "航空母舰"},
    {"en": " Officer", "zh": "官员"},
    {"en": " Sentry", "zh": "岗哨"},
    {"en": " Drone", "zh": "无人机"}
]

# 虫洞目标映射
WORMHOLE_TARGET_MAP = {
    1: {"zh": "1级虫洞空间", "other": "W-Space C1"},
    2: {"zh": "2级虫洞空间", "other": "W-Space C2"},
    3: {"zh": "3级虫洞空间", "other": "W-Space C3"},
    4: {"zh": "4级虫洞空间", "other": "W-Space C4"},
    5: {"zh": "5级虫洞空间", "other": "W-Space C5"},
    6: {"zh": "6级虫洞空间", "other": "W-Space C6"},
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
# 英文名称映射缓存
type_en_name_cache = {}


def get_npc_ship_scene(group_name, lang='en'):
    """根据组名确定NPC船只场景"""
    for scene in NPC_SHIP_SCENES:
        if group_name.startswith(scene['en']):
            if scene['en'].strip() == 'FW':
                return "Faction Warfare" if lang == 'en' else "势力战争"
            return scene[lang].strip()
    return "Other" if lang == 'en' else "其他"


def get_npc_ship_faction(group_name, lang='en'):
    """根据组名确定NPC船只势力"""
    for faction in NPC_SHIP_FACTIONS:
        if faction['en'] in group_name:
            return faction[lang].strip()
    return "Other" if lang == 'en' else "其他"


def get_npc_ship_type(group_name, name, lang='en'):
    """根据组名和物品名称确定NPC船只类型"""
    # 首先检查组名是否以Officer结尾
    if group_name.endswith("Officer"):
        return "Officer" if lang == 'en' else "官员"

    # 然后检查物品名称是否以指定类型结尾
    for ship_type in NPC_SHIP_TYPES:
        if name.endswith(ship_type['en']) or group_name.endswith(ship_type['en']):
            return ship_type[lang].strip()

    return "Other" if lang == 'en' else "其他"


def read_yaml(file_path):
    """读取 types.yaml 文件"""
    start_time = time.time()

    with open(file_path, 'r', encoding='utf-8') as file:
        types_data = yaml.load(file, Loader=SafeLoader)

    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return types_data


def read_repackaged_volumes():
    """读取 repackagedvolumes.json 文件"""
    try:
        with open('thirdparty_data_source/repackagedvolumes.json', 'r', encoding='utf-8') as file:
            repackaged_volumes = json.load(file)
        return repackaged_volumes
    except (FileNotFoundError, json.JSONDecodeError):
        print("警告：无法读取repackagedvolumes.json文件或文件格式不正确")
        return {}


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
    input_bpc_file = f"{x}_bpc_64.png"
    output_bpc_file = f"icon_{x}_bpc_64.png"

    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)
    input_bpc_path = os.path.join(input_directory, input_bpc_file)

    # 构造输入文件完整路径
    input_path = os.path.join(input_directory, input_file)
    # 检查源文件是否存在
    if not os.path.exists(input_path):
        return "items_7_64_15.png", None

    # 计算源文件的MD5
    file_md5 = calculate_file_md5(input_path)

    # 检查MD5是否存在于映射中
    if file_md5 in icon_md5_map:
        # 如果存在，检查目标文件是否存在
        output_file = icon_md5_map[file_md5]
        output_path = os.path.join(output_directory, output_file)
        if not os.path.exists(output_path):
            shutil.copy(input_path, output_path)
    else:
        # 如果MD5没有重复，则复制一次
        output_path = os.path.join(output_directory, output_file)
        if not os.path.exists(output_path):
            shutil.copy(input_path, output_path)
            # 将新的MD5和文件名添加到映射中
            icon_md5_map[file_md5] = output_file
            # 保存更新后的映射
            save_md5_map(icon_md5_map)


    # 检查是否存在bpc图标
    if os.path.exists(input_bpc_path):
        # 计算bpc文件的MD5
        bpc_md5 = calculate_file_md5(input_bpc_path)

        # 检查bpc的MD5是否存在于映射中
        if bpc_md5 in icon_md5_map:
            # 如果存在，检查目标文件是否存在
            output_bpc_file = icon_md5_map[bpc_md5]
            output_bpc_path = os.path.join(output_directory, output_bpc_file)
            if not os.path.exists(output_bpc_path):
                shutil.copy(input_bpc_path, output_bpc_path)
        else:
            # 复制bpc文件并重命名
            output_bpc_path = os.path.join(output_directory, output_bpc_file)
            if not os.path.exists(output_bpc_path):
                shutil.copy(input_bpc_path, output_bpc_path)
                # 将新的MD5和文件名添加到映射中
                icon_md5_map[bpc_md5] = output_bpc_file
                # 保存更新后的映射
                save_md5_map(icon_md5_map)
        return output_file, output_bpc_file

    return output_file, None


def create_types_table(cursor):
    """创建 types 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS types (
            type_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            de_name TEXT,
            en_name TEXT,
            es_name TEXT,
            fr_name TEXT,
            ja_name TEXT,
            ko_name TEXT,
            ru_name TEXT,
            zh_name TEXT,
            description TEXT,
            icon_filename TEXT,
            bpc_icon_filename TEXT,
            published BOOLEAN,
            volume REAL,
            repackaged_volume REAL,
            capacity REAL,
            mass REAL,
            marketGroupID INTEGER,
            metaGroupID INTEGER,
            iconID INTEGER,
            groupID INTEGER,
            group_name TEXT,
            categoryID INTEGER,
            category_name TEXT,
            pg_need REAL,
            cpu_need REAL,
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
            type_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            description TEXT,
            icon TEXT,
            target_value INTEGER,
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
            type_id, name, description, icon, target_value, target, stable_time, 
            max_stable_mass, max_jump_mass, size_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        type_id, name, description, icon, target_value, target, stable_time,
        max_stable_mass, max_jump_mass, size_type
    ))


def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    create_types_table(cursor)
    create_wormholes_table(cursor)  # 创建虫洞表
    group_to_category, category_id_to_name, group_id_to_name = fetch_and_process_data(cursor)

    # 读取repackaged_volumes数据
    repackaged_volumes = read_repackaged_volumes()

    # 如果是英文数据库，清空缓存并建立英文名称映射
    if lang == 'en':
        npc_classification_cache.clear()
        type_en_name_cache.clear()
        # 预处理所有英文名称
        for type_id, item in types_data.items():
            type_en_name_cache[type_id] = item['name'].get('en', "")

    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数

    for type_id, item in types_data.items():
        # 获取当前语言的名称作为主要name
        name = item['name'].get(lang, item['name'].get('en', ""))

        # 获取所有语言的名称
        names = {
            'de': item['name'].get('de', name),
            'en': item['name'].get('en', name),
            'es': item['name'].get('es', name),
            'fr': item['name'].get('fr', name),
            'ja': item['name'].get('ja', name),
            'ko': item['name'].get('ko', name),
            'ru': item['name'].get('ru', name),
            'zh': item['name'].get('zh', name)
        }

        description = item.get('description', {}).get(lang, item.get('description', {}).get('en', ""))
        published = item.get('published', False)
        volume = item.get('volume', None)
        # 获取重新打包体积
        repackaged_volume = repackaged_volumes.get(str(type_id), None)
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

        if category_id == 11:  # 对所有语言的数据库都处理分类
            if lang == 'en':  # 英文数据库处理并缓存
                # 同时缓存中英文版本
                npc_ship_scene_en = get_npc_ship_scene(group_name, 'en')
                npc_ship_scene_zh = get_npc_ship_scene(group_name, 'zh')
                npc_ship_faction_en = get_npc_ship_faction(group_name, 'en')
                npc_ship_faction_zh = get_npc_ship_faction(group_name, 'zh')
                npc_ship_type_en = get_npc_ship_type(group_name, name, 'en')
                npc_ship_type_zh = get_npc_ship_type(group_name, name, 'zh')
                npc_ship_faction_icon = get_faction_icon(cursor, npc_ship_faction_en)

                # 保存到缓存
                npc_classification_cache[type_id] = {
                    'scene': {'en': npc_ship_scene_en, 'zh': npc_ship_scene_zh},
                    'faction': {'en': npc_ship_faction_en, 'zh': npc_ship_faction_zh},
                    'type': {'en': npc_ship_type_en, 'zh': npc_ship_type_zh},
                    'faction_icon': npc_ship_faction_icon
                }

                # 使用英文版本
                npc_ship_scene = npc_ship_scene_en
                npc_ship_faction = npc_ship_faction_en
                npc_ship_type = npc_ship_type_en
            elif type_id in npc_classification_cache:  # 其他语言从缓存获取
                cached_data = npc_classification_cache[type_id]
                if lang == 'zh':
                    # 中文数据库使用中文版本
                    npc_ship_scene = cached_data['scene']['zh']
                    npc_ship_faction = cached_data['faction']['zh']
                    npc_ship_type = cached_data['type']['zh']
                else:
                    # 其他语言使用英文版本
                    npc_ship_scene = cached_data['scene']['en']
                    npc_ship_faction = cached_data['faction']['en']
                    npc_ship_type = cached_data['type']['en']
                npc_ship_faction_icon = cached_data['faction_icon']

        copied_file, bpc_copied_file = copy_and_rename_icon(type_id)
        res = get_attributes_value(cursor, type_id, [30, 50, 1153, 114, 118, 117, 116, 14, 13, 12, 1154, 102, 101])

        pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage, \
            high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot = res

        # 处理虫洞数据
        if groupID == 988:
            process_wormhole_data(cursor, type_id, name, description, copied_file, lang)

        # 添加到批处理列表
        batch_data.append((
            type_id, name,
            names['de'], names['en'], names['es'], names['fr'],
            names['ja'], names['ko'], names['ru'], names['zh'],
            description, copied_file, bpc_copied_file, published, volume, repackaged_volume, capacity, mass,
            marketGroupID,
            metaGroupID, iconID, groupID, group_name, category_id, category_name,
            pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage,
            high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot, variationParentTypeID,
            process_size, npc_ship_scene, npc_ship_faction, npc_ship_type, npc_ship_faction_icon
        ))

        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR IGNORE INTO types (
                    type_id, name, 
                    de_name, en_name, es_name, fr_name, 
                    ja_name, ko_name, ru_name, zh_name,
                    description, icon_filename, bpc_icon_filename, published, volume, repackaged_volume, capacity, mass, marketGroupID,
                    metaGroupID, iconID, groupID, group_name, categoryID, category_name,
                    pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage,
                    high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot,
                    variationParentTypeID, process_size, npc_ship_scene, npc_ship_faction, 
                    npc_ship_type, npc_ship_faction_icon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表

    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR IGNORE INTO types (
                type_id, name, 
                de_name, en_name, es_name, fr_name, 
                ja_name, ko_name, ru_name, zh_name,
                description, icon_filename, bpc_icon_filename, published, volume, repackaged_volume, capacity, mass, marketGroupID,
                metaGroupID, iconID, groupID, group_name, categoryID, category_name,
                pg_need, cpu_need, rig_cost, em_damage, them_damage, kin_damage, exp_damage,
                high_slot, mid_slot, low_slot, rig_slot, gun_slot, miss_slot,
                variationParentTypeID, process_size, npc_ship_scene, npc_ship_faction, 
                npc_ship_type, npc_ship_faction_icon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
