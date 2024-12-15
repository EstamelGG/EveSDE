import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
import os
import time
from cache_manager import register_cache_cleaner

# 定义源和目标目录
ICONS_SOURCE_DIR = 'Data/Icons/items'
ICONS_DEST_DIR = 'output/Icons'

# 图标目录与实际目录的局部映射
# key是yaml中的关键词，value是实际映射的文件的开头
icon_path_map = {
    "/UI/Texture/Icons/Modules/": "items_modules",
    "/UI/Texture/Icons/Ammo/": "items_ammo",
    "/UI/Texture/Icons/Brackets/": "items_brackets",
    "/UI/Texture/Icons/DustIcons/": "items_DustIcons",
    "/UI/Texture/Icons/generic/": "items_generic",
    "/UI/Texture/Icons/Inventory/": "items_Inventory",
    "/UI/Texture/Icons/ItemOverlay/": "items_ItemOverlay",
    "/UI/Texture/Icons/notifications/": "items_notifications",
    "/UI/Texture/Icons/RewardTrack/": "items_RewardTrack",
    "/UI/Texture/Icons/SkillPoints/": "items_SkillPoints",
    "/UI/Texture/Icons/StatusEffects/": "items_StatusEffects",
    "/UI/Texture/Icons/Triglavian/": "items_Triglavian",
    "/ui/texture/corps/": "corporations",
    "/ui/texture/icons/": "items"
}

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('iconIDs_handler', clear_cache)

def read_yaml(file_path):
    """读取 iconIDs.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data


def ensure_icons_directory_exists(directory):
    """检查并确保目标目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def copy_and_rename_icons(icon_data):
    """整理图像文件并创建文件名映射字典"""
    icon_filename_mapping = {}  # icon_id -> new_icon_file
    raw_icon_filename_mapping = {}
    ensure_icons_directory_exists(ICONS_DEST_DIR)  # 确保目标目录存在

    for icon_id, details in icon_data.items():
        icon_file = details.get('iconFile', "")
        raw_icon_filename_mapping[icon_id] = icon_file
        dest_icon_filename = ""
        # 判断 iconFile 是否包含 "/icons/" 等目录, 其他筛选条件后续再加
        for key in icon_path_map:
            if key.lower() in icon_file.lower():
                icon_filename = str(icon_file).split("/")[-1]
                dest_icon_filename = f"{icon_path_map[key]}_{icon_filename}".lower()
                break
        dest_file_path = os.path.join(ICONS_DEST_DIR, dest_icon_filename)
        if not os.path.exists(dest_file_path):
            dest_icon_filename = ""
        dest_icon_filename_fix = dest_icon_filename  # .split(".")[0] # 只留文件名
        icon_filename_mapping[icon_id] = dest_icon_filename_fix
    return raw_icon_filename_mapping, icon_filename_mapping


def create_iconIDs_table(cursor):
    """创建 iconIDs 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iconIDs (
            icon_id INTEGER PRIMARY KEY,
            description TEXT,
            iconFile TEXT,
            iconFile_new TEXT
        )
    ''')


def insert_iconIDs(cursor, icon_data, raw_icon_filename_mapping, icon_filename_mapping):
    """将整理好的 iconIDs 数据插入到数据库"""
    for icon_id, details in icon_data.items():
        description = details.get('description', "")

        # 获取新的 iconFile（如果有映射的话）
        new_icon_file = icon_filename_mapping.get(icon_id, details.get('iconFile', ""))
        old_icon_file = raw_icon_filename_mapping.get(icon_id, details.get('iconFile', ""))

        # 插入或替换数据
        cursor.execute('''
            INSERT OR REPLACE INTO iconIDs (icon_id, description, iconFile, iconFile_new)
            VALUES (?, ?, ?, ?)
        ''', (icon_id, description, old_icon_file, new_icon_file))


def process_data(icon_data, cursor, lang):
    """处理 iconIDs 数据并插入数据库"""
    # 处理并复制文件，获取文件名映射
    raw_icon_filename_mapping, icon_filename_mapping = copy_and_rename_icons(icon_data)

    # 插入数据库（使用新文件名）
    create_iconIDs_table(cursor)
    insert_iconIDs(cursor, icon_data, raw_icon_filename_mapping, icon_filename_mapping)
