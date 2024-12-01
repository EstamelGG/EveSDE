import os
import sqlite3
from categories_handler import read_yaml as read_categories_yaml, process_data as process_categories_data
from groups_handler import read_yaml as read_groups_yaml, process_data as process_groups_data
from types_handler import read_yaml as read_types_yaml, process_data as process_types_data
from iconIDs_handler import read_yaml as read_iconIDs_yaml, process_data as process_iconIDs_data
import image_extra

# 文件路径
categories_yaml_file_path = 'Data/sde/fsd/categories.yaml'
groups_yaml_file_path = 'Data/sde/fsd/groups.yaml'
types_yaml_file_path = 'Data/sde/fsd/types.yaml'
iconIDs_yaml_file_path = 'Data/sde/fsd/iconIDs.yaml'

# 输出数据库文件的目录
output_dir = 'output/db'
os.makedirs(output_dir, exist_ok=True)

# 语言列表
languages = ['de', 'en', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']


def process_yaml_file(yaml_file_path, read_func, process_func):
    """处理每个 YAML 文件并更新所有语言的数据库"""
    # 读取 YAML 数据一次
    data = read_func(yaml_file_path)

    for lang in languages:
        db_filename = os.path.join(output_dir, f'item_db_{lang}.sqlite')

        # 连接数据库
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 针对单一语言处理数据
        process_func(data, cursor, lang)

        # 提交事务并关闭连接
        conn.commit()
        conn.close()

        print(f"Database {db_filename} has been updated for language: {lang}.")


def main():
    # 依次处理每个 YAML 文件
    print("\nProcessing categories.yaml...")
    process_yaml_file(categories_yaml_file_path, read_categories_yaml, process_categories_data)

    print("\nProcessing groups.yaml...")
    process_yaml_file(groups_yaml_file_path, read_groups_yaml, process_groups_data)

    print("\nProcessing types.yaml...")
    process_yaml_file(types_yaml_file_path, read_types_yaml, process_types_data)

    #print("\nProcessing iconIDs.yaml...")
    #process_yaml_file(iconIDs_yaml_file_path, read_iconIDs_yaml, process_iconIDs_data)

    # 调用新脚本以复制图像
    print("\nProcessing images for types...")
    image_extra.main()  # 调用新的脚本处理图片

    print("\n所有数据库已更新。")


if __name__ == "__main__":
    main()