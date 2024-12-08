from ruamel.yaml import YAML
import sqlite3

# 用于处理物品属性信息
# 提取出各属性id对应的名称

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 dogmaAttributes.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = {}
        for part in yaml.load_all(file):
            data.update(part)
        return data


def create_dogma_attributes_table(cursor):
    """创建精简版 dogmaAttributes 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaAttributes (
            attribute_id INTEGER PRIMARY KEY,
            categoryID INTEGER,
            name TEXT,
            display_name TEXT,
            description TEXT,
            tooltipDescription TEXT,
            iconID INTEGER
        )
    ''')


def process_data(data, cursor, lang):
    """处理 dogmaAttributes 数据并插入数据库（针对单一语言）"""
    create_dogma_attributes_table(cursor)

    for attr_id, attr_data in data.items():
        attributeID = attr_data.get('attributeID')

        # 多语言字段
        displayName = attr_data.get('displayNameID', {}).get(lang, "")
        name = attr_data.get('name', "")
        description = attr_data.get('description', "")
        iconID = attr_data.get('iconID', 0)
        categoryID = attr_data.get('categoryID', 0)
        tooltipDescription = attr_data.get('tooltipDescriptionID', {}).get(lang, "")

        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO dogmaAttributes (
                attribute_id, categoryID, name, display_name, description, tooltipDescription, iconID
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (attributeID, categoryID, name, displayName, description, tooltipDescription, iconID))