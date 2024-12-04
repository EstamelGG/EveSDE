import os
import shutil
import sqlite3
import zipfile
from categories_handler import read_yaml as read_categories_yaml, process_data as process_categories_data
from groups_handler import read_yaml as read_groups_yaml, process_data as process_groups_data
from types_handler import read_yaml as read_types_yaml, process_data as process_types_data
from iconIDs_handler import read_yaml as read_iconIDs_yaml, process_data as process_iconIDs_data
from metaGroups_handler import read_yaml as read_metaGroups_yaml, process_data as process_metaGroups_data
from dogmaAttributes_handler import read_yaml as read_dogmaAttributes_yaml, process_data as process_dogmaAttributes_data
from dogmaAttributeCategories_handler import read_yaml as read_dogmaAttributeCategories_yaml, \
    process_data as process_dogmaAttributeCategories_data
from typeDogma_handler import read_yaml as read_typeDogma_yaml, process_data as process_typeDogma_data
from icons_copy import copy_and_rename_png_files
from update_catelogy_icons import update_groups_with_icon_filename

# 文件路径
categories_yaml_file_path = 'Data/sde/fsd/categories.yaml'
groups_yaml_file_path = 'Data/sde/fsd/groups.yaml'
iconIDs_yaml_file_path = 'Data/sde/fsd/iconIDs.yaml'
types_yaml_file_path = 'Data/sde/fsd/types.yaml'
metaGroups_yaml_file_path = 'Data/sde/fsd/metaGroups.yaml'
dogmaAttributes_yaml_file_path = 'Data/sde/fsd/dogmaAttributes.yaml'
dogmaAttributeCategories_yaml_file_path = 'Data/sde/fsd/dogmaAttributeCategories.yaml'
typeDogma_yaml_file_path = 'Data/sde/fsd/typeDogma.yaml'
ZIP_ICONS_DEST = 'output/Icons/icons.zip'
ICONS_DEST_DIR = 'output/Icons'

# 语言列表
languages = ['en', 'de', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']  # en 务必在第一个否则有些功能可能会有缺失

output_db_dir = 'output/db'
output_icons_dir = 'output/Icons'


def rebuild_directory(directory_path):
    """
    删除指定目录中的所有文件和子目录，但保留目录本身。
    :param directory_path: 要清理的目录路径
    """
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return

    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)  # 删除文件或符号链接
            print(f"Deleted file: {item_path}")
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)  # 删除子目录及其内容
            print(f"Deleted directory: {item_path}")
    # 输出数据库文件的目录
    os.makedirs(output_db_dir, exist_ok=True)
    os.makedirs(output_icons_dir, exist_ok=True)


def zip_icons():
    # 检查 ZIP 文件是否已经存在
    if os.path.exists(ZIP_ICONS_DEST):
        return  # 如果文件存在，跳过压缩
    # 创建一个 ZIP 文件
    with zipfile.ZipFile(ZIP_ICONS_DEST, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历指定目录下的文件
        for filename in os.listdir(ICONS_DEST_DIR):
            file_path = os.path.join(ICONS_DEST_DIR, filename)
            # 确保处理的是文件而不是子目录，只压缩 png 文件
            if os.path.isfile(file_path) and file_path.endswith(".png"):
                try:
                    # 将文件添加到 ZIP 压缩包中
                    zipf.write(file_path, os.path.basename(file_path))  # 压缩文件并保留文件名
                    # 文件压缩成功后删除源文件
                    os.remove(file_path)
                    # print(f"已成功压缩并删除文件: {filename}")
                except Exception as e:
                    print(f"压缩文件 {filename} 时发生错误: {e}")
    print(f"所有文件已成功压缩到 {ZIP_ICONS_DEST}")


def process_yaml_file(yaml_file_path, read_func, process_func):
    """处理每个 YAML 文件并更新所有语言的数据库"""
    # 读取 YAML 数据一次
    data = read_func(yaml_file_path)

    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')

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
    rebuild_directory("./output")
    # 依次处理每个 YAML 文件
    copy_and_rename_png_files()
    print("\nProcessing iconIDs.yaml...")  # 图标ID与文件路径
    process_yaml_file(iconIDs_yaml_file_path, read_iconIDs_yaml, process_iconIDs_data)

    print("\nProcessing categories.yaml...")  # 物品目录
    process_yaml_file(categories_yaml_file_path, read_categories_yaml, process_categories_data)

    print("\nProcessing groups.yaml...")  # 物品组
    process_yaml_file(groups_yaml_file_path, read_groups_yaml, process_groups_data)

    print("\nProcessing metaGroups.yaml...")  # 物品衍生组
    process_yaml_file(metaGroups_yaml_file_path, read_metaGroups_yaml, process_metaGroups_data)

    print("\nProcessing dogmaAttributeCategories.yaml...")  # 物品属性目录
    process_yaml_file(dogmaAttributeCategories_yaml_file_path, read_dogmaAttributeCategories_yaml,
                      process_dogmaAttributeCategories_data)

    print("\nProcessing dogmaAttributes.yaml...")  # 物品属性名称
    process_yaml_file(dogmaAttributes_yaml_file_path, read_dogmaAttributes_yaml, process_dogmaAttributes_data)

    print("\nProcessing typeDogma.yaml...")  # 物品属性详情
    process_yaml_file(typeDogma_yaml_file_path, read_typeDogma_yaml, process_typeDogma_data)

    print("\nProcessing types.yaml...")  # 物品详情
    process_yaml_file(types_yaml_file_path, read_types_yaml, process_types_data)

    print("\nUpdating groups...") # 给 groups 更新图标名称
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        update_groups_with_icon_filename(db_filename)

    zip_icons()
    print("\n所有数据库已更新。")


if __name__ == "__main__":
    main()
