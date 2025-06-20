from ruamel.yaml import YAML
import os
import time

yaml = YAML(typ='safe')

# 提取所有目录信息

categories_id_icon_map = {
    0: "items_7_64_4.png",
    1: "items_70_128_11.png",
    2: "icon_6_64.png",
    3: "icon_1932_64.png",
    4: "icon_34_64.png",
    5: "icon_29668_64.png",
    6: "items_26_64_2.png",
    7: "items_2_64_11.png",
    8: "items_5_64_2.png",
    9: "icon_1002_64.png",
    10: "items_6_64_3.png",
    11: "items_26_64_10.png",
    14: "items_modules_fleetboost_infobase.png",
    16: "icon_2403_64.png",
    17: "icon_11068_64.png",
    18: "icon_2454_64.png",
    20: "items_40_64_16.png",
    22: "icon_33475_64.png",
    23: "icon_17174_64.png",
    24: "items_comprfuel_amarr.png",
    25: "items_inventory_moonasteroid_r4.png",
    30: "items_inventory_cratexvishirt.png",
    32: "items_76_64_7.png",
    34: "icon_30752_64.png",
    35: "items_55_64_11.png",
    39: "items_95_64_6.png",
    40: "icon_32458_64.png",
    41: "icon_2409_64.png",
    42: "items_97_64_10.png",
    43: "items_99_64_8.png",
    46: "icon_2233_64.png",
    63: "icon_19658_64.png",
    65: "icon_40340_64.png",
    66: "icon_35923_64.png",
    87: "icon_23061_64.png",
    91: "items_rewardtrack_crateskincontainer.png",
    2100: "icon_57203_64.png",
    2118: "icon_83291_64.png",
    2143: "icon_81143_64.png",
}


def read_yaml(file_path):
    """读取 categories.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data


def create_categories_table(cursor):
    """创建 categories 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            de_name TEXT,
            en_name TEXT,
            es_name TEXT,
            fr_name TEXT,
            ja_name TEXT,
            ko_name TEXT,
            ru_name TEXT,
            zh_name TEXT,
            icon_filename TEXT,
            iconID INTEGER,
            published BOOLEAN
        )
    ''')


def process_data(categories_data, cursor, lang):
    """处理 categories 数据并插入数据库（针对单一语言）"""
    create_categories_table(cursor)

    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数

    for item_id, item in categories_data.items():
        # 获取当前语言的名称作为主要name
        name = item['name'].get(lang, item['name'].get('en', ""))
        
        # 获取所有语言的名称
        names = {
            'de': item['name'].get('de', name),
            'en': item['name'].get('en', name),
            'es': item['name'].get('es', name),
            'fr': item['name'].get('fr', name),
            'ja': item['name'].get('ja', name),
            'ko': item['name'].get('ko', name),
            'ru': item['name'].get('ru', name),
            'zh': item['name'].get('zh', name)
        }

        if name is None:
            continue

        published = item['published']
        iconID = item.get('iconID', 0)  # 获取 iconID，如果没有则设为 0
        dest_icon_filename = categories_id_icon_map.get(item_id, "items_73_16_50.png")

        # 添加到批处理列表
        batch_data.append((
            item_id, name,
            names['de'], names['en'], names['es'], names['fr'],
            names['ja'], names['ko'], names['ru'], names['zh'],
            dest_icon_filename, iconID, published
        ))

        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO categories (
                    category_id, name,
                    de_name, en_name, es_name, fr_name,
                    ja_name, ko_name, ru_name, zh_name,
                    icon_filename, iconID, published
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表

    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO categories (
                category_id, name,
                de_name, en_name, es_name, fr_name,
                ja_name, ko_name, ru_name, zh_name,
                icon_filename, iconID, published
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)
