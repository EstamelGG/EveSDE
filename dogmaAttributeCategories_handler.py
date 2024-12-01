from ruamel.yaml import YAML
import sqlite3
import time

yaml = YAML(typ='safe')

# 处理属性的目录类型，用于分类展示不同属性

def read_yaml(file_path):
    """读取 dogmaAttributeCategories.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = {}
        for part in yaml.load_all(file):
            data.update(part)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data


def create_dogma_attribute_categories_table(cursor):
    """创建 dogmaAttributeCategories 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaAttributeCategories (
            attribute_category_id INTEGER NOT NULL PRIMARY KEY,
            name TEXT,
            description TEXT
        )
    ''')


def process_data(data, cursor, lang):
    """处理 dogmaAttributeCategories 数据并插入数据库（针对单一语言）"""
    create_dogma_attribute_categories_table(cursor)

    language_map = {
        "Fitting": {
            "zh": "装配"
        },
        "Shield": {
            "zh": "护盾"
        },
        "Armor": {
            "zh": "装甲"
        },
        "Structure": {
            "zh": "结构"
        },
        "Capacitor": {
            "zh": "电容"
        },
        "Targeting": {
            "zh": "目标锁定"
        },
        "Miscellaneous": {
            "zh": "杂项"
        },
        "Required Skills": {
            "zh": "所需技能"
        },
        "Drones": {
            "zh": "无人机"
        },
        "AI": {
            "zh": "AI"
        },
        "Speed and Travel": {
            "zh": "速度与旅行"
        },
        "Loot": {
            "zh": "战利品"
        },
        "Remote Assistance": {
            "zh": "远程协助"
        },
        "EW - Target Painting": {
            "zh": "电子战-目标标记"
        },
        "EW - Energy Neutralizing": {
            "zh": "电子战-能量中和"
        },
        "EW - Remote Electronic Counter Measures": {
            "zh": "电子战-电子干扰"
        },
        "EW - Sensor Dampening": {
            "zh": "电子战-感应抑阻"
        },
        "EW - Target Jamming": {
            "zh": "电子战-锁定干扰"
        },
        "EW - Tracking Disruption": {
            "zh": "电子战-索敌扰断"
        },
        "EW - Warp Scrambling": {
            "zh": "电子战-跃迁扰断"
        },
        "EW - Webbing": {
            "zh": "电子战-停滞网"
        },
        "Turrets": {
            "zh": "炮塔"
        },
        "Missile": {
            "zh": "导弹"
        },
        "Graphics": {
            "zh": "图形"
        },
        "Entity Rewards": {
            "zh": "赏金"
        },
        "Entity Extra Attributes": {
            "zh": "附加属性"
        },
        "Fighter Abilities": {
            "zh": "舰载机能力"
        },
        "EW - Resistance": {
            "zh": "电子战抗性"
        },
        "Bonuses": {
            "zh": "加成"
        },
        "Fighter Attributes": {
            "zh": "舰载机属性"
        },
        "Superweapons": {
            "zh": "超级武器"
        },
        "Hangars & Bays": {
            "zh": "船舱"
        },
        "On Death": {
            "zh": "死亡时"
        },
        "Behavior Attributes": {
            "zh": "行为属性"
        },
        "Mining": {
            "zh": "采矿"
        },
        "Heat": {
            "zh": "超载"
        }
    }

    for category_id, category_data in data.items():
        # 获取字段
        name = category_data.get('name', "")
        description = category_data.get('description', "")
        if name in language_map.keys():
            if lang in language_map[name]:
                name = language_map[name][lang]
        # 插入数据
        cursor.execute('''
            INSERT OR REPLACE INTO dogmaAttributeCategories (
                attribute_category_id, name, description
            ) VALUES (?, ?, ?)
        ''', (category_id, name, description))