from ruamel.yaml import YAML

yaml = YAML(typ='safe')

# 提取所有组信息

def read_yaml(file_path):
    """读取 groups.yaml 文件"""
    import time
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data

def create_groups_table(cursor):
    """创建 groups 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            name TEXT,
            iconID INTEGER,
            categoryID INTEGER,
            anchorable BOOLEAN,
            anchored BOOLEAN,
            fittableNonSingleton BOOLEAN,
            published BOOLEAN,
            useBasePrice BOOLEAN,
            icon_filename TEXT
        )
    ''')

def process_data(groups_data, cursor, lang):
    """处理 groups 数据并插入数据库（针对单一语言）"""
    create_groups_table(cursor)

    for group_id, item in groups_data.items():
        name = item['name'].get(lang, item['name'].get('en', ""))  # 优先取 lang，没有则取 en
        if name is None:
            continue

        categoryID = item['categoryID']
        iconID = item.get('iconID', 0)
        anchorable = item['anchorable']
        anchored = item['anchored']
        fittableNonSingleton = item['fittableNonSingleton']
        published = item['published']
        useBasePrice = item['useBasePrice']

        # 使用 INSERT OR IGNORE 语句，避免重复插入
        cursor.execute('''
            INSERT OR IGNORE INTO groups (group_id, name, categoryID, iconID, anchorable, anchored, fittableNonSingleton, published, useBasePrice, icon_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (group_id, name, categoryID, iconID, anchorable, anchored, fittableNonSingleton, published, useBasePrice, "items_73_16_50.png"))