from ruamel.yaml import YAML
import sqlite3

yaml = YAML(typ='safe')

# 处理属性的目录类型，用于分类展示不同属性

def read_yaml(file_path):
    """读取 dogmaAttributeCategories.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = {}
        for part in yaml.load_all(file):
            data.update(part)
        return data


def create_dogma_attribute_categories_table(cursor):
    """创建 dogmaAttributeCategories 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaAttributeCategories (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
        )
    ''')


def process_data(data, cursor, lang):
    """处理 dogmaAttributeCategories 数据并插入数据库（针对单一语言）"""
    create_dogma_attribute_categories_table(cursor)

    for category_id, category_data in data.items():
        # 获取字段
        name = category_data.get('name', "")
        description = category_data.get('description', "")

        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO dogmaAttributeCategories (
                id, name, description
            ) VALUES (?, ?, ?)
        ''', (category_id, name, description))