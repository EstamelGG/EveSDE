import os
import shutil
import sqlite3
from categories_handler import read_yaml as read_categories_yaml, process_data as process_categories_data
from groups_handler import read_yaml as read_groups_yaml, process_data as process_groups_data
from types_handler import read_yaml as read_types_yaml, process_data as process_types_data
from iconIDs_handler import read_yaml as read_iconIDs_yaml, process_data as process_iconIDs_data
from metaGroups_handler import read_yaml as read_metaGroups_yaml, process_data as process_metaGroups_data
from dogmaAttributes_handler import read_yaml as read_dogmaAttributes_yaml, process_data as process_dogmaAttributes_data
from dogmaAttributeCategories_handler import read_yaml as read_dogmaAttributeCategories_yaml, process_data as process_dogmaAttributeCategories_data
from typeDogma_handler import read_yaml as read_typeDogma_yaml, process_data as process_typeDogma_data
import image_extra

# 文件路径
categories_yaml_file_path = 'Data/sde/fsd/categories.yaml'
groups_yaml_file_path = 'Data/sde/fsd/groups.yaml'
iconIDs_yaml_file_path = 'Data/sde/fsd/iconIDs.yaml'
types_yaml_file_path = 'Data/sde/fsd/types.yaml'
metaGroups_yaml_file_path = 'Data/sde/fsd/metaGroups.yaml'
dogmaAttributes_yaml_file_path = 'Data/sde/fsd/dogmaAttributes.yaml'
dogmaAttributeCategories_yaml_file_path = 'Data/sde/fsd/dogmaAttributeCategories.yaml'
typeDogma_yaml_file_path = 'Data/sde/fsd/typeDogma.yaml'

# 输出数据库文件的目录
output_dir = 'output/db'
os.makedirs(output_dir, exist_ok=True)

# 语言列表
languages = ['en', 'de', 'es', 'fr', 'ja', 'ko', 'ru', 'zh'] # en 务必在第一个否则有些功能可能会有缺失


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
    print("\nProcessing iconIDs.yaml...")  # 图标ID与文件路径
    process_yaml_file(iconIDs_yaml_file_path, read_iconIDs_yaml, process_iconIDs_data)

    print("\nProcessing categories.yaml...") # 物品目录
    process_yaml_file(categories_yaml_file_path, read_categories_yaml, process_categories_data)

    print("\nProcessing groups.yaml...") # 物品组
    process_yaml_file(groups_yaml_file_path, read_groups_yaml, process_groups_data)

    print("\nProcessing metaGroups.yaml...") # 物品衍生组
    process_yaml_file(metaGroups_yaml_file_path, read_metaGroups_yaml, process_metaGroups_data)

    print("\nProcessing dogmaAttributeCategories.yaml...") # 物品属性目录
    process_yaml_file(dogmaAttributeCategories_yaml_file_path, read_dogmaAttributeCategories_yaml,
                      process_dogmaAttributeCategories_data)

    print("\nProcessing dogmaAttributes.yaml...") # 物品属性名称
    process_yaml_file(dogmaAttributes_yaml_file_path, read_dogmaAttributes_yaml, process_dogmaAttributes_data)

    print("\nProcessing typeDogma.yaml...") # 物品属性详情
    process_yaml_file(typeDogma_yaml_file_path, read_typeDogma_yaml, process_typeDogma_data)

    print("\nProcessing types.yaml...") # 物品详情
    process_yaml_file(types_yaml_file_path, read_types_yaml, process_types_data)

    # 调用脚本以复制Render图像
    # print("\nProcessing images for types...")
    image_extra.main()  # 调用新的脚本处理图片

    print("\n所有数据库已更新。")


if __name__ == "__main__":
    main()