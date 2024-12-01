import sqlite3
from ruamel.yaml import YAML

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 iconIDs.yaml 文件并返回数据"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)

def create_iconIDs_table(cursor):
    """创建 iconIDs 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iconIDs (
            icon_id INTEGER PRIMARY KEY,
            description TEXT,
            iconFile TEXT
        )
    ''')

def insert_iconIDs(cursor, icon_data):
    """将 iconIDs 数据插入到数据库"""
    for icon_id, details in icon_data.items():
        description = details.get('description', "")
        icon_file = details.get('iconFile', "")

        # 去除路径中的 'res:'，只保留相对路径
        icon_file = icon_file.replace("res:", "")

        cursor.execute('''
            INSERT OR REPLACE INTO iconIDs (icon_id, description, iconFile)
            VALUES (?, ?, ?)
        ''', (icon_id, description, icon_file))

def process_data(icon_data, cursor, lang):
    """处理 iconIDs 数据并插入数据库"""
    create_iconIDs_table(cursor)
    insert_iconIDs(cursor, icon_data)