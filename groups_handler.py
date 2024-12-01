from ruamel.yaml import YAML

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 groups.yaml 文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)

def create_groups_table(cursor):
    """创建 groups 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            name TEXT,
            categoryID INTEGER,
            anchorable BOOLEAN,
            anchored BOOLEAN,
            fittableNonSingleton BOOLEAN,
            published BOOLEAN,
            useBasePrice BOOLEAN
        )
    ''')

def process_data(groups_data, cursor, lang):
    """处理 groups 数据并插入数据库（针对单一语言）"""
    create_groups_table(cursor)

    for item_id, item in groups_data.items():
        name = item['name'].get(lang, None)
        if name is None:
            continue

        categoryID = item['categoryID']
        anchorable = item['anchorable']
        anchored = item['anchored']
        fittableNonSingleton = item['fittableNonSingleton']
        published = item['published']
        useBasePrice = item['useBasePrice']

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO groups (group_id, name, categoryID, anchorable, anchored, fittableNonSingleton, published, useBasePrice)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item_id, name, categoryID, anchorable, anchored, fittableNonSingleton, published, useBasePrice))