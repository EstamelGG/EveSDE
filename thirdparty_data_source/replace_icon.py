import os
import shutil
from PIL import Image


def get_file_size(image_path):
    """获取图片文件的尺寸（字节数）"""
    return os.path.getsize(image_path)


def copy_icons():
    # 定义源目录和目标目录
    source_dir = "./icon_from_api"
    target_dir = "../Data/Types"

    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 获取源目录中的所有文件
    if not os.path.exists(source_dir):
        print(f"源目录 {source_dir} 不存在！")
        return

    files = os.listdir(source_dir)
    total_files = len(files)
    copied = 0
    replaced = 0

    print(f"开始处理 {total_files} 个文件...")

    for i, filename in enumerate(files, 1):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)

        print(f"处理第 {i}/{total_files} 个文件: {filename}", end='')

        # 如果目标文件不存在，直接复制
        if not os.path.exists(target_path):
            shutil.copy2(source_path, target_path)
            copied += 1
            print(" - 已复制")
            continue
        shutil.copy2(source_path, target_path)
        source_size = get_file_size(source_path)
        target_size = get_file_size(target_path)
        print(f" - 已替换 (新文件: {source_size}字节, 原文件: {target_size}字节)")

    print("\n处理完成！")
    print(f"新复制: {copied} 个文件")
    print(f"已替换: {replaced} 个文件")


if __name__ == "__main__":
    copy_icons()