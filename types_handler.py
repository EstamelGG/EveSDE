from ruamel.yaml import YAML
import sqlite3
import shutil
import os

yaml = YAML(typ='safe')


def read_yaml(file_path):
    """读取 types.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        types_data = {}
        for part in yaml.load_all(file):
            types_data.update(part)
        return types_data


def copy_and_rename_icon(x):
    # 定义文件路径
    input_directory = "Data/Types"
    output_directory = "output/Icons"
    input_file = f"{x}_64.png"
    output_file = f"icon_{x}_64.png"

    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)

    # 构造输入文件完整路径
    input_path = os.path.join(input_directory, input_file)

    # 检查文件是否存在
    if os.path.exists(input_path):
        # 构造输出文件完整路径
        output_path = os.path.join(output_directory, output_file)

        # 复制文件并重命名
        if not os.path.exists(output_file):
            shutil.copy(input_path, output_path)
        return output_file
    else:
        return ""


def create_types_table(cursor):
    """创建 types 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS types (
            type_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            icon_filename TEXT,
            published BOOLEAN,
            volume INTEGER,
            marketGroupID INTEGER,
            metaGroupID INTEGER,
            iconID INTEGER,
            groupID INTEGER,
            pg_need INTEGER,
            cpu_need INTEGER
        )
    ''')


def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    create_types_table(cursor)

    for item_id, item in types_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        description = item.get('description', {}).get(lang,
                                                      item.get('description', {}).get('en', ""))  # 优先取 lang，没有则取 en
        published = item.get('published', False)
        volume = item.get('volume', 0)
        marketGroupID = item.get('marketGroupID', 0)
        metaGroupID = item.get('metaGroupID', 1)
        iconID = item.get('iconID', 0)
        groupID = item.get('groupID', 0)
        copied_file = copy_and_rename_icon(item_id)  # 复制物品图像
        # 获取 pg_need 和 cpu_need 的值
        pg_need = get_attribute_value(cursor, item_id, 30)  # 获取 pg占用 的值 (pg_need)
        cpu_need = get_attribute_value(cursor, item_id, 50)  # 获取 cpu占用 的值 (cpu_need)

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO types (type_id, name, description, icon_filename, published, volume, marketGroupID, metaGroupID, iconID, groupID, pg_need, cpu_need)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, name, description,copied_file,  published, volume, marketGroupID, metaGroupID, iconID, groupID, pg_need,
            cpu_need))


def get_attribute_value(cursor, type_id, attribute_id):
    """从 typeAttributes 表获取两个属性的值"""
    cursor.execute('''
        SELECT value FROM typeAttributes WHERE type_id = ? AND attribute_id = ?
    ''', (type_id, attribute_id))
    result = cursor.fetchone()
    return result[0] if result else -1  # 如果没有值，返回 None
