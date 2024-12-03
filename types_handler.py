from ruamel.yaml import YAML
import sqlite3

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 types.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        types_data = {}
        for part in yaml.load_all(file):
            types_data.update(part)
        return types_data

def create_types_table(cursor):
    """创建 types 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS types (
            type_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            published BOOLEAN,
            volume REAL,
            marketGroupID INTEGER,
            metaGroupID INTEGER,
            iconID INTEGER,
            groupID INTEGER,
            pg_need REAL,  -- 新增 pg_need 列
            cpu_need REAL  -- 新增 cpu_need 列
        )
    ''')

def process_data(types_data, cursor, lang):
    """处理 types 数据并插入数据库（针对单一语言）"""
    create_types_table(cursor)

    for item_id, item in types_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        description = item.get('description', {}).get(lang, item.get('description', {}).get('en', ""))  # 优先取 lang，没有则取 en
        published = item.get('published', False)
        volume = item.get('volume', 0)
        marketGroupID = item.get('marketGroupID', 0)
        metaGroupID = item.get('metaGroupID', 1)
        iconID = item.get('iconID', 0)
        groupID = item.get('groupID', 0)

        # 获取 pg_need 和 cpu_need 的值
        pg_need = get_attribute_value(cursor, item_id, 30)  # 获取 pg占用 的值 (pg_need)
        cpu_need = get_attribute_value(cursor, item_id, 50)  # 获取 cpu占用 的值 (cpu_need)

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO types (type_id, name, description, published, volume, marketGroupID, metaGroupID, iconID, groupID, pg_need, cpu_need)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, name, description, published, volume, marketGroupID, metaGroupID, iconID, groupID, pg_need, cpu_need))

def get_attribute_value(cursor, type_id, attribute_id):
    """从 typeAttributes 表获取两个属性的值"""
    cursor.execute('''
        SELECT value FROM typeAttributes WHERE type_id = ? AND attribute_id = ?
    ''', (type_id, attribute_id))
    result = cursor.fetchone()
    return result[0] if result else -1  # 如果没有值，返回 None