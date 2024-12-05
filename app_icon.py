from PIL import Image

# 输入图片路径
input_image_path = "raw_icon/Appicon1024x1024.png"

# 输出图片路径模板
output_image_path_template = "raw_icon/Appicon{size}x{size}.png"

# 目标尺寸列表
sizes = [512, 256, 128, 64, 32, 16]

# 打开原始图片
try:
    with Image.open(input_image_path) as img:
        # 确保图片为正方形
        if img.width != img.height:
            raise ValueError("The input image must be square (e.g., 1024x1024).")

        # 遍历尺寸并保存每个缩放后的图片
        for size in sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            resized_img.save(output_image_path_template.format(size=size))
            print(f"Saved resized image: {output_image_path_template.format(size=size)}")
except Exception as e:
    print(f"Error: {e}")