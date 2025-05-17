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
            group_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            de_name TEXT,
            en_name TEXT,
            es_name TEXT,
            fr_name TEXT,
            ja_name TEXT,
            ko_name TEXT,
            ru_name TEXT,
            zh_name TEXT,
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

    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数

    for group_id, item in groups_data.items():
        
        # 获取所有语言的名称
        names = {
            'de': item['name'].get('de', ''),
            'en': item['name'].get('en', ''),
            'es': item['name'].get('es', ''),
            'fr': item['name'].get('fr', ''),
            'ja': item['name'].get('ja', ''),
            'ko': item['name'].get('ko', ''),
            'ru': item['name'].get('ru', ''),
            'zh': item['name'].get('zh', '')
        }

        # 为特定 group_id 添加后缀
        suffix = ""
        if group_id == 1884:
            suffix = "(R4)"
        elif group_id == 1920:
            suffix = "(R8)"
        elif group_id == 1921:
            suffix = "(R16)"
        elif group_id == 1922:
            suffix = "(R32)"
        elif group_id == 1923:
            suffix = "(R64)"

        # 如果存在后缀，为所有语言添加后缀
        if suffix:
            for lang in names:
                if names[lang]:  # 只有当名称不为空时才添加后缀
                    names[lang] = names[lang] + suffix

        # 获取当前语言的名称作为主要name
        name = names[lang]

        categoryID = item['categoryID']
        iconID = item.get('iconID', 0)
        anchorable = item['anchorable']
        anchored = item['anchored']
        fittableNonSingleton = item['fittableNonSingleton']
        published = item['published']
        useBasePrice = item['useBasePrice']

        # 添加到批处理列表
        batch_data.append((
            group_id, name,
            names['de'], names['en'], names['es'], names['fr'],
            names['ja'], names['ko'], names['ru'], names['zh'],
            categoryID, iconID, anchorable, anchored, fittableNonSingleton,
            published, useBasePrice, "items_73_16_50.png"
        ))

        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR IGNORE INTO groups (
                    group_id, name,
                    de_name, en_name, es_name, fr_name,
                    ja_name, ko_name, ru_name, zh_name,
                    categoryID, iconID, anchorable, anchored,
                    fittableNonSingleton, published, useBasePrice, icon_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表

    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR IGNORE INTO groups (
                group_id, name,
                de_name, en_name, es_name, fr_name,
                ja_name, ko_name, ru_name, zh_name,
                categoryID, iconID, anchorable, anchored,
                fittableNonSingleton, published, useBasePrice, icon_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)