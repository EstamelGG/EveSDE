import os
from PIL import Image
import json
from tqdm import tqdm


def create_sprite_sheet_from_folder(folder_path, output_image, output_json, max_width=10, padding=5):
    """
    创建一个图集，将指定文件夹中的所有图片打包到一个大图中，同时生成索引文件，并显示进度条。

    :param folder_path: 包含图片的文件夹路径
    :param output_image: 输出图集的路径
    :param output_json: 输出 JSON 索引的路径
    :param max_width: 每行的最大图片数量
    :param padding: 图片之间的间距
    """
    # 获取文件夹内所有图片文件
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    image_files.sort()  # 按文件名排序

    if not image_files:
        raise ValueError("文件夹中没有找到图片文件")

    images = []
    valid_files = []

    # 加载所有合法图片并显示进度条
    print("加载图片中...")
    for file_name in tqdm(image_files, desc="加载图片", unit="张"):
        file_path = os.path.join(folder_path, file_name)
        try:
            img = Image.open(file_path)
            img.verify()  # 验证图片合法性
            img = Image.open(file_path)  # 重新打开以实际使用
            images.append(img)
            valid_files.append(file_name)
        except (IOError, SyntaxError) as e:
            print(f"跳过无效图片: {file_name}，原因: {e}")

    if not images:
        raise ValueError("没有找到合法的图片文件")

    max_image_width = max(image.width for image in images)
    max_image_height = max(image.height for image in images)

    # 图集宽度和高度
    total_width = (max_image_width + padding) * min(max_width, len(images)) - padding
    rows = (len(images) + max_width - 1) // max_width
    total_height = (max_image_height + padding) * rows - padding

    # 创建空白图集
    sprite_sheet = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    index = {}

    # 填充图集并显示进度条
    print("生成图集中...")
    x_offset, y_offset = 0, 0
    for img, file_name in tqdm(zip(images, valid_files), desc="生成图集", total=len(images), unit="张"):
        sprite_sheet.paste(img, (x_offset, y_offset))
        index[file_name] = {
            "x": x_offset,
            "y": y_offset,
            "width": img.width,
            "height": img.height,
        }

        # 删除原始图片
        img.close()
        os.remove(os.path.join(folder_path, file_name))

        # 更新偏移
        x_offset += max_image_width + padding
        if x_offset + max_image_width > total_width:
            x_offset = 0
            y_offset += max_image_height + padding

    # 保存图集和索引
    sprite_sheet.save(output_image)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=4)

    print(f"图集已保存到 {output_image}")
    print(f"索引文件已保存到 {output_json}")