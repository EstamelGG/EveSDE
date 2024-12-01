import sqlite3
import os
import shutil
from tqdm import tqdm  # 导入 tqdm 用于显示进度条
import random  # 导入 random 用于随机选择缺失的 type_id


def get_all_type_ids(db_filename):
    """从数据库中获取所有 type_id"""
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # 获取 types 表中的所有 type_id
    cursor.execute("SELECT type_id FROM types")
    type_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return type_ids


def copy_images(type_ids, types_image_dir, output_image_dir):
    """根据 type_id 查找对应图片并复制到目标目录"""
    os.makedirs(output_image_dir, exist_ok=True)

    # 记录复制成功的文件数和未找到的文件数
    copied_files = 0
    missed_files = 0
    missed_type_ids = []  # 用于记录缺失图片的 type_id

    # 使用 tqdm 显示进度条
    for type_id in tqdm(type_ids, desc="Copying images", unit="type_id"):
        # 生成图片文件名，例如 "123_32.png" 或 "123_64.png"
        for size in [32, 64]:
            image_filename = f"{type_id}_{size}.png"
            source_path = os.path.join(types_image_dir, image_filename)

            # 检查图片是否存在
            if os.path.exists(source_path):
                # 复制文件到目标目录
                shutil.copy(source_path, os.path.join(output_image_dir, image_filename))
                copied_files += 1
            else:
                if type_id not in missed_type_ids:
                    missed_type_ids.append(type_id)
                missed_files += 1

    # 打印最终结果
    print(f"\nFinished copying images.")
    print(f"Copied {copied_files} files.")
    print(f"Missed {missed_files} files due to missing icons in Types directory.")

    # 如果缺失文件超过 20 个，随机选择 20 个缺失的 type_id 打印出来
    if missed_type_ids:
        print("\n10 random missed image type_ids:")
        random_missed_ids = random.sample(missed_type_ids, min(20, len(missed_type_ids)))
        for missed_id in random_missed_ids:
            print(missed_id)


def main():
    """处理所有图片：从数据库提取 type_id 并复制图片"""
    db_filename = 'output/db/item_db_en.sqlite'
    types_image_dir = 'Data/Types'
    output_image_dir = 'output/images'

    # 获取数据库中的所有 type_id
    type_ids = get_all_type_ids(db_filename)

    # 复制对应的图片
    copy_images(type_ids, types_image_dir, output_image_dir)


if __name__ == "__main__":
    main()