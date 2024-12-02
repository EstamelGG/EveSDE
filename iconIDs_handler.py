import os
import shutil
import sqlite3
from ruamel.yaml import YAML

# 提取图片id和图片文件名
yaml = YAML(typ='safe')

# 定义源和目标目录
ICONS_SOURCE_DIR = 'Data/Icons/items'
ICONS_DEST_DIR = 'output/Icons'


def read_yaml(file_path):
    """读取 iconIDs.yaml 文件并返回数据"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)


def ensure_icons_directory_exists(directory):
    """检查并确保目标目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} created.")
    else:
        print(f"Directory {directory} already exists.")


def copy_and_rename_icons(icon_data):
    """整理图像文件并创建文件名映射字典"""
    icon_filename_mapping = {}  # icon_id -> new_icon_file
    ensure_icons_directory_exists(ICONS_DEST_DIR)  # 确保目标目录存在
    copy_num = 0
    for icon_id, details in icon_data.items():
        icon_file = details.get('iconFile', "")

        # 判断 iconFile 是否包含 "/icons/" 目录
        if "/" in icon_file:
            if "icons" == str(icon_file).split("/")[-2]:
                file_name = str(icon_file).split("/")[-1]
                source_path = os.path.join(ICONS_SOURCE_DIR, file_name)
                dest_path = os.path.join(ICONS_DEST_DIR, f"item_{file_name}")

                # 如果源文件不存在，则默认用73_16_50
                if not os.path.exists(source_path):
                    source_path = os.path.join(ICONS_SOURCE_DIR, "73_16_50.png")
                if not os.path.exists(dest_path):  # 如果目标文件不存在
                    shutil.copy(source_path, dest_path)
                    copy_num += 1
                icon_filename_mapping[icon_id] = f"{os.path.basename(dest_path)}"
                    # print(f"Copied and renamed {file_name} to {dest_path}")
                # else:
                # print(f"Warning: {file_name} not found in source directory.")
    print(f"Copied %i icons" % copy_num)
    return icon_filename_mapping


def create_iconIDs_table(cursor):
    """创建 iconIDs 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iconIDs (
            icon_id INTEGER PRIMARY KEY,
            description TEXT,
            iconFile TEXT
        )
    ''')


def insert_iconIDs(cursor, icon_data, icon_filename_mapping):
    """将整理好的 iconIDs 数据插入到数据库"""
    for icon_id, details in icon_data.items():
        description = details.get('description', "")

        # 获取新的 iconFile（如果有映射的话）
        new_icon_file = icon_filename_mapping.get(icon_id, details.get('iconFile', ""))

        # 插入或替换数据
        cursor.execute('''
            INSERT OR REPLACE INTO iconIDs (icon_id, description, iconFile)
            VALUES (?, ?, ?)
        ''', (icon_id, description, new_icon_file))


def process_data(icon_data, cursor, lang):
    """处理 iconIDs 数据并插入数据库"""
    icon_filename_mapping = copy_and_rename_icons(icon_data)

    # 插入数据库（使用新文件名）
    create_iconIDs_table(cursor)
    insert_iconIDs(cursor, icon_data, icon_filename_mapping)
