from ruamel.yaml import YAML
import sqlite3
import json
import time

# 用于处理物品属性信息
# 提取出各属性id对应的名称

yaml = YAML(typ='safe')

def read_yaml(file_path):
    """读取 dogmaAttributes.yaml 文件"""
    start_time = time.time()
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.load(file)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return data


def create_dogma_attributes_table(cursor):
    """创建精简版 dogmaAttributes 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dogmaAttributes (
            attribute_id INTEGER NOT NULL PRIMARY KEY,
            categoryID INTEGER,
            name TEXT,
            display_name TEXT,
            tooltipDescription TEXT,
            iconID INTEGER,
            icon_filename TEXT,
            unitID INTEGER,
            unitName TEXT,
            highIsGood BOOLEAN,
            defaultValue REAL,
            stackable BOOLEAN
        )
    ''')


def extract_display_names_from_file(file_path):
    # 从文件中读取JSON内容
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)  # 使用json.load直接从文件读取并解析JSON
        except json.JSONDecodeError as e:
            raise ValueError(f"无效的JSON格式: {e}")

    # 创建一个字典来存储结果
    result = {}

    # 遍历每个条目，提取key和displayName
    for key, value in data.items():
        result[key] = value.get("displayName", None)

    return result


def format_number(value):
    # 判断输入变量是否是数字
    if not isinstance(value, (int, float)):
        raise ValueError("输入的值必须是数字")

    # 如果是int类型，直接返回
    if isinstance(value, int):
        return f"{value:,}"

    # 如果是float类型，保留3位小数，且末尾不为零
    formatted_value = f"{value:,.3f}".rstrip('0').rstrip('.')

    return formatted_value


def process_data(data, cursor, lang):
    """处理 dogmaAttributes 数据并插入数据库（针对单一语言）"""
    create_dogma_attributes_table(cursor)
    unitDict = extract_display_names_from_file("thirdparty_data_source/dogmaunits.json")

    unitName_map = {
        "140": {
            "zh": "等级"
        },
        "120": {
            "zh": "点"
        },
        "136": {
            "zh": "槽位"
        },
        "138": {
            "zh": "单位"
        },
        "141": {
            "zh": "挂点"
        }
    }

    # 用于存储批量插入的数据
    batch_data = []
    batch_size = 1000  # 每批处理的记录数
    
    for attr_id, attr_data in data.items():
        attributeID = attr_data.get('attributeID')
        unitID = attr_data.get("unitID", None)
        unitName = None
        if unitID != None and str(unitID) in unitDict.keys():
            unitName = unitDict[str(unitID)]
        if str(unitID) in unitName_map.keys():
            if lang in unitName_map[str(unitID)]:
                unitName = unitName_map[str(unitID)][lang]
        # 多语言字段
        displayName = attr_data.get('displayNameID', {}).get(lang, None)
        name = attr_data.get('name', None)
        iconID = attr_data.get('iconID', 0)
        defaultValue = attr_data.get('defaultValue', None)
        
        # 获取图标文件名
        icon_filename = None
        if iconID:
            cursor.execute('SELECT iconFile_new FROM iconIDs WHERE icon_id = ?', (iconID,))
            result = cursor.fetchone()
            if result:
                icon_filename = result[0]
        
        categoryID = attr_data.get('categoryID', 0)
        tooltipDescription = attr_data.get('tooltipDescriptionID', {}).get(lang, None)
        highIsGood = attr_data.get('highIsGood', None)
        # 获取stackable字段
        stackable = attr_data.get('stackable', None)

        # 添加到批处理列表
        batch_data.append((
            attributeID, categoryID, name, displayName,
            tooltipDescription, iconID, icon_filename, unitID, unitName, highIsGood, defaultValue, stackable
        ))
        
        # 当达到批处理大小时执行插入
        if len(batch_data) >= batch_size:
            cursor.executemany('''
                INSERT OR REPLACE INTO dogmaAttributes (
                    attribute_id, categoryID, name, display_name, 
                    tooltipDescription, iconID, icon_filename, unitID, unitName, highIsGood, defaultValue, stackable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch_data)
            batch_data = []  # 清空批处理列表
    
    # 处理剩余的数据
    if batch_data:
        cursor.executemany('''
            INSERT OR REPLACE INTO dogmaAttributes (
                attribute_id, categoryID, name, display_name, 
                tooltipDescription, iconID, icon_filename, unitID, unitName, highIsGood, defaultValue, stackable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', batch_data)