import sqlite3
import re

def is_contains_chinese(text):
    if text is None or len(str(text).strip()) == 0:
        return True
    # 使用正则表达式检查是否包含中文字符
    text = str(text).replace("\r", "").replace("\n", "")
    return bool(re.search('[\u4e00-\u9fff]', text))

def main():
    # 连接到SQLite数据库
    db_path = '/Users/gg/Documents/GitHub/EVE-Nexus/EVE Nexus/utils/SQLite/item_db_zh.sqlite'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 执行查询
    cursor.execute("SELECT type_id, name, description FROM types WHERE published IS TRUE")
    results = cursor.fetchall()

    # 检查结果
    non_chinese_items = []
    for type_id, name, description in results:
        if not is_contains_chinese(name) or not is_contains_chinese(description):
            non_chinese_items.append({
                'type_id': type_id,
                'name': name,
                'description': description
            })

    # 打印结果
    print(f"找到 {len(non_chinese_items)} 个可能缺少中文的条目：")
    for item in non_chinese_items:
        print(f"\nType ID: {item['type_id']}")
        print(f"Name: {item['name']}")
        print(f"Description: {item['description']}")

    conn.close()

if __name__ == "__main__":
    main() 