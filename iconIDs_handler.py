import zipfile
from ruamel.yaml import YAML
import os

yaml = YAML(typ='safe')

# 定义源和目标目录
ICONS_SOURCE_DIR = 'Data/Icons/items'
ICONS_DEST_DIR = 'output/Icons'
ZIP_ICONS_DEST = 'output/Icons/icons.zip'

# 图标目录与实际目录的局部映射
# key是yaml中的关键词，value是实际映射的文件的开头
icon_path_map = {
    "/ui/texture/icons/": "items",
    "/ui/texture/corps/": "corporations"
}

def read_yaml(file_path):
    """读取 iconIDs.yaml 文件并返回数据"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.load(file)


def ensure_icons_directory_exists(directory):
    """检查并确保目标目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def copy_and_rename_icons(icon_data):
    """整理图像文件并创建文件名映射字典"""
    icon_filename_mapping = {}  # icon_id -> new_icon_file
    raw_icon_filename_mapping = {}
    ensure_icons_directory_exists(ICONS_DEST_DIR)  # 确保目标目录存在

    for icon_id, details in icon_data.items():
        icon_file = details.get('iconFile', "")
        raw_icon_filename_mapping[icon_id] = icon_file
        dest_icon_filename = "items_73_16_50.png"
        # 判断 iconFile 是否包含 "/icons/" 等目录, 其他筛选条件后续再加
        for key in icon_path_map:
            if key.lower() in icon_file.lower():
                icon_filename = str(icon_file).split("/")[-1]
                dest_icon_filename = f"{icon_path_map[key]}_{icon_filename}".lower()
                break
        dest_file_path = os.path.join(ICONS_DEST_DIR, dest_icon_filename)
        if not os.path.exists(dest_file_path):
            dest_icon_filename = "items_73_16_50.png"
        dest_icon_filename_fix = dest_icon_filename.split(".")[0] # 只留文件名
        icon_filename_mapping[icon_id] = dest_icon_filename_fix
    return raw_icon_filename_mapping, icon_filename_mapping


def create_iconIDs_table(cursor):
    """创建 iconIDs 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS iconIDs (
            icon_id INTEGER PRIMARY KEY,
            description TEXT,
            iconFile TEXT,
            renamedIcon TEXT
        )
    ''')


def insert_iconIDs(cursor, icon_data, raw_icon_filename_mapping, icon_filename_mapping):
    """将整理好的 iconIDs 数据插入到数据库"""
    for icon_id, details in icon_data.items():
        description = details.get('description', "")

        # 获取新的 iconFile（如果有映射的话）
        new_icon_file = icon_filename_mapping.get(icon_id, details.get('iconFile', "item_73_16_50"))
        old_icon_file = raw_icon_filename_mapping.get(icon_id, details.get('iconFile', ""))

        # 插入或替换数据
        cursor.execute('''
            INSERT OR REPLACE INTO iconIDs (icon_id, description, iconFile, renamedIcon)
            VALUES (?, ?, ?, ?)
        ''', (icon_id, description, old_icon_file, new_icon_file))


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

def process_data(icon_data, cursor, lang):
    """处理 iconIDs 数据并插入数据库"""
    # 处理并复制文件，获取文件名映射
    raw_icon_filename_mapping, icon_filename_mapping = copy_and_rename_icons(icon_data)

    # 插入数据库（使用新文件名）
    create_iconIDs_table(cursor)
    insert_iconIDs(cursor, icon_data, raw_icon_filename_mapping, icon_filename_mapping)
    zip_icons()