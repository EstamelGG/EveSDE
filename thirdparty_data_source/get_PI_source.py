import sqlite3
import json
import requests
import time

# 获取行星原材料的采集源

def get_planet_resource_types(db_path):
    """从数据库获取行星资源类型ID"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT type_id FROM types WHERE categoryID = 42')
    type_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return type_ids


def fetch_resource_data(type_id):
    """从everef获取资源数据"""
    url = f"https://ref-data.everef.net/types/{type_id}"

    try:
        # 添加请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 解析JSON数据
        data = response.json()
        harvested_by = data.get('harvested_by_pin_type_ids', [])

        return harvested_by

    except Exception as e:
        print(f"获取type_id {type_id}的数据时出错: {str(e)}")
        return None


def main():
    # 数据库路径
    db_path = 'output/db/item_db_en.sqlite'

    # 获取所有行星资源type_id
    print("正在从数据库获取行星资源类型...")
    type_ids = get_planet_resource_types(db_path)
    print(f"找到 {len(type_ids)} 个行星资源类型")

    # 存储结果的字典
    result_data = {}

    # 获取每个资源的数据
    print("开始获取资源数据...")
    for i, type_id in enumerate(type_ids, 1):
        print(f"正在处理 {i}/{len(type_ids)}: type_id {type_id}")
        harvested_by = fetch_resource_data(type_id)

        if harvested_by is not None:
            result_data[type_id] = harvested_by

        # 添加延时，避免请求过于频繁
        time.sleep(1)

    # 将结果保存到JSON文件
    output_file = './planet_resource_harvesters.json'
    print(f"\n正在保存数据到 {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print("数据获取和保存完成！")


if __name__ == "__main__":
    main()