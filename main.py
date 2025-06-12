# -*- coding: utf-8 -*-
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
from typeMaterials_handler import read_yaml as read_typeMaterials_yaml, process_data as process_typeMaterials_data
from blueprints_handler import read_yaml as read_blueprints_yaml, process_data as process_blueprints_data
from typeSkillRequirements_handler import process_skill_requirements
from marketGroups_handler import read_yaml as read_marketGroups_yaml, process_data as process_marketGroups_data
from factions_handler import read_yaml as read_factions_yaml, process_data as process_factions_data
from icons_copy import copy_and_rename_png_files
from update_groups_icons import update_groups_with_icon_filename
from planet_schematics_handler import read_yaml as read_planetSchematics_yaml, \
    process_data as process_planetSchematics_data
from stations_handler import read_stations_yaml, process_data as process_stations_data
# from invUniqueNames_handler import read_yaml as read_invUniqueNames_yaml, process_data as process_invUniqueNames_data  # 注释掉旧的导入
from invUniqueNames_handler_new import read_universe_data, process_data as process_invUniqueNames_data  # 新的导入
# from universe import process_data as process_universe_data  # 注释掉旧的导入
from universe_new import process_data as process_universe_data  # 新的导入
from npcCorporations_handler import process_data as process_corporations_data
from npcCorporations_handler import read_yaml as read_corporations_yaml
from invFlags_handler import read_yaml as read_invFlags_yaml, process_data as process_invFlags_data
from invNames_handler import read_yaml as read_invNames_yaml, process_data as process_invNames_data
from agents_handler import read_agents_yaml, read_agents_in_space_yaml, process_agents_data
from divisions_handler import read_divisions_yaml, process_divisions_data
from dynamic_items_handler import process_data as process_dynamic_items_data, fetch_dynamic_items_data
from agent_localization_handler import update_agents_localization  # 导入新的本地化处理函数
from station_name_localization.station_localization_handler import update_stations_localization  # 导入空间站本地化处理函数
from dogmaEffects_handler import read_yaml as read_dogmaEffects_yaml, process_data as process_dogmaEffects_data
from dbuff_collections_handler import read_yaml as read_dbuff_collections_yaml, process_data as process_dbuff_collections_data

# 文件路径
categories_yaml_file_path = 'Data/sde/fsd/categories.yaml'
groups_yaml_file_path = 'Data/sde/fsd/groups.yaml'
iconIDs_yaml_file_path = 'Data/sde/fsd/iconIDs.yaml'
planetSchematics_yaml_file_path = 'Data/sde/fsd/planetSchematics.yaml'
types_yaml_file_path = 'Data/sde/fsd/types.yaml'
metaGroups_yaml_file_path = 'Data/sde/fsd/metaGroups.yaml'
dogmaAttributes_yaml_file_path = 'Data/sde/fsd/dogmaAttributes.yaml'
dogmaAttributeCategories_yaml_file_path = 'Data/sde/fsd/dogmaAttributeCategories.yaml'
typeDogma_yaml_file_path = 'Data/sde/fsd/typeDogma.yaml'
update_typeDogma_yaml_file_path = 'fetchTypes/typeDogma.yaml'
typeMaterials_yaml_file_path = 'Data/sde/fsd/typeMaterials.yaml'
blueprints_yaml_file_path = 'Data/sde/fsd/blueprints.yaml'
marketGroups_yaml_file_path = 'Data/sde/fsd/marketGroups.yaml'
factions_yaml_file_path = 'Data/sde/fsd/factions.yaml'
# invUniqueNames_yaml_file_path = 'Data/sde/bsd/invUniqueNames.yaml'  # 注释掉旧的文件路径
npcCorporations_yaml_file_path = 'Data/sde/fsd/npcCorporations.yaml'
agents_yaml_file_path = 'Data/sde/fsd/agents.yaml'
agents_in_space_yaml_file_path = 'Data/sde/fsd/agentsInSpace.yaml'
divisions_yaml_file_path = 'Data/sde/fsd/npcCorporationDivisions.yaml'
ZIP_ICONS_DEST = 'output/Icons/icons.zip'
arch_ICONS_DEST = 'output/Icons/icons.aar'
ICONS_DEST_DIR = 'output/Icons'
stations_yaml_file_path = 'Data/sde/bsd/staStations.yaml'
invFlags_yaml_file_path = 'Data/sde/bsd/invFlags.yaml'
invNames_yaml_file_path = 'Data/sde/bsd/invNames.yaml'
dogmaEffects_yaml_file_path = 'Data/sde/fsd/dogmaEffects.yaml'
dbuff_collections_yaml_file_path = 'Data/sde/fsd/dbuffCollections.yaml'

# aa archive -o ../icons.aar -d .

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


def clean_unused_icons(source_dir):
    """
    清理未使用的图标文件
    
    Args:
        source_dir: 源图标目录路径
        
    Returns:
        set: 返回所有使用的图标文件名集合
    """
    # 连接数据库获取所有使用的图标文件名
    db_path = os.path.join('output/db', 'item_db_en.sqlite')
    used_icons = set()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查询 marketGroups
        cursor.execute("SELECT icon_name FROM marketGroups WHERE icon_name != ''")
        marketGroups_icons = {row[0] for row in cursor.fetchall()}

        # 查询 groups
        cursor.execute("SELECT icon_filename FROM groups WHERE icon_filename != ''")
        groups_icons = {row[0] for row in cursor.fetchall()}

        # 查询categories
        cursor.execute("SELECT icon_filename FROM categories WHERE icon_filename != ''")
        categories_icons = {row[0] for row in cursor.fetchall()}

        # 查询types表中的icon_filename和bpc_icon_filename
        cursor.execute(
            "SELECT icon_filename FROM types WHERE icon_filename != '' UNION SELECT bpc_icon_filename FROM types WHERE bpc_icon_filename != ''")
        types_icons = {row[0] for row in cursor.fetchall()}

        # 查询dogmaAttributes表中的icon_filename
        cursor.execute("SELECT icon_filename FROM dogmaAttributes WHERE icon_filename != ''")
        dogma_icons = {row[0] for row in cursor.fetchall()}

        # 查询npcCorporations表中的icon_filename
        cursor.execute("SELECT icon_filename FROM npcCorporations WHERE icon_filename != ''")
        corp_icons = {row[0] for row in cursor.fetchall()}

        # 查询factions表中的iconName
        cursor.execute("SELECT iconName FROM factions WHERE iconName != ''")
        factions_icons = {row[0] for row in cursor.fetchall()}

        # 合并所有使用的图标文件名
        used_icons = types_icons.union(marketGroups_icons, groups_icons, dogma_icons, corp_icons, categories_icons,
                                       factions_icons)

        conn.close()
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return set()

    # 统计删除的文件数量
    deleted_count = 0
    total_count = 0

    # 遍历目录下的文件
    for filename in os.listdir(source_dir):
        file_path = os.path.join(source_dir, filename)
        # 确保处理的是PNG文件
        if os.path.isfile(file_path) and filename.lower().endswith(".png"):
            total_count += 1
            try:
                # 如果文件不在使用的图标列表中，则删除
                if filename not in used_icons:
                    os.remove(file_path)
                    print(f"已删除未使用的图标文件: {filename}")
                    deleted_count += 1
            except Exception as e:
                print(f"删除文件 {filename} 时发生错误: {e}")

    print(f"总共检查了 {total_count} 个图标文件，删除了 {deleted_count} 个未使用的图标文件")
    print(f"保留了 {total_count - deleted_count} 个使用的图标文件")
    return used_icons


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

    # 清理未使用的图标文件
    clean_unused_icons(source_dir)

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


def process_special_data(process_func, description, **kwargs):
    """处理特殊数据（不需要读取YAML文件的处理器）"""
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        try:
            if 'lang' in kwargs:
                process_func(cursor, lang)
            else:
                process_func(cursor)
            conn.commit()
        finally:
            conn.close()

        print(f"Database {db_filename} has been updated for {description}.")


def process_universe_names():
    """处理宇宙名称数据"""
    data = read_universe_data()
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        try:
            process_invUniqueNames_data(data, cursor, lang)
            conn.commit()
        finally:
            conn.close()

        print(f"Database {db_filename} has been updated for universe names.")


def process_agents_yaml_files():
    """处理代理相关的YAML文件"""
    # 读取YAML数据
    agents_data = read_agents_yaml(agents_yaml_file_path)
    agents_in_space_data = read_agents_in_space_yaml(agents_in_space_yaml_file_path)

    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        try:
            process_agents_data(agents_data, agents_in_space_data, cursor, lang)
            conn.commit()
        finally:
            conn.close()

        print(f"Database {db_filename} has been updated for agents data.")


def get_file_size(file_path):
    """获取文件大小并返回格式化的字符串"""
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)  # 转换为MB
    return f"{size_mb:.2f}MB"


def compress_database(db_filename):
    """压缩单个数据库文件"""
    try:
        # 获取压缩前的大小
        before_size = os.path.getsize(db_filename) / (1024 * 1024)  # 转换为MB
        print(f"\n压缩数据库: {db_filename}")
        print(f"压缩前大小: {before_size:.2f}MB")

        # 创建zip文件路径
        zip_filename = f"{db_filename}.zip"

        # 如果zip文件已存在，先删除
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
            print(f"已删除现有ZIP文件: {zip_filename}")

        # 创建一个压缩的ZIP文件
        with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            # 将数据库文件添加到ZIP中
            zipf.write(db_filename, os.path.basename(db_filename))
            # 删除原始数据库文件
            os.remove(db_filename)

        # 获取压缩后的大小
        after_size = os.path.getsize(zip_filename) / (1024 * 1024)  # 转换为MB
        print(f"压缩后大小: {after_size:.2f}MB")
        print(f"节省空间: {(before_size - after_size):.2f}MB")

        return before_size - after_size
    except Exception as e:
        print(f"压缩数据库 {db_filename} 时发生错误: {e}")
        return 0


def compress_all_databases():
    """压缩所有语言的数据库"""
    print("\n开始压缩所有数据库...")
    total_saved = 0

    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')
        if os.path.exists(db_filename):
            saved = compress_database(db_filename)
            total_saved += saved

    print(f"\n数据库压缩完成，总共节省空间: {total_saved:.2f}MB")


def drop_icon_ids_table():
    """删除所有数据库中的iconIDs表，因为该表已不再需要"""
    print("\n删除iconIDs表...")

    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')

        try:
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

            # 删除iconIDs表
            cursor.execute('DROP TABLE IF EXISTS iconIDs')

            conn.commit()
            conn.close()

            print(f"已从数据库 {db_filename} 中删除iconIDs表")
        except Exception as e:
            print(f"删除数据库 {db_filename} 中的iconIDs表时发生错误: {e}")


def clean_invnames_table():
    """删除invNames表中itemID不在40,000,000到49,999,999范围内的记录"""
    print("\n清理invNames表...")

    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')

        try:
            conn = sqlite3.connect(db_filename)
            cursor = conn.cursor()

            # 先获取总记录数
            cursor.execute('SELECT COUNT(*) FROM invNames')
            total_records = cursor.fetchone()[0]

            # 删除不在指定范围内的记录
            cursor.execute('DELETE FROM invNames WHERE itemID < 40000000 OR itemID > 49999999')
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            print(
                f"已从数据库 {db_filename} 中删除了 {deleted_count} 条记录，原有 {total_records} 条，剩余 {total_records - deleted_count} 条")
        except Exception as e:
            print(f"清理数据库 {db_filename} 中的invNames表时发生错误: {e}")


def copy_icon_batch():
    """从fetchIcons/icon_fix目录复制修正过的图标到Data/Types目录

    这些图片是已知某些typeid对应的图片存在错误，因此通过手动修正后放在icon_fix目录中
    复制到Data/Types目录后，就能确保在处理时使用正确的图片

    同时处理一些特殊情况：某些图片需要复制为多个不同type_id的文件
    """

    source_dir = "fetchIcons/icon_fix"
    target_dir = "Data/Types"

    # 有些物品，如无人机，其衍生等级相同，但均使用了错误的图标
    # 定义特殊文件映射字典: key为源文件名，value为需要复制成的type_id列表
    # SELECT t.type_id, t.name, t.metaGroupID, t.icon_filename FROM types AS t JOIN (SELECT icon_filename, categoryID, metaGroupID FROM types WHERE type_id = 12200) AS ref ON t.icon_filename = ref.icon_filename AND t.categoryID = ref.categoryID AND t.metaGroupID = ref.metaGroupID
    # 可以这样查询到，由于只有部分物品存在此问题，因此暂时使用硬编码。
    special_file_mapping = {
        '2173': [2173, 23702, 23709, 23725],  # 渗透者 I
        '2174': [2174, 23703, 23710, 23726],  # 渗透者 I
        '2193': [2193, 22572, 23510, 23523],  # 执政官 I
        '2194': [2194, 22573, 23511, 23524],  # 执政官 I
        '2203': [2203, 3549, 17565, 22574, 22713, 23659, 23711, 23727],  # 侍僧 I
        '2204': [2204, 23660, 23712, 23728],  # 侍僧 I
        '2464': [2464, 23707, 23719],  # 大黄蜂 I
        '2465': [2465, 23708, 23720],  # 大黄蜂 I
        '15508': [15508, 23705, 23717],  # 金星 I
        '15509': [15509, 23706, 23718],  # 金星 I
        '2476': [2476],  # 狂战士 I
        '2477': [2477],  # 狂战士 I
        '15510': [15510, 23721, 23729],  # 瓦尔基里 I
        '15511': [15511, 23722, 23730],  # 瓦尔基里 I
        '2486': [2486, 23723, 23731],  # 武士 I
        '2487': [2487, 23724, 23732],  # 武士 I
        '40553': [40553, 40559, 40571],  # 因赫吉 II
        '41386': [41374, 41384, 41386],  # 因赫吉 II
        '40570': [40555, 40558, 40570],  # 萨梯 II
        '41372': [41372, 41381, 41383],  # 萨梯 II
        '40569': [40554, 40557, 40569],  # 蚱蜢 II
        '41370': [41370, 41378, 41380],  # 蚱蜢 II
        '40568': [40552, 40556, 40568],  # 圣殿骑士 II
        '41368': [41368, 41375, 41377],  # 圣殿骑士 II
        '40560': [40560, 40561],  # 阿米特 II
        '41356': [41356, 41352],  # 阿米特 II
        '40562': [40562, 40563],  # 独眼巨人 II
        '41351': [41351, 41364],  # 独眼巨人 II
        '40566': [40566, 40567],  # 白蚁 II
        '41362': [41362, 41353],  # 白蚁 II
        '40565': [40564, 40565],  # 斩裂剑 II
        '41354': [41354, 41366],  # 斩裂剑 II
        '47036': [47036, 47133, 47140],  # 屹立德洛米 I
        '47211': [47211, 47222, 47230],  # 屹立德洛米 I
        '47145': [47035, 47131, 47145],  # 屹立修道士 I
        '47213': [47208, 47213, 47224],  # 屹立修道士 I
        '47138': [47132, 47138, 47146],  # 屹立圣甲虫 I
        '47209': [47209, 47216, 47226],  # 屹立圣甲虫 I
        '47147': [47037, 47139, 47147],  # 屹立掷矛手 I
        '47219': [47210, 47219, 47228],  # 屹立掷矛手 I
        '47151': [47137, 47144, 47151],  # 屹立德洛米 II
        '47223': [47221, 47223, 47231],  # 屹立德洛米 II
        '47148': [47134, 47141, 47148],  # 屹立圣殿骑士 II
        '47214': [47212, 47214, 47225],  # 屹立圣殿骑士 II
        '47142': [47135, 47142, 47149],  # 屹立蜻蜓 II
        '47215': [47215, 47217, 47227],  # 屹立蜻蜓 II
        '47150': [47136, 47143, 47150],  # 屹立掷矛手 II
        '47220': [47218, 47220, 47229],  # 屹立掷矛手 II
        '28270': [28270, 28272],  # 集成型战锤
        '28271': [28271, 28273],  # 集成型战锤
        '28274': [28274, 28276],  # 集成型地精灵
        '28275': [28275, 28277],  # 集成型地精灵
        '28286': [28286, 28288],  # 集成型蛮妖
        '28287': [28287, 28289],  # 集成型蛮妖
        '28278': [28278, 28280],  # 集成型大黄蜂
        '28279': [28279, 28281],  # 集成型大黄蜂
        '28306': [28306, 28308],  # 集成型胡蜂
        '28307': [28307, 28309],  # 集成型胡蜂
        '28298': [28298, 28300],  # 集成型金星
        '28299': [28299, 28301],  # 集成型金星
        '28282': [28282, 28284],  # 集成型渗透者
        '28283': [28283, 28285],  # 集成型渗透者
        '28262': [28262, 28264],  # 集成型侍僧
        '28263': [28263, 28265],  # 集成型侍僧
        '28302': [28302, 28304],  # 集成型武士
        '28303': [28303, 28305],  # 集成型武士
        '28290': [28290, 28292],  # 集成型执政官
        '28291': [28291, 28293],  # 集成型执政官
        '47127': [47127, 47119],  # 屹立槌骨 II
        '47242': [47242, 47238],  # 屹立槌骨 II
        '47129': [47129, 47121],  # 屹立独眼巨人 II
        '47246': [47237, 47246],  # 屹立独眼巨人 II
        '47128': [47128, 47120],  # 屹立螳螂 II
        '47244': [47244, 47239],  # 屹立螳螂 II
        '47122': [47122, 47130],  # 屹立斩裂剑 II
        '47240': [47240, 47248],  # 屹立斩裂剑 II

        '12200': [4386, 12198, 12199, 12200],  # 大型机动跃迁扰断器 I
        '12301': [12297, 12300, 12301],  # 大型机动跃迁扰断器 I
        '26888': [26888, 26890, 26892],  # 大型机动跃迁扰断器 II
        '26889': [26889, 26891, 26893],  # 大型机动跃迁扰断器 II
        '27560': [27560, 27562, 27638, 27640, 27641, 27643],  # 古斯塔斯超大型鱼雷发射台
        '27557': [27542, 27544, 27545, 27547, 27548, 27550, 27551, 27553, 27554, 27556, 27557, 27559, 27766, 27767, 27772, 27773],  # 血袭者大型脉冲激光炮台
        '16689': [16689, 16692, 16694, 16867, 17402, 17406, 17770],  # 大型火炮塔台
        '2805': [2803, 2804, 2805, 2807, 2829, 2830],  # 大型火炮塔台
        '16631': [16631, 16688, 17771, 17772],  # 小型火炮塔台
        '2816': [2810, 2814, 2816, 2819],  # 小型火炮塔台
        '17167': [17167, 17168, 17407, 17408],  # 小型集束激光炮台
        '2826': [2825, 2826, 2827, 2828],  # 小型集束激光炮台
        '27583': [27570, 27573, 27574, 27576, 27577, 27579, 27580, 27582, 27583, 27585, 27778, 27779, 27855, 27856, 27857, 27858],  # 天使停滞缠绕光束发射台
        '27565': [27563, 27565, 27567, 27569],  # 天蛇跃迁扰断波发射台
        '16690': [16690, 16691, 17403, 17404],  # 小型磁轨炮台
        '2815': [2806, 2808, 2813, 2815],  # 小型磁轨炮台

        # 可以根据需要添加更多映射
    }

    # 检查源目录是否存在
    if not os.path.exists(source_dir):
        print(f"警告：{source_dir}目录不存在，跳过图标批量复制")
        return

    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 复制普通文件
    copy_count = 0
    for item_id in special_file_mapping.keys():
        # 检查是否是特殊映射文件
        file_name = f"{item_id}_64.png"
        source_path = os.path.join(source_dir, file_name)
        if os.path.exists(source_path):
            # 为每个指定的type_id创建一个复制
            for type_id in special_file_mapping[item_id]:
                target_file_name = f"{type_id}_64.png"
                target_path = os.path.join(target_dir, target_file_name)
                shutil.copy2(source_path, target_path)
                copy_count += 1
        else:
            print(f"找不到源文件: {source_path}")

    print(f"\n已从{source_dir}复制{copy_count}个修正图标到{target_dir}")


def update_dynamic_items_data():
    """尝试从网络更新动态物品数据，如果失败则使用本地数据"""
    print("\nUpdating dynamic items data...")
    fetch_dynamic_items_data(use_cache=False)  # 强制从网络获取，如果失败则使用本地文件


def getNewAttributeID(cursor):
    """
    获取dogmaAttributes中最大的attribute_id，返回该id+1
    
    Args:
        cursor: 数据库游标
        
    Returns:
        int: 新的属性ID
    """
    cursor.execute('SELECT MAX(attribute_id) FROM dogmaAttributes')
    max_id = cursor.fetchone()[0]
    return max_id + 1


def dogmaEffect_patch():
    """修补dogmaEffects表中的特定效果数据"""
    print("\n执行dogmaEffects表数据修补...")

    # 需要修补的效果数据
    patches = [
        {
            "effect_name": "selfRof",
            "modifier_info": '[{"domain": "shipID", "func": "LocationRequiredSkillModifier", "modifiedAttributeID": 51, "modifyingAttributeID": 293, "operation": 6, "skillTypeID": -1}]'
        },
        {
            "effect_name": "droneDmgBonus",
            "modifier_info": '[{"domain": "shipID", "func": "OwnerRequiredSkillModifier", "modifiedAttributeID": 64, "modifyingAttributeID": 292, "operation": 6, "skillTypeID": -1}]'
        },
        {
            "effect_name": "microJumpDrive",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 552, "modifyingAttributeID": 973, "operation": 6}]'
        },
        {
            "effect_name": "moduleBonusMicrowarpdrive",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 552, "modifyingAttributeID": 554, "operation": 6}, {"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 4, "modifyingAttributeID": 796, "operation": 2}]'
        },
        {
            "effect_name": "moduleBonusAfterburner",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 4, "modifyingAttributeID": 796, "operation": 2}]'
        },
        {
            "effect_name": "adaptiveArmorHardener",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 267, "modifyingAttributeID": 267, "operation": 0}, {"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 268, "modifyingAttributeID": 268, "operation": 0},{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 269, "modifyingAttributeID": 269, "operation": 0},{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 270, "modifyingAttributeID": 270, "operation": 0}]'
        },
        {
            "effect_name": "hardPointModifierEffect",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 101, "modifyingAttributeID": 1369, "operation": 2}, {"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 102, "modifyingAttributeID": 1368, "operation": 2}]'
        },
        {
            "effect_name": "slotModifier",
            "modifier_info": '[{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 14, "modifyingAttributeID": 1374, "operation": 2},{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 13, "modifyingAttributeID": 1375, "operation": 2},{"domain": "shipID", "func": "ItemModifier", "modifiedAttributeID": 12, "modifyingAttributeID": 1376, "operation": 2}]'
        }
    ]

    # 遍历所有语言的数据库
    for lang in languages:
        db_filename = os.path.join(output_db_dir, f'item_db_{lang}.sqlite')

        # 检查数据库文件是否存在
        if os.path.exists(db_filename):
            db_path = db_filename
        elif os.path.exists(f"{db_filename}.zip"):
            print(f"警告：数据库 {db_filename} 已被压缩，无法修补。请在压缩前执行修补操作。")
            continue
        else:
            print(f"错误：找不到数据库 {db_filename}")
            continue

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 应用每个修补
            for patch in patches:
                effect_name = patch["effect_name"]
                modifier_info = patch["modifier_info"]

                # 更新指定效果的modifier_info字段
                cursor.execute(
                    'UPDATE dogmaEffects SET modifier_info = ? WHERE effect_name = ?',
                    (modifier_info, effect_name)
                )

                # 获取受影响的行数
                affected_rows = cursor.rowcount
                print(f"数据库 {lang}: 已更新 {affected_rows} 条 {effect_name} 效果记录")

            # 提交更改
            conn.commit()
            conn.close()

        except Exception as e:
            print(f"修补数据库 {db_filename} 时发生错误: {e}")


def main():
    rebuild_directory("./output")
    # 依次处理每个 YAML 文件
    copy_and_rename_png_files()

    # 更新动态物品数据（尝试从网络获取）
    update_dynamic_items_data()

    print("\nProcessing dbuffCollections.yaml...")  # 处理dbuff集合数据
    process_yaml_file(dbuff_collections_yaml_file_path, read_dbuff_collections_yaml, process_dbuff_collections_data)

    print("\nProcessing dynamic items data...")  # 动态物品属性数据
    process_special_data(process_dynamic_items_data, "dynamic items data")

    print("\nProcessing universe data...")
    process_special_data(process_universe_data, "universe data", lang=True)

    print("\nProcessing universe names...")
    process_universe_names()

    print("\nProcessing dogmaEffects.yaml...")  # 处理效果数据
    process_yaml_file(dogmaEffects_yaml_file_path, read_dogmaEffects_yaml, process_dogmaEffects_data)

    print("\nProcessing planetSchematics.yaml...")
    process_yaml_file(planetSchematics_yaml_file_path, read_planetSchematics_yaml, process_planetSchematics_data)

    print("\nProcessing iconIDs.yaml...")  # 图标ID与文件路径
    process_yaml_file(iconIDs_yaml_file_path, read_iconIDs_yaml, process_iconIDs_data)

    print("\nProcessing categories.yaml...")  # 物品目录
    process_yaml_file(categories_yaml_file_path, read_categories_yaml, process_categories_data)

    print("\nProcessing groups.yaml...")  # 物品组
    process_yaml_file(groups_yaml_file_path, read_groups_yaml, process_groups_data)

    print("\nProcessing stations.yaml...")  # 空间站数据
    process_yaml_file(stations_yaml_file_path, read_stations_yaml, process_stations_data)

    print("\nUpdating station names localization...")  # 更新空间站名称的本地化信息
    update_stations_localization()

    print("\nProcessing metaGroups.yaml...")  # 物品衍生组
    process_yaml_file(metaGroups_yaml_file_path, read_metaGroups_yaml, process_metaGroups_data)

    print("\nProcessing factions.yaml...")  # 派系数据
    process_yaml_file(factions_yaml_file_path, read_factions_yaml, process_factions_data)

    print("\nProcessing npcCorporations.yaml...")  # NPC公司数据
    process_yaml_file(npcCorporations_yaml_file_path, read_corporations_yaml, process_corporations_data)

    print("\nProcessing agents data...")  # 代理人数据
    process_agents_yaml_files()

    print("\nProcessing divisions data...")  # NPC公司部门数据
    process_yaml_file(divisions_yaml_file_path, read_divisions_yaml, process_divisions_data)

    print("\nProcessing dogmaAttributeCategories.yaml...")  # 物品属性目录
    process_yaml_file(dogmaAttributeCategories_yaml_file_path, read_dogmaAttributeCategories_yaml,
                      process_dogmaAttributeCategories_data)

    print("\nProcessing dogmaAttributes.yaml...")  # 物品属性名称
    process_yaml_file(dogmaAttributes_yaml_file_path, read_dogmaAttributes_yaml, process_dogmaAttributes_data)

    print("\nProcessing typeDogma.yaml...")  # 物品属性详情
    load_online = False  # 在线属性同步比较麻烦，只在必要时重新同步，执行 fetch_type_dogma.py 即可
    if os.path.exists(update_typeDogma_yaml_file_path) and load_online:
        process_yaml_file(update_typeDogma_yaml_file_path, read_typeDogma_yaml, process_typeDogma_data)
    else:
        process_yaml_file(typeDogma_yaml_file_path, read_typeDogma_yaml, process_typeDogma_data)

    # 存在一些需要修复的图片
    copy_icon_batch()

    print("\nProcessing types.yaml...")  # 物品详情
    process_yaml_file(types_yaml_file_path, read_types_yaml, process_types_data)

    print("\nProcessing marketGroups.yaml...")  # 市场分组
    process_yaml_file(marketGroups_yaml_file_path, read_marketGroups_yaml, process_marketGroups_data)

    # print("\nUpdating type localization...")  # 更新type描述
    # from update_type_description import update_type_description
    # update_type_description()

    print("\nProcessing typeMaterials.yaml...")  # 物品材料产出
    process_yaml_file(typeMaterials_yaml_file_path, read_typeMaterials_yaml, process_typeMaterials_data)

    print("\nProcessing blueprints.yaml...")  # 蓝图数据
    process_yaml_file(blueprints_yaml_file_path, read_blueprints_yaml, process_blueprints_data)

    print("\nProcessing invFlags.yaml...")  # 物品位置标识
    process_yaml_file(invFlags_yaml_file_path, read_invFlags_yaml, process_invFlags_data)

    print("\nProcessing invNames.yaml...")  # 物品名称
    process_yaml_file(invNames_yaml_file_path, read_invNames_yaml, process_invNames_data)

    print("\nUpdating agents localization...")  # 更新agents表的本地化信息
    update_agents_localization()

    print("\nUpdating groups icons...")  # 给 groups 更新图标名称
    process_special_data(update_groups_with_icon_filename, "groups icons")

    print("\nProcessing skill requirements...")  # 处理技能需求数据
    process_special_data(process_skill_requirements, "skill requirements", lang=True)

    # 删除iconIDs表，因为图标文件名已经复制到各个相关表中
    drop_icon_ids_table()

    # 清理invNames表中不在指定范围的记录
    clean_invnames_table()

    # 执行dogmaEffects表数据修补
    dogmaEffect_patch()

    print("\n")
    create_uncompressed_icons_zip(ICONS_DEST_DIR, ZIP_ICONS_DEST)

    # 压缩所有数据库
    compress_all_databases()

    print("\n所有数据库已更新。")


if __name__ == "__main__":
    main()
