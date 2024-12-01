from ruamel.yaml import YAML

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 categories.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)

def create_categories_table(cursor):
    """创建 categories 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY,
            name TEXT,
            iconID INTEGER,
            published BOOLEAN
        )
    ''')

def process_data(categories_data, cursor, lang):
    """处理 categories 数据并插入数据库（针对单一语言）"""
    create_categories_table(cursor)

    for item_id, item in categories_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        published = item['published']
        iconID = item.get('iconID', 0)  # 获取 iconID，如果没有则设为 0

        if name is None:
            continue

        # 使用 INSERT OR REPLACE 语句，当 category_id 已存在时更新记录
        cursor.execute('''
            INSERT OR REPLACE INTO categories (category_id, name, iconID, published)
            VALUES (?, ?, ?, ?)
        ''', (item_id, name, iconID, published))