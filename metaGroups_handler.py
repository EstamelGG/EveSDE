import sqlite3
import os
from ruamel.yaml import YAML
import time
import yaml
try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader
from cache_manager import register_cache_cleaner

# 用于缓存数据的全局变量
_cached_data = None

def clear_cache():
    """清理模块的缓存数据"""
    global _cached_data
    _cached_data = None

# 注册缓存清理函数
register_cache_cleaner('metaGroups', clear_cache)

# 提取科技等级组对应的名字

yaml = YAML(typ='safe')

# 定义语言列表
languages = ['de', 'en', 'es', 'fr', 'ja', 'ko', 'ru', 'zh']

# 文件路径
meta_groups_yaml_file_path = 'Data/sde/fsd/metaGroups.yaml'
output_dir = 'output/db'
os.makedirs(output_dir, exist_ok=True)


def read_yaml(file_path):
    """读取 metaGroups.yaml 文件并返回数据"""
    start_time = time.time()
    
    global _cached_data
    if _cached_data is None:
        with open(file_path, 'r', encoding='utf-8') as file:
            _cached_data = yaml.load(file, Loader=SafeLoader)
    
    end_time = time.time()
    print(f"读取 {file_path} 耗时: {end_time - start_time:.2f} 秒")
    return _cached_data


def create_meta_groups_table(cursor):
    """创建 metaGroups 表"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metaGroups (
            metagroup_id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')


def process_data(meta_groups_data, cursor, lang):
    """处理 metaGroups 数据并插入数据库（针对单一语言）"""
    create_meta_groups_table(cursor)

    for metagroup_id, meta_group in meta_groups_data.items():
        # 提取当前语言的名称，如果没有对应语言，优先使用英文
        name = meta_group.get('nameID', {}).get(lang, meta_group.get('nameID', {}).get('en', ""))

        # 插入数据
        cursor.execute('''
            INSERT OR IGNORE INTO metaGroups (metagroup_id, name)
            VALUES (?, ?)
        ''', (metagroup_id, name))


def process_yaml_file(yaml_file_path, languages, output_dir):
    """处理 metaGroups.yaml 文件并写入数据库"""
    # 读取 YAML 数据
    meta_groups_data = read_yaml(yaml_file_path)

    for lang in languages:
        db_filename = os.path.join(output_dir, f'metaGroups_db_{lang}.sqlite')

        # 连接数据库
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()

        # 处理数据
        process_data(meta_groups_data, cursor, lang)

        # 提交事务并关闭连接
        conn.commit()
        conn.close()

        print(f"Database {db_filename} has been updated for language: {lang}.")


def main():
    """主函数"""
    print("Processing metaGroups.yaml...")
    process_yaml_file(meta_groups_yaml_file_path, languages, output_dir)
    print("\nAll metaGroups databases have been updated.")


if __name__ == "__main__":
    main()