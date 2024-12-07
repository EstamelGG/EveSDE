import os
import shutil
import sqlite3
import zipfile
import tarfile
import gzip
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
from update_groups_icons import update_groups_with_icon_filename

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


def create_uncompressed_icons_tar(source_dir, zip_path):
    """
    创建一个tar.gz文件，用于存储图标
    使用gzip压缩，保持与原函数相同的参数和删除逻辑

    Args:
        source_dir: 源图标目录路径
        zip_path: 目标文件路径（会自动将.zip替换为.tar.gz）
    """
    # 将输出路径从.zip改为.tar.gz
    tar_path = zip_path.replace('.zip', '.tar.gz')

    # 如果文件已存在，先删除
    if os.path.exists(tar_path):
        os.remove(tar_path)
        print(f"已删除现有文件: {tar_path}")

    # 创建tar.gz文件
    with tarfile.open(tar_path, 'w:gz') as tarf:
        # 遍历指定目录下的文件
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            # 确保处理的是PNG文件
            if os.path.isfile(file_path) and filename.lower().endswith(".png"):
                try:
                    # 将文件添加到tar中
                    tarf.add(file_path, arcname=filename)  # 只保留文件名，不包含路径
                    os.remove(file_path)
                except Exception as e:
                    print(f"处理文件 {filename} 时发生错误: {e}")

    # 显示文件大小
    tar_size = os.path.getsize(tar_path) / (1024 * 1024)  # 转换为MB
    print(f"\n文件创建完成: {tar_path}")
    print(f"文件大小: {tar_size:.2f}MB")

def create_uncompressed_icons_zip(source_dir, zip_path):
    """
    创建一个无压缩的ZIP文件，用于存储图标

    Args:
        source_dir: 源图标目录路径
        zip_path: 目标ZIP文件路径
    """
    # 如果ZIP文件已存在，先删除
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"已删除现有ZIP文件: {zip_path}")

    # 创建一个无压缩的ZIP文件
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as zipf:
        # 遍历指定目录下的文件
        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)
            # 确保处理的是PNG文件
            if os.path.isfile(file_path) and filename.lower().endswith(".png"):
                try:
                    # 将文件添加到ZIP中，不使用压缩
                    zipf.write(file_path, filename)  # 只保留文件名，不包含路径
                    os.remove(file_path)
                except Exception as e:
                    print(f"处理文件 {filename} 时发生错误: {e}")

    # 显示ZIP文件大小
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # 转换为MB
    print(f"\nZIP文件创建完成: {zip_path}")
    print(f"文件大小: {zip_size:.2f}MB")

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
    print("\n")
    # create_uncompressed_icons_zip(ICONS_DEST_DIR, ZIP_ICONS_DEST)
    create_uncompressed_icons_tar(ICONS_DEST_DIR, ZIP_ICONS_DEST)
    print("\n所有数据库已更新。")


if __name__ == "__main__":
    main()
