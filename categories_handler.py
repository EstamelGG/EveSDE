from ruamel.yaml import YAML
import os

yaml = YAML(typ='safe')

# 提取所有目录信息

categories_id_icon_map = {
    0: "items_7_64_4.png",
    1: "items_70_128_11.png",
    2: "items_30_64_4.png",
    3: "items_27_64_16.png",
    4: "icon_34_64.png",
    5: "icon_44992_64.png",
    6: "items_26_64_2.png",
    7: "items_2_64_11.png",
    8: "items_5_64_2.png",
    9: "icon_1002_64.png",
    10: "items_6_64_3.png",
    11: "items_26_64_10.png",
    14: "items_modules_fleetboost_infobase.png",
    16: "icon_3300_64.png",
    17: "items_49_64_1.png",
    18: "icon_2454_64.png",
    20: "items_40_64_16.png",
    22: "icon_33475_64.png",
    23: "icon_12239_64.png",
    24: "items_comprfuel_amarr.png",
    25: "items_inventory_moonasteroid_r4.png",
    30: "items_inventory_cratexvishirt.png",
    32: "items_76_64_7.png",
    34: "items_55_64_15.png",
    35: "items_55_64_11.png",
    39: "items_95_64_6.png",
    40: "icon_32458_64.png",
    41: "icon_2133_64.png",
    42: "items_97_64_10.png",
    43: "items_99_64_8.png",
    46: "icon_2233_64.png",
    63: "icon_19658_64.png",
    65: "icon_40340_64.png",
    66: "icon_35923_64.png",
    87: "icon_23061_64.png",
}


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
            icon_filename TEXT,
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
        dest_icon_filename = categories_id_icon_map.get(item_id, "items_73_16_50.png")
        if not os.path.exists(f"output/Icons/{dest_icon_filename}"):
            dest_icon_filename = "items_73_16_50.png"
        # 使用 INSERT OR REPLACE 语句，当 category_id 已存在时更新记录
        cursor.execute('''
            INSERT OR REPLACE INTO categories (category_id, name, icon_filename, iconID, published)
            VALUES (?, ?, ?, ?, ?)
        ''', (item_id, name, dest_icon_filename, iconID, published))
