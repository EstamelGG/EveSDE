import os
import shutil
import sys

# 定义源目录和目标目录
source_root = "Data/Icons"
destination_root = "output/Icons"

if not os.path.exists(source_root):
    print(f"Error: Icon source directory '{source_root}' does not exist.")
    sys.exit(1)

def normalize_filename(path):
    """
    根据给定的路径生成新的文件名，
    按相对于根目录的路径用下划线连接。
    """
    relative_path = os.path.relpath(path, source_root)
    parts = relative_path.split(os.sep)
    normalized_name = "_".join(parts)
    return normalized_name

def copy_and_rename_png_files():
    """
    遍历源目录及其子目录，将所有大于 0 字节的 PNG 文件
    复制到目标目录，并重命名。
    """
    for root, _, files in os.walk(source_root):
        for file in files:
            if file.lower().endswith(".png"):
                source_file = os.path.join(root, file)
                # 检查文件大小是否大于 0 字节
                if os.path.getsize(source_file) > 0:
                    # 生成新的文件名
                    new_filename = normalize_filename(source_file).lower()
                    destination_file = os.path.join(destination_root, new_filename)
                    # 复制文件到目标目录
                    shutil.copy2(source_file, destination_file)
                    # print(f"Copied and renamed: {source_file} -> {destination_file}")